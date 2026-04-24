from __future__ import annotations

import os
import time
import json
import asyncio
from collections import deque
from typing import List, Optional, Dict, Set, Any

import httpx
import psutil
from fastapi import FastAPI, HTTPException, Query, Depends, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    RegisterRequest,
    MetricsPayload,
    ControlRequest,
    CommandItem,
    ClientInfo,
    LogEntry,
    AIAnalyzeInput,
    PatternsUpdate,
    BulkControlRequest,
    ClientUpdate,
    BulkTagsRequest,
    CommandResult,
)
from .state import STATE
from .ai import analyze_behavior, analyze_behavior_async, OLLAMA_URL, MODEL_NAME

# VNC server info storage (client_id -> VNC info)
vnc_servers: Dict[str, Dict[str, Any]] = {}  # client_id -> {port, password, status}

# HTTP client with connection pooling for async operations
_http_client: Optional[httpx.AsyncClient] = None

def get_http_client() -> httpx.AsyncClient:
    """Get or create shared HTTP client with connection pooling"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(5.0, connect=2.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            http2=True,
        )
    return _http_client

app = FastAPI(title="Server–Client Manager", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up HTTP client on shutdown"""
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Better error messages for validation errors"""
    body = None
    if exc.body:
        if isinstance(exc.body, bytes):
            try:
                body = exc.body.decode()
            except (UnicodeDecodeError, AttributeError):
                body = str(exc.body)
        elif isinstance(exc.body, dict):
            body = exc.body
        else:
            body = str(exc.body)
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": body,
        },
    )

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
LARAVEL_WEBHOOK_URL = os.getenv("LARAVEL_WEBHOOK_URL")
LARAVEL_WEBHOOK_KEY = os.getenv("LARAVEL_WEBHOOK_KEY")


def require_admin(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
    if ADMIN_API_KEY and x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


async def post_webhook_async(event_type: str, data: dict) -> None:
    """Async webhook posting - non-blocking"""
    if not LARAVEL_WEBHOOK_URL:
        return
    body = {"type": event_type, "data": data, "ts": time.time()}
    headers = {"Content-Type": "application/json"}
    if LARAVEL_WEBHOOK_KEY:
        headers["X-Webhook-Key"] = LARAVEL_WEBHOOK_KEY
    try:
        client = get_http_client()
        await client.post(LARAVEL_WEBHOOK_URL, json=body, headers=headers)
    except Exception:
        # ignore webhook errors - fire and forget
        pass

def post_webhook(event_type: str, data: dict) -> None:
    """Synchronous wrapper - schedules async call without blocking"""
    if not LARAVEL_WEBHOOK_URL:
        return
    # Schedule async call without waiting - use get_event_loop for compatibility
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create task
            loop.create_task(post_webhook_async(event_type, data))
        else:
            # If no loop running, run in new thread
            import threading
            def run_webhook():
                asyncio.run(post_webhook_async(event_type, data))
            threading.Thread(target=run_webhook, daemon=True).start()
    except RuntimeError:
        # No event loop, run in background thread
        import threading
        def run_webhook():
            asyncio.run(post_webhook_async(event_type, data))
        threading.Thread(target=run_webhook, daemon=True).start()


@app.get("/")
def root() -> dict:
    return {
        "name": "Server–Client Manager API",
        "version": "0.2.0",
        "endpoints": {
            "health": "/health",
            "register": "/register",
            "metrics": "/metrics",
            "control": "/control",
            "clients": "/clients",
            "vnc": "/vnc/{client_id}",
            "vnc_ws": "/vnc/ws/{client_id}",
        }
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True, "ts": time.time()}


@app.post("/register")
def register(req: RegisterRequest) -> dict:
    now = time.time()
    info = ClientInfo(client_id=req.client_id, ip=req.ip, meta=req.meta, last_seen_ts=now)
    STATE.upsert_client(info)
    return {"ok": True}


@app.post("/metrics")
async def metrics(payload: MetricsPayload) -> dict:
    now = time.time()
    # Upsert client và heartbeat (tránh build dict tạm cho toàn bộ clients)
    client = STATE.get_client(payload.client_id) or ClientInfo(client_id=payload.client_id)
    # Enforce block: refuse metrics from blocked clients
    if client.blocked:
        raise HTTPException(status_code=403, detail="Client is blocked")
    client.ip = payload.ip or client.ip
    client.last_seen_ts = now
    STATE.upsert_client(client)

    snapshot = payload.model_dump()
    snapshot["ts"] = now
    STATE.add_history_point(payload.client_id, snapshot)

    # Prepare input for AI (lấy tối đa 30 điểm mới nhất, logic cắt nằm ở state)
    history = STATE.get_history(payload.client_id)
    recent_history = history[-30:] if len(history) > 30 else history
    
    # Skip AI analysis if connections_per_min is 0 (likely a spam test or manual override)
    result = None
    ai_input = None
    if payload.connections_per_min and payload.connections_per_min > 0:
        ai_input = AIAnalyzeInput(
            client_id=payload.client_id,
            cpu=payload.cpu,
            network_out=payload.network_out,
            connections_per_min=payload.connections_per_min,
            history=recent_history,
        )

        # Gọi AI là bước tốn thời gian; chạy async để không block response
        try:
            result = await analyze_behavior_async(ai_input)
        except Exception:
            result = None

    if result and ai_input:
        if result.status == "block":
            # Mark blocked and enqueue a block command
            client.blocked = True
            STATE.upsert_client(client)
            STATE.enqueue_command(
                CommandItem(
                    client_id=payload.client_id,
                    action="block",
                    message=result.reason,
                    source="AI",
                )
            )
            STATE.write_log(
                LogEntry(
                    ts=now,
                    source="AI",
                    action="block",
                    client_id=payload.client_id,
                    reason=result.reason,
                    raw=ai_input.model_dump(),
                )
            )
            post_webhook(
                "ai_block",
                {
                    "client_id": payload.client_id,
                    "reason": result.reason,
                },
            )
        elif result.status == "warn":
            STATE.write_log(
                LogEntry(
                    ts=now,
                    source="AI",
                    action="warn",
                    client_id=payload.client_id,
                    reason=result.reason,
                    raw=ai_input.model_dump(),
                )
            )
            post_webhook(
                "ai_warn",
                {
                    "client_id": payload.client_id,
                    "reason": result.reason,
                },
            )

    return {"ok": True, "ai": (result.model_dump() if result else None)}


@app.post("/control")
def control(req: ControlRequest, _: None = Depends(require_admin)) -> dict:
    # Basic check - get or create client (optimized: get single client instead of all)
    client = STATE.get_client(req.client_id)
    if not client:
        # Client doesn't exist yet - create a basic client info
        # This allows sending commands to clients that haven't registered yet
        client = ClientInfo(
            client_id=req.client_id,
            ip=None,
            meta={},
            last_seen_ts=time.time(),
            blocked=False,
        )
        STATE.upsert_client(client)

    now = time.time()
    # Update block state for certain actions
    if req.action == "block":
        client.blocked = True
        STATE.upsert_client(client)
    elif req.action == "unblock":
        client.blocked = False
        STATE.upsert_client(client)

    # Generate command_id for tracking
    import uuid
    command_id = str(uuid.uuid4())
    
    # Enqueue command for the agent
    STATE.enqueue_command(
        CommandItem(
            client_id=req.client_id,
            action=req.action,
            message=req.message,
            source=req.source,
            source_user=req.source_user,
            command=req.command,
            file_path=req.file_path,
            file_data=req.file_data,
            target_path=req.target_path,
            command_id=command_id,
            process_id=req.process_id,
            service_name=req.service_name,
            service_action=req.service_action,
            directory_path=req.directory_path,
        )
    )

    # Log the action
    STATE.write_log(
        LogEntry(
            ts=now,
            source=req.source,
            action=req.action,
            client_id=req.client_id,
            reason=req.message,
            source_user=req.source_user,
            raw=req.model_dump(),
        )
    )

    post_webhook(
        "control",
        {
            "client_id": req.client_id,
            "action": req.action,
            "message": req.message,
            "source": req.source,
            "source_user": req.source_user,
        },
    )

    return {"ok": True, "command_id": command_id}


@app.post("/command/result")
def command_result(result: CommandResult) -> dict:
    """Receive command execution result from agent"""
    now = time.time()
    
    # Log the result
    STATE.write_log(
        LogEntry(
            ts=now,
            source="AI",  # Agent results are from AI source
            action=f"{result.action}_result",
            client_id=result.client_id,
            reason=f"Success: {result.success}, Exit: {result.exit_code}",
            raw=result.model_dump(),
        )
    )
    
    # Store result in state (for history tracking)
    STATE.store_command_result(result)
    
    # If this is a VNC server start result, store VNC info
    if result.metadata and isinstance(result.metadata, dict):
        action = result.metadata.get("action") or ""
        if action == "start_vnc_server" and result.success:
            # Store VNC server info
            client_ip = None
            client = STATE.get_client(result.client_id)
            if client:
                client_ip = client.ip
            
            # Prefer client_ip from metadata (sent by client), then from client record, then fallback
            final_client_ip = result.metadata.get("client_ip") or client_ip or "127.0.0.1"
            
            print(f"[VNC] Storing VNC info for {result.client_id}: port={result.metadata.get('port')}, ip={final_client_ip}")
            
            vnc_servers[result.client_id] = {
                "port": result.metadata.get("port", 5900),
                "display": result.metadata.get("display", 1),
                "password_set": result.metadata.get("password_set", False),
                "client_ip": final_client_ip,
            }
    
    post_webhook(
        "command_result",
        {
            "command_id": result.command_id,
            "client_id": result.client_id,
            "action": result.action,
            "success": result.success,
        },
    )
    
    return {"ok": True}


@app.get("/command/result/{command_id}")
def get_command_result(command_id: str, _: None = Depends(require_admin)) -> dict:
    """Get command execution result by command_id"""
    result = STATE.get_command_result(command_id)
    if result:
        return {"ok": True, "result": result.model_dump()}
    return {"ok": False, "error": "Command result not found"}


@app.get("/commands/next")
def commands_next(client_id: str = Query(...)) -> dict:
    # Enforce block: do not serve commands to blocked clients
    client = STATE.get_client(client_id)
    if client and client.blocked:
        raise HTTPException(status_code=403, detail="Client is blocked")
    cmd = STATE.pop_next_command(client_id)
    if not cmd:
        return {"command": None}
    return {"command": cmd.model_dump()}


@app.get("/clients")
def list_clients(
    q: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    blocked: Optional[bool] = Query(None),
    export: Optional[bool] = Query(False),
    _: None = Depends(require_admin),
) -> List[dict]:
    items = STATE.get_clients()
    if q:
        q_lower = q.lower()
        items = [
            c
            for c in items
            if (
                q_lower in c.client_id.lower()
                or (c.ip or "").lower().find(q_lower) != -1
                or any(q_lower in (t or "").lower() for t in (c.tags or []))
                or (c.note or "").lower().find(q_lower) != -1
            )
        ]
    if tag:
        items = [c for c in items if tag in (c.tags or [])]
    if blocked is not None:
        items = [c for c in items if c.blocked == blocked]
    rows = [c.model_dump() for c in items]
    if export:
        # Trả về CSV text/plain đơn giản
        import csv
        import io

        fieldnames = [
            "client_id",
            "ip",
            "last_seen_ts",
            "blocked",
            "tags",
            "note",
        ]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "client_id": r.get("client_id"),
                    "ip": r.get("ip"),
                    "last_seen_ts": r.get("last_seen_ts"),
                    "blocked": r.get("blocked"),
                    "tags": ",".join(r.get("tags", [])),
                    "note": r.get("note", ""),
                }
            )
        from fastapi import Response

        return Response(content=buf.getvalue(), media_type="text/csv")
    return rows


@app.get("/logs")
def get_logs(limit: int = Query(100, ge=1, le=1000), since_ts: Optional[float] = Query(None), _: None = Depends(require_admin)) -> List[dict]:
    # Return last N logs by tailing the file
    from .state import LOG_FILE
    items: deque[str] = deque(maxlen=limit)
    try:
        with LOG_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                items.append(line)
    except FileNotFoundError:
        return []

    out: List[dict] = []
    for line in items:
        line = line.strip()
        if not line:
            continue
        try:
            import json

            obj = json.loads(line)
            if since_ts is not None:
                try:
                    if float(obj.get("ts", 0.0)) < float(since_ts):
                        continue
                except Exception:
                    pass
            out.append(obj)
        except Exception:
            continue
    return out



# Admin convenience endpoints


@app.get("/stats")
def stats(_: None = Depends(require_admin)) -> dict:
    return STATE.get_stats()


@app.get("/system")
def system(_: None = Depends(require_admin)) -> dict:
    """Return basic system metrics for the server itself."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
    except Exception:
        cpu_percent = None
    try:
        vm = psutil.virtual_memory()
        mem = {
            "total": vm.total,
            "available": vm.available,
            "used": vm.used,
            "percent": vm.percent,
        }
    except Exception:
        mem = {}
    try:
        swapm = psutil.swap_memory()
        swap = {
            "total": swapm.total,
            "used": swapm.used,
            "percent": swapm.percent,
        }
    except Exception:
        swap = {}
    try:
        du = psutil.disk_usage("/")
        disk = {
            "total": du.total,
            "used": du.used,
            "percent": du.percent,
        }
    except Exception:
        disk = {}
    try:
        boot_time = getattr(psutil, "boot_time", lambda: None)()
        uptime_sec = time.time() - boot_time if boot_time else None
    except Exception:
        uptime_sec = None

    return {
        "cpu_percent": cpu_percent,
        "memory": mem,
        "swap": swap,
        "disk": disk,
        "uptime_sec": uptime_sec,
        "ts": time.time(),
    }


@app.get("/clients/{client_id}")
def get_client(client_id: str, _: None = Depends(require_admin)) -> dict:
    client = STATE.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client.model_dump()


@app.patch("/clients/{client_id}")
def update_client(client_id: str, payload: ClientUpdate, _: None = Depends(require_admin)) -> dict:
    client = STATE.update_client(
        client_id,
        tags=payload.tags,
        note=payload.note,
        blocked=payload.blocked,
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"ok": True, "client": client.model_dump()}


@app.patch("/clients/{client_id}/rename")
def rename_client(client_id: str, new_client_id: str = Query(..., alias="new_client_id"), _: None = Depends(require_admin)) -> dict:
    """Rename client (update client_id) while preserving all data."""
    if not new_client_id or len(new_client_id) < 3:
        raise HTTPException(status_code=400, detail="new_client_id must be at least 3 characters")
    
    success = STATE.rename_client(client_id, new_client_id)
    if not success:
        raise HTTPException(status_code=404, detail="Client not found or new client_id already exists")
    
    post_webhook("client_renamed", {"old_client_id": client_id, "new_client_id": new_client_id})
    return {"ok": True, "old_client_id": client_id, "new_client_id": new_client_id}


@app.delete("/clients/{client_id}")
def delete_client(client_id: str, _: None = Depends(require_admin)) -> dict:
    existed = STATE.delete_client(client_id)
    if not existed:
        raise HTTPException(status_code=404, detail="Client not found")
    post_webhook("client_deleted", {"client_id": client_id})
    return {"ok": True}


@app.get("/clients/{client_id}/queue")
def get_client_queue(client_id: str, _: None = Depends(require_admin)) -> List[dict]:
    q = STATE.get_queue(client_id)
    return [c.model_dump() for c in q]


@app.delete("/clients/{client_id}/queue")
def clear_client_queue(client_id: str, _: None = Depends(require_admin)) -> dict:
    n = STATE.clear_queue(client_id)
    post_webhook("queue_cleared", {"client_id": client_id, "cleared": n})
    return {"ok": True, "cleared": n}


@app.get("/clients/{client_id}/history")
def get_client_history(client_id: str, limit: int = Query(100, ge=1, le=1000), _: None = Depends(require_admin)) -> List[dict]:
    history = STATE.get_history(client_id)
    if not history:
        # If client missing, still return empty list to keep UI simple
        return []
    return history[-limit:]


@app.delete("/clients/{client_id}/history")
def clear_client_history(client_id: str, _: None = Depends(require_admin)) -> dict:
    n = STATE.clear_history(client_id)
    post_webhook("history_cleared", {"client_id": client_id, "cleared": n})
    return {"ok": True, "cleared": n}


@app.get("/patterns")
def get_patterns(_: None = Depends(require_admin)) -> dict:
    return {"patterns": STATE.get_patterns()}


@app.put("/patterns")
def put_patterns(payload: PatternsUpdate, _: None = Depends(require_admin)) -> dict:
    STATE.set_patterns(payload.patterns)
    return {"ok": True}


@app.post("/control/bulk")
def control_bulk(req: BulkControlRequest, _: None = Depends(require_admin)) -> dict:
    # Optimized: get clients once and reuse
    all_clients = STATE.get_clients()
    existing = {c.client_id: c for c in all_clients}
    target_ids: List[str]
    if req.client_ids:
        target_ids = [cid for cid in req.client_ids if cid in existing]
    else:
        # filter by q/tag/blocked (reuse existing dict values)
        items = list(existing.values())
        if req.q:
            ql = req.q.lower()
            items = [
                c
                for c in items
                if (
                    ql in c.client_id.lower()
                    or (c.ip or "").lower().find(ql) != -1
                    or any(ql in (t or "").lower() for t in (c.tags or []))
                    or (c.note or "").lower().find(ql) != -1
                )
            ]
        if req.tag:
            items = [c for c in items if req.tag in (c.tags or [])]
        if req.blocked is not None:
            items = [c for c in items if c.blocked == req.blocked]
        target_ids = [c.client_id for c in items]

    now = time.time()
    count = 0
    for cid in target_ids:
        client = existing[cid]
        if req.action == "block":
            client.blocked = True
            STATE.upsert_client(client)
        elif req.action == "unblock":
            client.blocked = False
            STATE.upsert_client(client)

        STATE.enqueue_command(
            CommandItem(
                client_id=cid,
                action=req.action,
                message=req.message,
                source=req.source,
                source_user=req.source_user,
                command=req.command,
                file_path=req.file_path,
                file_data=req.file_data,
                target_path=req.target_path,
                process_id=req.process_id,
                service_name=req.service_name,
                service_action=req.service_action,
                directory_path=req.directory_path,
            )
        )
        STATE.write_log(
            LogEntry(
                ts=now,
                source=req.source,
                action=req.action,
                client_id=cid,
                reason=req.message,
                source_user=req.source_user,
                raw={"bulk": True},
            )
        )
        count += 1

    post_webhook(
        "control_bulk",
        {
            "client_ids": target_ids,
            "action": req.action,
            "message": req.message,
            "source": req.source,
            "source_user": req.source_user,
            "count": count,
        },
    )

    return {"ok": True, "count": count}


@app.post("/clients/tags:bulk")
def bulk_tags(req: BulkTagsRequest, _: None = Depends(require_admin)) -> dict:
    # Optimized: get clients once and reuse
    all_clients = STATE.get_clients()
    existing = {c.client_id: c for c in all_clients}
    # Resolve targets
    if req.client_ids:
        targets = [existing[cid] for cid in req.client_ids if cid in existing]
    else:
        items = list(existing.values())
        if req.q:
            ql = req.q.lower()
            items = [
                c
                for c in items
                if (
                    ql in c.client_id.lower()
                    or (c.ip or "").lower().find(ql) != -1
                    or any(ql in (t or "").lower() for t in (c.tags or []))
                    or (c.note or "").lower().find(ql) != -1
                )
            ]
        if req.tag:
            items = [c for c in items if req.tag in (c.tags or [])]
        if req.blocked is not None:
            items = [c for c in items if c.blocked == req.blocked]
        targets = items

    added = list(dict.fromkeys(req.add or []))
    removed = set(req.remove or [])
    count = 0
    for c in targets:
        tags = [t for t in (c.tags or []) if t not in removed]
        for t in added:
            if t not in tags:
                tags.append(t)
        STATE.update_client(c.client_id, tags=tags)
        count += 1

    post_webhook(
        "tags_bulk",
        {
            "count": count,
            "add": added,
            "remove": list(removed),
        },
    )
    return {"ok": True, "count": count}


@app.get("/ai/health")
async def ai_health(_: None = Depends(require_admin)) -> dict:
    try:
        tags_url = OLLAMA_URL.replace("/generate", "/tags")
        client = get_http_client()
        res = await client.get(tags_url)
        return {"ok": res.is_success}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/ai/test")
def ai_test(body: AIAnalyzeInput, _: None = Depends(require_admin)) -> dict:
    try:
        result = analyze_behavior(body)
        return {"ok": True, "result": result.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# VNC server endpoints
@app.get("/vnc/{client_id}", dependencies=[Depends(require_admin)])
async def get_vnc_info(client_id: str) -> dict:
    """Get VNC server info for a client"""
    if client_id in vnc_servers:
        vnc_info = vnc_servers[client_id].copy()
        # Test TCP connection to VNC server
        import socket
        vnc_port = vnc_info.get("port", 5900)
        client_host = vnc_info.get("client_ip", "127.0.0.1")
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(2)
            result = test_socket.connect_ex((client_host, vnc_port))
            test_socket.close()
            vnc_info["tcp_connectable"] = (result == 0)
            if result != 0:
                vnc_info["tcp_error"] = f"Connection test failed (code: {result})"
        except Exception as e:
            vnc_info["tcp_connectable"] = False
            vnc_info["tcp_error"] = str(e)
        return {"ok": True, "vnc": vnc_info}
    return {"ok": False, "error": "VNC server not started for this client"}


@app.websocket("/vnc/ws/{client_id}")
async def vnc_websocket_proxy(
    websocket: WebSocket,
    client_id: str,
    api_key: Optional[str] = Query(default=None),
):
    """
    WebSocket proxy for VNC connection (for noVNC).
    Proxies WebSocket messages to VNC server TCP connection on client machine.
    """
    print(f"[VNC Proxy] WebSocket connection attempt for client_id: {client_id}")
    
    # Verify API key (only if ADMIN_API_KEY is configured)
    if ADMIN_API_KEY:
        if api_key != ADMIN_API_KEY:
            print(f"[VNC Proxy] Invalid API key provided (got={api_key!r})")
            await websocket.close(code=1008, reason="Invalid API key")
            return
    
    if client_id not in vnc_servers:
        print(f"[VNC Proxy] VNC server not found for client_id: {client_id}")
        print(f"[VNC Proxy] Available VNC servers: {list(vnc_servers.keys())}")
        await websocket.close(code=1008, reason="VNC server not started")
        return
    
    vnc_info = vnc_servers[client_id]
    vnc_port = vnc_info.get("port", 5900)
    client_host = vnc_info.get("client_ip", "127.0.0.1")
    
    print(f"[VNC Proxy] VNC info for {client_id}: host={client_host}, port={vnc_port}")
    
    try:
        await websocket.accept()
        print(f"[VNC Proxy] WebSocket accepted, connecting to VNC server at {client_host}:{vnc_port}")
    except Exception as e:
        print(f"[VNC Proxy] Failed to accept WebSocket: {e}")
        import traceback
        traceback.print_exc()
        return
    
    try:
        import asyncio
        
        # Create TCP connection to VNC server on client machine
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(client_host, vnc_port),
                timeout=10.0  # Increased timeout
            )
            print(f"[VNC Proxy] Successfully connected to VNC server at {client_host}:{vnc_port}")
        except asyncio.TimeoutError:
            error_msg = f"Timeout connecting to VNC server at {client_host}:{vnc_port}"
            print(f"[VNC Proxy] {error_msg}")
            await websocket.close(code=1008, reason=error_msg)
            return
        except ConnectionRefusedError as e:
            error_msg = f"Connection refused to {client_host}:{vnc_port}. VNC server may not be running or not listening on this interface."
            print(f"[VNC Proxy] {error_msg}: {e}")
            await websocket.close(code=1008, reason=error_msg)
            return
        except OSError as e:
            error_msg = f"Network error connecting to {client_host}:{vnc_port}: {str(e)}"
            print(f"[VNC Proxy] {error_msg}")
            await websocket.close(code=1008, reason=error_msg)
            return
        except Exception as e:
            error_msg = f"Unexpected error connecting to {client_host}:{vnc_port}: {str(e)}"
            print(f"[VNC Proxy] {error_msg}")
            import traceback
            traceback.print_exc()
            await websocket.close(code=1008, reason=error_msg)
            return
        
        async def forward_ws_to_vnc():
            """Forward WebSocket messages to VNC TCP"""
            try:
                while True:
                    try:
                        data = await websocket.receive_bytes()
                    except WebSocketDisconnect:
                        print("[VNC Proxy] WebSocket disconnected (WS->VNC)")
                        break
                    if not data:
                        # No payload, skip
                        continue
                    print(f"[VNC Proxy] WS->VNC {len(data)} bytes")
                    writer.write(data)
                    await writer.drain()
            except Exception as e:
                print(f"[VNC Proxy] WS to VNC error: {e}")
        
        async def forward_vnc_to_ws():
            """Forward VNC TCP messages to WebSocket"""
            try:
                while True:
                    data = await reader.read(8192)
                    if not data:
                        print("[VNC Proxy] VNC server closed TCP connection")
                        break
                    print(f"[VNC Proxy] VNC->WS {len(data)} bytes")
                    try:
                        await websocket.send_bytes(data)
                    except WebSocketDisconnect:
                        print("[VNC Proxy] WebSocket disconnected while sending (VNC->WS)")
                        break
            except Exception as e:
                print(f"[VNC Proxy] VNC to WS error: {e}")
        
        # Run both directions concurrently
        await asyncio.gather(
            forward_ws_to_vnc(),
            forward_vnc_to_ws(),
            return_exceptions=True
        )
        
    except Exception as e:
        print(f"[VNC Proxy] Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close(code=1011, reason=f"Internal error: {str(e)}")
        except:
            pass
    finally:
        # Clean up TCP connection if it was created
        try:
            if 'writer' in locals():
                writer.close()
                await writer.wait_closed()
        except:
            pass
        # Close WebSocket if still open
        try:
            if websocket.client_state.name != "DISCONNECTED":
                await websocket.close()
        except:
            pass

