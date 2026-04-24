"""
api.py

High-level API and background agent runner for the Agent Client UI.

This module provides:
- ApiClient: simple wrapper around HTTP endpoints (/health, /register, /login, /metrics, /command)
- AgentRunner: background worker that periodically sends metrics and polls commands

Designed for Python 3.13. Dependencies: requests, psutil.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import uuid
import socket

import psutil
import requests
from urllib.parse import urlparse, urlunparse

# Import command executor
try:
    from command_executor import CommandExecutor
except ImportError:
    # Fallback if module not found
    CommandExecutor = None


class ApiClient:
    """HTTP client for communicating with the Agent Server.

    Responsibilities:
    - Manage base URL and auth token
    - Persist identity (token, username) to .agent_identity.json
    - Provide helpers to call server endpoints
    """

    def __init__(self, base_url: Optional[str] = None, identity_filename: str = ".agent_identity.json") -> None:
        self._base_url: Optional[str] = None
        self._token: Optional[str] = None
        self._username: Optional[str] = None
        # Use Session with connection pooling for better performance
        self._session = requests.Session()
        # Configure adapter for connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=2,
            pool_block=False
        )
        self._session.mount('http://', adapter)
        self._session.mount('https://', adapter)
        self._timeout_seconds: float = 5.0  # Reduced from 8.0 for faster failures
        self._client_id: Optional[str] = None
        self._registered_fastapi: bool = False
        self._metrics_url_cache: Optional[str] = None
        self._command_url_cache: Optional[str] = None
        self._last_net_sent_bytes: Optional[int] = None
        self._last_net_ts: Optional[float] = None

        # Identity file path stored next to this file by default
        self._identity_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), identity_filename)

        if base_url:
            self.set_base_url(base_url)

        # Try loading existing identity
        self._load_identity_if_exists()

        # Ensure client_id exists
        if not self._client_id:
            self._client_id = str(uuid.uuid4())
            self._save_identity()

    # -----------------------------
    # Public properties
    # -----------------------------
    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    @property
    def token(self) -> Optional[str]:
        return self._token

    @property
    def username(self) -> Optional[str]:
        return self._username

    # -----------------------------
    # Identity management
    # -----------------------------
    def _load_identity_if_exists(self) -> None:
        if not os.path.exists(self._identity_path):
            return
        try:
            with open(self._identity_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._token = data.get("token") or None
            self._username = data.get("username") or None
            self._client_id = data.get("client_id") or None
        except Exception:
            # Ignore corrupted identity file
            pass

    def _save_identity(self) -> None:
        try:
            payload = {"token": self._token, "username": self._username, "client_id": self._client_id}
            with open(self._identity_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            # Do not raise into UI layer
            pass
    
    def set_client_id(self, new_client_id: str) -> None:
        """Update client ID and save to identity file."""
        if not new_client_id or not isinstance(new_client_id, str):
            raise ValueError("Client ID must be a non-empty string")
        new_client_id = new_client_id.strip()
        if len(new_client_id) < 3:
            raise ValueError("Client ID must be at least 3 characters long")
        self._client_id = new_client_id
        self._save_identity()

    def set_base_url(self, base_url: str) -> None:
        normalized = (base_url or "").strip()
        if normalized.endswith("/"):
            normalized = normalized[:-1]
        self._base_url = normalized or None

    # -----------------------------
    # HTTP helpers
    # -----------------------------
    def _build_url(self, path: str) -> str:
        if not self._base_url:
            raise ValueError("Server URL is not set. Please connect first.")
        if not path.startswith("/"):
            path = "/" + path
        return f"{self._base_url}{path}"

    def _candidate_base_urls(self, prefer_python: bool = False) -> list[str]:
        """Return likely base URLs to try when some endpoints 404 (e.g., Laravel 8000 vs FastAPI 5000).
        
        Args:
            prefer_python: If True, prioritize Python server (5000) over Laravel (8000) for metrics/commands.
        """
        bases: list[str] = []
        if not self._base_url:
            return bases
        try:
            p = urlparse(self._base_url)
            if p.scheme and p.hostname:
                # Detect if base URL points to Laravel (port 8000) or Python (port 5000)
                current_port = p.port or (8000 if ":8000" in self._base_url else 5000 if ":5000" in self._base_url else None)
                
                # Build Python server URL (port 5000)
                py_netloc = f"{p.hostname}:5000"
                if p.username or p.password:
                    userinfo = ""
                    if p.username:
                        userinfo += p.username
                    if p.password:
                        userinfo += f":{p.password}"
                    py_netloc = f"{userinfo}@{py_netloc}"
                py_url = urlunparse((p.scheme, py_netloc, "", "", "", ""))
                
                # Build Laravel URL (port 8000) if needed
                laravel_url = self._base_url
                if current_port != 8000 and ":8000" not in self._base_url:
                    laravel_netloc = f"{p.hostname}:8000"
                    if p.username or p.password:
                        userinfo = ""
                        if p.username:
                            userinfo += p.username
                        if p.password:
                            userinfo += f":{p.password}"
                        laravel_netloc = f"{userinfo}@{laravel_netloc}"
                    laravel_url = urlunparse((p.scheme, laravel_netloc, "", "", "", ""))
                
                # Order: prefer Python for metrics/commands, Laravel for auth/profile
                if prefer_python:
                    if py_url not in bases:
                        bases.append(py_url)
                    if self._base_url not in bases:
                        bases.append(self._base_url)
                    if laravel_url != self._base_url and laravel_url not in bases:
                        bases.append(laravel_url)
                else:
                    # Default: try original first, then alternatives
                    if self._base_url not in bases:
                        bases.append(self._base_url)
                    if py_url not in bases:
                        bases.append(py_url)
                    if laravel_url != self._base_url and laravel_url not in bases:
                        bases.append(laravel_url)
        except Exception:
            # Fallback: just use original base URL
            bases.append(self._base_url)
        return bases

    def _auth_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _get_local_ip(self) -> Optional[str]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.2)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return None

    # -----------------------------
    # Endpoints
    # -----------------------------
    def get_profile(self) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Fetch client profile (status/online/tags/note) from Laravel DB via API.

        Requires login (Bearer token) and base_url pointing to Laravel.
        """
        try:
            if not self._client_id:
                return False, None, "No client_id"
            url = self._build_url(f"/api/client/{self._client_id}/profile")
            resp = self._session.get(url, headers=self._auth_headers(), timeout=self._timeout_seconds)
            if 200 <= resp.status_code < 300:
                try:
                    data = resp.json()
                except Exception:
                    data = None
                if isinstance(data, dict):
                    return True, data, "OK"
                return True, None, "Empty"
            return False, None, f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, None, str(exc)

    def set_online(self, online: bool) -> Tuple[bool, str]:
        """Update online flag in Laravel DB for this client (auth:sanctum)."""
        try:
            if not self._client_id:
                return False, "No client_id"
            if not self._token:
                return False, "Not authenticated"
            url = self._build_url(f"/api/client/{self._client_id}/online")
            payload = {"online": bool(online), "ip": self._get_local_ip() or ""}
            resp = self._session.patch(url, json=payload, headers=self._auth_headers(), timeout=self._timeout_seconds)
            if 200 <= resp.status_code < 300:
                return True, "OK"
            return False, f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, str(exc)
    
    def update_client_id(self, new_client_id: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Update client_id (rename client) in Laravel DB.
        
        Args:
            new_client_id: New client ID to set
            
        Returns:
            (success, updated_profile_dict, message)
        """
        try:
            if not self._client_id:
                return False, None, "No current client_id"
            if not self._token:
                return False, None, "Not authenticated"
            
            url = self._build_url(f"/api/client/{self._client_id}/client-id")
            payload = {"new_client_id": new_client_id}
            
            resp = self._session.patch(url, json=payload, headers=self._auth_headers(), timeout=self._timeout_seconds)
            if 200 <= resp.status_code < 300:
                try:
                    data = resp.json()
                    client_data = data.get("client")
                    # Update local client_id if update succeeded
                    if data.get("ok") and data.get("new_client_id"):
                        self._client_id = data.get("new_client_id")
                        self._save_identity()
                    return True, client_data, "Client ID updated"
                except Exception:
                    return True, None, "Client ID updated"
            elif resp.status_code == 409:
                # Conflict - client ID already exists
                try:
                    error_data = resp.json()
                    error_msg = error_data.get("error") or error_data.get("message") or "Client ID already exists"
                except Exception:
                    error_msg = "Client ID already exists"
                return False, None, error_msg
            return False, None, f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, None, str(exc)
    
    def update_profile(self, tags: Optional[List[str]] = None, note: Optional[str] = None, ip: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Update client profile (tags, note, ip) in Laravel DB.
        
        Args:
            tags: List of tags to set
            note: Note text
            ip: IP address
            
        Returns:
            (success, updated_profile_dict, message)
        """
        try:
            if not self._client_id:
                return False, None, "No client_id"
            if not self._token:
                return False, None, "Not authenticated"
            
            url = self._build_url(f"/api/client/{self._client_id}/profile")
            payload = {}
            if tags is not None:
                payload["tags"] = tags
            if note is not None:
                payload["note"] = note
            if ip is not None:
                payload["ip"] = ip
            
            resp = self._session.patch(url, json=payload, headers=self._auth_headers(), timeout=self._timeout_seconds)
            if 200 <= resp.status_code < 300:
                try:
                    data = resp.json()
                    client_data = data.get("client")
                    return True, client_data, "Profile updated"
                except Exception:
                    return True, None, "Profile updated"
            return False, None, f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, None, str(exc)

    def health(self) -> Tuple[bool, str]:
        """Check server health.

        Returns (is_online, message)
        """
        try:
            # First try Laravel admin API health route
            url = self._build_url("/admin-api/ai/health")
            resp = self._session.get(url, timeout=self._timeout_seconds)
            if 200 <= resp.status_code < 300:
                try:
                    data = resp.json()
                    msg = data.get("status") or "OK"
                except Exception:
                    msg = "OK"
                return True, msg
            # If the Laravel route is not found, try FastAPI native health
            if resp.status_code == 404:
                try:
                    url2 = self._build_url("/health")
                    resp2 = self._session.get(url2, timeout=self._timeout_seconds)
                    if 200 <= resp2.status_code < 300:
                        return True, "OK"
                    return False, f"HTTP {resp2.status_code}"
                except Exception as e2:
                    return False, str(e2)
            return False, f"HTTP {resp.status_code}"
        except Exception as exc:
            # If connection fails (e.g., pointing directly to FastAPI), try its /health
            try:
                url2 = self._build_url("/health")
                resp2 = self._session.get(url2, timeout=self._timeout_seconds)
                if 200 <= resp2.status_code < 300:
                    return True, "OK"
                return False, f"HTTP {resp2.status_code}"
            except Exception:
                return False, str(exc)

    def register(self, email: str, password: str) -> Tuple[bool, str]:
        try:
            # Laravel API route for client registration
            url = self._build_url("/api/client/register")
            payload = {"email": email, "password": password}
            resp = self._session.post(url, json=payload, headers=self._auth_headers(), timeout=self._timeout_seconds)
            if 200 <= resp.status_code < 300:
                return True, "Registered successfully"
            # Fallback to FastAPI register if 404/405 or connection to FastAPI directly
            if resp.status_code in (404, 405):
                self._username = email
                ok, msg = self.register_fastapi()
                if ok:
                    # Create a dummy token so UI flow can proceed
                    self._token = self._token or "FASTAPI_LOCAL_TOKEN"
                    self._save_identity()
                    return True, "Registered (FastAPI)"
                return False, msg
            try:
                data = resp.json()
                return False, data.get("message") or f"HTTP {resp.status_code}"
            except Exception:
                return False, f"HTTP {resp.status_code}"
        except Exception:
            # Likely pointed to FastAPI; attempt FastAPI register directly
            self._username = email
            ok, msg = self.register_fastapi()
            if ok:
                self._token = self._token or "FASTAPI_LOCAL_TOKEN"
                self._save_identity()
                return True, "Registered (FastAPI)"
            return False, msg

    def register_fastapi(self) -> Tuple[bool, str]:
        try:
            url = self._build_url("/register")
            payload = {
                "client_id": self._client_id or "",
                "ip": self._get_local_ip(),
                "meta": {
                    "username": self._username,
                },
            }
            resp = self._session.post(url, json=payload, headers=self._auth_headers(), timeout=self._timeout_seconds)
            if 200 <= resp.status_code < 300:
                self._registered_fastapi = True
                return True, "Registered"
            return False, f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, str(exc)

    def login(self, username: str, password: str) -> Tuple[bool, str]:
        try:
            # Laravel API route for client login
            url = self._build_url("/api/client/login")
            # Backend expects email, reuse username field in UI as email
            payload = {"email": username, "password": password}
            resp = self._session.post(url, json=payload, headers=self._auth_headers(), timeout=self._timeout_seconds)
            if 200 <= resp.status_code < 300:
                token: Optional[str] = None
                client_id_from_server: Optional[str] = None
                try:
                    data = resp.json()
                    token = data.get("token")
                    client_id_from_server = data.get("client_id")
                except Exception:
                    token = None
                if not token:
                    return False, "Token not found in response"
                self._token = token
                self._username = username
                
                # Update client_id if server returned one (from Laravel DB)
                if client_id_from_server:
                    self._client_id = client_id_from_server
                    self._save_identity()
                else:
                    # Keep existing client_id or create new one
                    if not self._client_id:
                        self._client_id = str(uuid.uuid4())
                    self._save_identity()
                
                # Set online status after successful login
                try:
                    if self._client_id:
                        self.set_online(True)
                except Exception:
                    # Don't fail login if online update fails
                    pass
                
                return True, "Logged in successfully"
            # Fallback to FastAPI mode on 404/405
            if resp.status_code in (404, 405):
                self._username = username
                # Ensure registered on FastAPI
                self.register_fastapi()
                # Create local token to satisfy UI/agent gate
                self._token = self._token or "FASTAPI_LOCAL_TOKEN"
                self._save_identity()
                return True, "Logged in (FastAPI mode)"
            try:
                data = resp.json()
                return False, data.get("message") or f"HTTP {resp.status_code}"
            except Exception:
                return False, f"HTTP {resp.status_code}"
        except Exception:
            # Likely a FastAPI base URL without Laravel; treat as local login
            self._username = username
            self.register_fastapi()
            self._token = self._token or "FASTAPI_LOCAL_TOKEN"
            self._save_identity()
            return True, "Logged in (FastAPI mode)"

    def send_metrics(self, metrics: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            # Attempt FastAPI registration một lần (best-effort, tránh spam)
            if not self._registered_fastapi:
                ok_reg, _ = self.register_fastapi()
                if not ok_reg:
                    # không coi là lỗi, chỉ log nhẹ phía UI
                    self._registered_fastapi = False

            now_ts = time.time()
            try:
                nio = psutil.net_io_counters()
                sent_bytes = getattr(nio, "bytes_sent", 0)
            except Exception:
                sent_bytes = 0

            if self._last_net_sent_bytes is not None and self._last_net_ts is not None:
                elapsed = max(0.001, now_ts - self._last_net_ts)
                network_out_bps = max(0.0, (sent_bytes - self._last_net_sent_bytes) / elapsed)
            else:
                network_out_bps = 0.0

            self._last_net_sent_bytes = sent_bytes
            self._last_net_ts = now_ts

            cpu_value = float(metrics.get("cpu_percent") if isinstance(metrics, dict) else 0.0)
            uptime_sec: Optional[int]
            try:
                boot_time = getattr(psutil, "boot_time", lambda: None)()
                uptime_sec = int(now_ts - boot_time) if boot_time else None
            except Exception:
                uptime_sec = None

            payload = {
                "client_id": self._client_id or "",
                "ip": self._get_local_ip(),
                "cpu": cpu_value,
                "network_out": float(network_out_bps),
                "connections_per_min": int(metrics.get("connections_per_min", 0)) if isinstance(metrics, dict) else 0,
                "uptime_sec": uptime_sec,
                "meta": {
                    "memory_percent": metrics.get("memory_percent") if isinstance(metrics, dict) else None,
                    "memory_used_mb": metrics.get("memory_used_mb") if isinstance(metrics, dict) else None,
                    "memory_total_mb": metrics.get("memory_total_mb") if isinstance(metrics, dict) else None,
                },
            }

            # Optimized: reduced path candidates to most common ones
            path_candidates = [
                "/metrics",  # FastAPI direct
                "/api/metrics",  # Laravel proxy
            ]

            last_status: Optional[int] = None
            # Try cached URL first for stability (giảm số endpoint phải thử mỗi lần)
            if self._metrics_url_cache:
                try:
                    resp = self._session.post(self._metrics_url_cache, json=payload, headers=self._auth_headers(), timeout=self._timeout_seconds)
                    if 200 <= resp.status_code < 300:
                        return True, "Metrics sent"
                    else:
                        # Invalidate and fall back to discovery
                        self._metrics_url_cache = None
                        last_status = resp.status_code
                except Exception:
                    self._metrics_url_cache = None
            # Ưu tiên thử Python server (5000) trước cho metrics endpoint
            for base in self._candidate_base_urls(prefer_python=True):
                for path in path_candidates:
                    try:
                        url = (base.rstrip("/") + path)
                        resp = self._session.post(url, json=payload, headers=self._auth_headers(), timeout=self._timeout_seconds)
                        last_status = resp.status_code
                        if 200 <= resp.status_code < 300:
                            self._metrics_url_cache = url
                            return True, "Metrics sent"
                        if resp.status_code in (404, 405):
                            continue
                    except Exception:
                        continue
            if last_status is not None:
                return False, f"HTTP {last_status}"
            return False, "No reachable metrics endpoint"
        except Exception as exc:
            return False, str(exc)

    def get_command(self) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Poll server for command.

        Returns (ok, command_dict_or_none, message)
        """
        try:
            # Optimized: reduced to most common endpoints
            path_candidates = [
                "/commands/next",  # FastAPI direct
                "/api/commands/next",  # Laravel proxy
            ]

            last_status = None
            last_error: Optional[str] = None
            # Try cached first for stability
            if self._command_url_cache:
                try:
                    params = {
                        "client_id": self._client_id or "",
                        "clientId": self._client_id or "",
                        "id": self._client_id or "",
                    }
                    resp = self._session.get(
                        self._command_url_cache,
                        params=params,
                        headers=self._auth_headers(),
                        timeout=self._timeout_seconds,
                    )
                    if resp.status_code == 204:
                        return True, None, "No command"
                    if 200 <= resp.status_code < 300:
                        try:
                            data = resp.json()
                        except Exception:
                            data = None
                        if isinstance(data, dict):
                            if "command" in data and isinstance(data.get("command"), dict):
                                return True, data.get("command"), "OK"
                            if any(k in data for k in ("action", "cmd", "type", "status", "state", "message")):
                                return True, data, "OK"
                            if isinstance(data.get("data"), dict):
                                return True, data.get("data"), "OK"
                        return True, data, "OK"
                    else:
                        last_status = resp.status_code
                        self._command_url_cache = None
                except Exception as e:
                    last_error = str(e)
                    self._command_url_cache = None
            # Ưu tiên thử Python server (5000) trước cho commands endpoint
            for base in self._candidate_base_urls(prefer_python=True):
                for path in path_candidates:
                    try:
                        url = (base.rstrip("/") + path)
                        # include alternative param names for compatibility
                        params = {
                            "client_id": self._client_id or "",
                            "clientId": self._client_id or "",
                            "id": self._client_id or "",
                        }
                        resp = self._session.get(
                            url,
                            params=params,
                            headers=self._auth_headers(),
                            timeout=self._timeout_seconds,
                        )
                        last_status = resp.status_code
                        if resp.status_code == 204:
                            return True, None, "No command"
                        if 200 <= resp.status_code < 300:
                            try:
                                data = resp.json()
                            except Exception:
                                data = None

                            # Normalize common response shapes
                            if isinstance(data, dict):
                                if "command" in data and isinstance(data.get("command"), dict):
                                    self._command_url_cache = url
                                    return True, data.get("command"), "OK"
                                # Some servers return the command fields at the root
                                if any(k in data for k in ("action", "cmd", "type", "status", "state", "message")):
                                    self._command_url_cache = url
                                    return True, data, "OK"
                                # Nested under 'data'
                                if isinstance(data.get("data"), dict):
                                    self._command_url_cache = url
                                    return True, data.get("data"), "OK"
                            self._command_url_cache = url
                            return True, data, "OK"
                        # try next candidate on 404/405
                        if resp.status_code in (404, 405):
                            continue
                    except Exception as e:
                        last_error = str(e)
                        continue

            if last_status is not None:
                return False, None, f"HTTP {last_status}"
            return False, None, last_error or "No reachable command endpoint"
        except Exception as exc:
            return False, None, str(exc)

    def send_command_result(self, result: Dict[str, Any]) -> Tuple[bool, str]:
        """Send command execution result back to server.
        
        Args:
            result: Result dictionary from CommandExecutor
            
        Returns:
            (success, message)
        """
        try:
            # Optimized: reduced to most common endpoints
            path_candidates = [
                "/command/result",  # FastAPI direct
                "/api/command/result",  # Laravel proxy
            ]
            
            last_status = None
            for base in self._candidate_base_urls(prefer_python=True):
                for path in path_candidates:
                    try:
                        url = (base.rstrip("/") + path)
                        resp = self._session.post(
                            url,
                            json=result,
                            headers=self._auth_headers(),
                            timeout=self._timeout_seconds,
                        )
                        last_status = resp.status_code
                        if 200 <= resp.status_code < 300:
                            return True, "Result sent"
                        if resp.status_code in (404, 405):
                            continue
                    except Exception:
                        continue
            
            if last_status is not None:
                return False, f"HTTP {last_status}"
            return False, "No reachable result endpoint"
        except Exception as exc:
            return False, str(exc)

    # -----------------------------
    # Metrics
    # -----------------------------
    @staticmethod
    def collect_metrics() -> Dict[str, Any]:
        # Optimized: shorter sampling interval for faster response (0.1s instead of 0.2s)
        cpu_percent = psutil.cpu_percent(interval=0.1)
        vm = psutil.virtual_memory()
        metrics = {
            "cpu_percent": float(cpu_percent),
            "memory_percent": float(vm.percent),
            "memory_used_mb": round(vm.used / (1024 * 1024), 2),
            "memory_total_mb": round(vm.total / (1024 * 1024), 2),
            "timestamp": int(time.time()),
        }
        return metrics


class AgentRunner:
    """Background worker that periodically sends metrics and polls commands.

    It relies on callbacks provided by the UI layer for logging and UI-thread execution.
    """

    def __init__(
        self,
        api_client: ApiClient,
        log_fn: Callable[[str], None],
        on_control_request: Callable[[], None],
        ui_executor: Callable[[Callable[[], None]], None],
        on_command: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self._api = api_client
        self._log = log_fn
        self._on_control_request = on_control_request
        self._ui_executor = ui_executor
        # Generic command callback to UI layer
        self._on_command_callback: Callable[[Dict[str, Any]], None] = (
            on_command if callable(on_command) else (lambda _cmd: None)
        )

        self._stop_event = threading.Event()
        self._metrics_thread: Optional[threading.Thread] = None
        self._command_thread: Optional[threading.Thread] = None
        self._start_stop_lock = threading.Lock()
        self._running: bool = False
        self._last_profile_check_ts: float = 0.0
        self._metrics_enabled: bool = False
        
        # Command executor for handling execute_command, get_system_info, etc.
        self._command_executor: Optional[CommandExecutor] = None
        if CommandExecutor:
            try:
                self._command_executor = CommandExecutor()
            except Exception as e:
                self._log(f"Failed to initialize command executor: {e}")
        
        # Callback for metrics sent (to update UI timestamps)
        self._on_metrics_sent_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Anti-spam: track last log messages to avoid duplicates
        self._last_log_message: Optional[str] = None
        self._last_log_time: float = 0.0
        self._log_repeat_count: int = 0
        self._log_throttle_seconds = 3.0  # Don't repeat same message within 3 seconds

    @property
    def is_running(self) -> bool:
        return self._running
    
    def set_metrics_sent_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set callback to be called when metrics are sent"""
        self._on_metrics_sent_callback = callback
    
    def _on_metrics_sent(self, metrics: Dict[str, Any]) -> None:
        """Internal callback when metrics are sent"""
        if self._on_metrics_sent_callback:
            try:
                self._on_metrics_sent_callback(metrics)
            except Exception:
                pass
    
    def _log_throttled(self, message: str) -> None:
        """Log with throttling to avoid spam of duplicate messages"""
        now = time.time()
        
        # Normalize message (remove timestamps, etc.)
        normalized = message.strip()
        
        # Skip empty or "None" messages
        if not normalized or normalized.lower() in ("none", "null", ""):
            return
        
        # Check if same as last message
        if normalized == self._last_log_message:
            # Same message - check throttle
            if now - self._last_log_time < self._log_throttle_seconds:
                self._log_repeat_count += 1
                # Don't log, just count
                return
            else:
                # Time passed, log with repeat count if > 1
                if self._log_repeat_count > 1:
                    self._log(f"{self._last_log_message} (x{self._log_repeat_count})")
                    self._log_repeat_count = 0
                # Fall through to log new message
        
        # Different message or throttle passed - log it
        if self._log_repeat_count > 1 and self._last_log_message:
            # Log previous message with repeat count first
            self._log(f"{self._last_log_message} (x{self._log_repeat_count})")
            self._log_repeat_count = 0
        
        self._log(message)
        self._last_log_message = normalized
        self._last_log_time = now

    def set_metrics_enabled(self, enabled: bool) -> None:
        self._metrics_enabled = bool(enabled)
        self._log(f"Auto metrics {'enabled' if self._metrics_enabled else 'disabled'}.")

    def start(self) -> bool:
        with self._start_stop_lock:
            if self._running:
                return False
            if not self._api.base_url:
                self._log("Server URL is not set. Please connect first.")
                return False
            if not self._api.token:
                self._log("You must log in before starting the agent.")
                return False

            # Mark online in DB (best effort)
            try:
                ok, msg = self._api.set_online(True)
                if ok:
                    self._log("Marked online in database.")
                else:
                    self._log(f"Failed to mark online in DB: {msg}")
            except Exception as e:
                self._log(f"Online mark error: {e}")

            # Initial DB status check (best effort)
            try:
                ok, prof, _ = self._api.get_profile()
                if ok and isinstance(prof, dict):
                    status_val = int(prof.get("status", 1) or 1)
                    online_val = bool(prof.get("online", False))
                    if status_val == 3:
                        # Block immediately according to DB - defer stop to avoid deadlock
                        self._log("Client is blocked (status=3), stopping agent")
                        # Set stop event first
                        self._stop_event.set()
                        # Defer UI callback to avoid deadlock (use threading.Timer instead of QtCore.QTimer)
                        def notify_block():
                            self._ui_executor(lambda: self._on_command_callback({"action": "block", "message": "Blocked by database status"}))
                        threading.Timer(0.1, notify_block).start()
                    elif status_val == 2:
                        self._ui_executor(lambda: self._on_command_callback({"action": "notify", "message": "Warning from database status"}))
                    # Only log profile if status or online changed
                    profile_msg = f"DB profile: status={status_val} | online={online_val}"
                    self._log_throttled(profile_msg)
                self._last_profile_check_ts = time.time()
            except Exception as e:
                self._log(f"Profile check error: {e}")

            self._stop_event.clear()
            self._metrics_thread = threading.Thread(target=self._metrics_loop, name="AgentMetricsThread", daemon=True)
            self._command_thread = threading.Thread(target=self._command_loop, name="AgentCommandThread", daemon=True)
            self._metrics_thread.start()
            self._command_thread.start()
            self._running = True
            self._log("Agent started.")
            return True

    def stop(self) -> bool:
        # Try to acquire lock with timeout to avoid deadlock
        if not self._start_stop_lock.acquire(timeout=1.0):
            # Lock is held (probably by start()), set stop event and return
            self._stop_event.set()
            self._log("Stop requested (lock held, will stop when start completes)")
            return False
        
        try:
            if not self._running:
                return False
            self._stop_event.set()
            for t in (self._metrics_thread, self._command_thread):
                if t and t.is_alive():
                    t.join(timeout=3.0)
            self._running = False
            self._log("Agent stopped.")
            # Best-effort mark offline
            try:
                self._api.set_online(False)
            except Exception:
                pass
            return True
        finally:
            self._start_stop_lock.release()

    # -----------------------------
    # Internal loops
    # -----------------------------
    def _sleep_with_stop(self, total_seconds: float, step_seconds: float = 0.25) -> None:
        remaining = float(total_seconds)
        while remaining > 0 and not self._stop_event.is_set():
            time.sleep(min(step_seconds, remaining))
            remaining -= step_seconds

    def _metrics_loop(self) -> None:
        # Metrics loop is now disabled by default - metrics only sent when server requests via "request_metrics" action
        # This loop now only handles periodic profile checks
        while not self._stop_event.is_set():
            try:
                # Auto-send metrics is disabled - only send when server requests via "request_metrics" action
                # Keep this loop for profile checks only
                
                # Periodically re-check DB profile (every ~30s)
                now = time.time()
                if now - (self._last_profile_check_ts or 0.0) >= 30.0:
                    try:
                        okp, prof, _ = self._api.get_profile()
                        if okp and isinstance(prof, dict):
                            status_val = int(prof.get("status", 1) or 1)
                            online_val = bool(prof.get("online", False))
                            if status_val == 3:
                                self._ui_executor(lambda: self._on_command_callback({"action": "block", "message": "Blocked by database status"}))
                            elif status_val == 2:
                                self._ui_executor(lambda: self._on_command_callback({"action": "notify", "message": "Database status: warning"}))
                            # Only log profile if status or online changed
                            profile_msg = f"DB profile: status={status_val} | online={online_val}"
                            self._log_throttled(profile_msg)
                    except Exception as e:
                        self._log(f"Profile check error: {e}")
                    finally:
                        self._last_profile_check_ts = now
            except Exception as exc:
                self._log(f"Profile check error: {exc}")
            self._sleep_with_stop(30.0)  # Check profile every 30 seconds

    def _command_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                ok, command, msg = self._api.get_command()
                if ok:
                    if command:
                        # Heuristic: treat any field value equal to 'request_control' as control request
                        values = list(command.values()) if isinstance(command, dict) else []
                        if any(isinstance(v, str) and v.lower() == "request_control" for v in values):
                            # Ensure popup runs on UI thread
                            self._ui_executor(self._on_control_request)
                            self._log("Control request received from server.")
                        
                        # Route actionable commands
                        if isinstance(command, dict):
                            try:
                                action = str(command.get("action", "")).lower()
                                msg_text = str(command.get("message", "")).strip()
                                
                                # Handle start_vnc_server command
                                if action == "start_vnc_server":
                                    self._log("Starting VNC server...")
                                    try:
                                        from vnc_manager import VNCManager
                                        
                                        vnc_manager = VNCManager()
                                        password = command.get("password", "")
                                        port = command.get("port")
                                        display = command.get("display")
                                        
                                        result = vnc_manager.start_vnc_server(
                                            password=password, 
                                            port=port,
                                            display=display
                                        )
                                        
                                        if result.get("success"):
                                            self._log(f"VNC server started on port {result.get('port', port)}")
                                            
                                            # Get client IP for VNC connection
                                            import socket
                                            try:
                                                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                                                s.connect(("8.8.8.8", 80))
                                                client_ip = s.getsockname()[0]
                                                s.close()
                                            except Exception:
                                                client_ip = "127.0.0.1"
                                            
                                            # Send command result to server (so server can store VNC info)
                                            command_result = {
                                                "command_id": command.get("command_id", ""),
                                                "client_id": self._api._client_id or command.get("client_id", ""),
                                                "action": "start_vnc_server",
                                                "success": True,
                                                "output": f"VNC server started on port {result.get('port')}",
                                                "error": None,
                                                "exit_code": 0,
                                                "metadata": {
                                                    "action": "start_vnc_server",
                                                    "port": result.get("port"),
                                                    "display": result.get("display"),
                                                    "password_set": bool(result.get("password")),
                                                    "client_ip": client_ip,
                                                },
                                            }
                                            try:
                                                self._api.send_command_result(command_result)
                                            except Exception as e:
                                                self._log(f"Failed to send VNC result to server: {e}")
                                            
                                            # Notify UI with connection info
                                            self._ui_executor(lambda r=result: self._on_command_callback({
                                                "action": "vnc_started",
                                                "message": f"VNC server started",
                                                "result": r,
                                            }))
                                        else:
                                            self._log(f"Failed to start VNC server: {result.get('error', 'Unknown error')}")
                                            # Send failure result too
                                            command_result = {
                                                "command_id": command.get("command_id", ""),
                                                "client_id": self._api._client_id or command.get("client_id", ""),
                                                "action": "start_vnc_server",
                                                "success": False,
                                                "output": None,
                                                "error": result.get("error", "Unknown error"),
                                                "exit_code": -1,
                                                "metadata": result,
                                            }
                                            try:
                                                self._api.send_command_result(command_result)
                                            except Exception:
                                                pass
                                    except Exception as e:
                                        self._log(f"Failed to start VNC server: {e}")
                                    # Continue to UI callback
                                
                                # Handle request_metrics - send metrics on demand
                                elif action == "request_metrics":
                                    self._log("Server requested metrics, sending...")
                                    try:
                                        metrics = self._api.collect_metrics()
                                        ok, msg = self._api.send_metrics(metrics)
                                        if ok:
                                            self._log(f"Metrics sent on request: CPU {metrics['cpu_percent']}% | RAM {metrics['memory_percent']}%")
                                            # Notify UI about metrics update
                                            self._ui_executor(lambda m=metrics: self._on_metrics_sent(m))
                                        else:
                                            self._log(f"Failed to send metrics on request: {msg}")
                                    except Exception as e:
                                        self._log(f"Error sending metrics on request: {e}")
                                
                                # Handle executable commands (execute_command, get_system_info, upload_file, download_file, get_screenshot, and new advanced features)
                                elif action in ("execute_command", "get_system_info", "upload_file", "download_file", "get_screenshot", "disable_network", "enable_network", "list_processes", "kill_process", "list_connections", "list_files", "control_service"):
                                    if self._command_executor:
                                        self._log(f"Executing command: {action}")
                                        # Add client_id to command if missing
                                        if "client_id" not in command and self._api._client_id:
                                            command["client_id"] = self._api._client_id
                                        
                                        # Execute command
                                        result = self._command_executor.execute(command)
                                        
                                        # Send result back to server
                                        try:
                                            self._api.send_command_result(result)
                                            self._log(f"Command {action} executed: {'success' if result.get('success') else 'failed'}")
                                        except Exception as e:
                                            self._log(f"Failed to send command result: {e}")
                                        
                                        # Also notify UI
                                        self._ui_executor(lambda c=command, r=result: self._on_command_callback({
                                            "action": action,
                                            "message": f"Command executed: {action}",
                                            "result": r,
                                        }))
                                    else:
                                        self._log(f"Command executor not available for: {action}")
                                else:
                                    # Log and notify UI for other commands (notify, block, unblock, shutdown, restart, etc.)
                                    if action:
                                        log_msg = f"Command received: {action}{' — ' + msg_text if msg_text else ''}"
                                        self._log_throttled(log_msg)
                                    # Invoke UI handler on UI thread for all commands
                                    self._ui_executor(lambda c=command: self._on_command_callback(c))
                            except Exception as _e:
                                # Swallow to keep loop healthy
                                self._log(f"Command processing error: {_e}")
                elif not ok:
                    # Only log if it's not a "No command" case (which is normal)
                    if "No command" not in msg and "No reachable" not in msg and "HTTP 404" not in msg:
                        self._log(f"Command poll failed: {msg}")
                    # If 404, try to clear cache to force rediscovery
                    if "HTTP 404" in msg:
                        self._api._command_url_cache = None
            except Exception as exc:
                self._log(f"Command loop error: {exc}")
            # Optimized: reduce polling interval from 10s to 5s for faster command pickup
            self._sleep_with_stop(5.0)


