from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Dict, List
from collections import deque

from .models import ClientInfo, CommandItem, LogEntry, CommandResult


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_FILE = DATA_DIR / "logs.jsonl"
PATTERN_FILE = DATA_DIR / "patterns.json"


class InMemoryState:
    def __init__(self) -> None:
        # Use Lock instead of RLock for better performance (most operations don't need reentrancy)
        self._lock = threading.Lock()
        self.client_id_to_client: Dict[str, ClientInfo] = {}
        # Use deque for queues - faster append/pop from left
        self.client_id_to_queue: Dict[str, deque] = {}
        # Use deque for history with maxlen for automatic size limiting
        self.client_id_to_history: Dict[str, deque] = {}
        self.command_id_to_result: Dict[str, CommandResult] = {}  # Store command results
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not PATTERN_FILE.exists():
            PATTERN_FILE.write_text(json.dumps({}, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert_client(self, info: ClientInfo) -> None:
        with self._lock:
            self.client_id_to_client[info.client_id] = info

    def get_clients(self) -> List[ClientInfo]:
        with self._lock:
            # Trả về shallow copy để tránh sửa trực tiếp trên state gốc
            return list(self.client_id_to_client.values())

    def get_client(self, client_id: str) -> ClientInfo | None:
        with self._lock:
            return self.client_id_to_client.get(client_id)

    def update_client(self, client_id: str, *, tags=None, note=None, blocked=None) -> ClientInfo | None:
        with self._lock:
            client = self.client_id_to_client.get(client_id)
            if not client:
                return None
            if tags is not None:
                client.tags = list(dict.fromkeys(tags))
            if note is not None:
                client.note = note
            if blocked is not None:
                client.blocked = bool(blocked)
            self.client_id_to_client[client_id] = client
            return client

    def rename_client(self, old_client_id: str, new_client_id: str) -> bool:
        """Rename client (update client_id) while preserving all data."""
        with self._lock:
            if old_client_id not in self.client_id_to_client:
                return False
            if new_client_id in self.client_id_to_client and new_client_id != old_client_id:
                # New ID already exists and it's different client
                return False
            
            # Get old client data
            old_client = self.client_id_to_client[old_client_id]
            old_queue = self.client_id_to_queue.get(old_client_id)
            old_history = self.client_id_to_history.get(old_client_id)
            
            # Create new client with new ID but same data
            new_client = ClientInfo(
                client_id=new_client_id,
                ip=old_client.ip,
                meta=old_client.meta,
                last_seen_ts=old_client.last_seen_ts,
                blocked=old_client.blocked,
                tags=old_client.tags,
                note=old_client.note,
            )
            
            # Remove old client
            self.client_id_to_client.pop(old_client_id, None)
            self.client_id_to_queue.pop(old_client_id, None)
            self.client_id_to_history.pop(old_client_id, None)
            
            # Add new client with migrated data
            self.client_id_to_client[new_client_id] = new_client
            if old_queue:
                self.client_id_to_queue[new_client_id] = old_queue
            if old_history:
                self.client_id_to_history[new_client_id] = old_history
            
            return True
    
    def delete_client(self, client_id: str) -> bool:
        with self._lock:
            existed = client_id in self.client_id_to_client
            self.client_id_to_client.pop(client_id, None)
            self.client_id_to_queue.pop(client_id, None)
            self.client_id_to_history.pop(client_id, None)
            return existed

    def enqueue_command(self, command: CommandItem) -> None:
        with self._lock:
            queue = self.client_id_to_queue.setdefault(command.client_id, deque())
            queue.append(command)

    def pop_next_command(self, client_id: str) -> CommandItem | None:
        with self._lock:
            queue = self.client_id_to_queue.get(client_id)
            if queue and len(queue) > 0:
                return queue.popleft()
            return None

    def get_queue(self, client_id: str) -> List[CommandItem]:
        with self._lock:
            queue = self.client_id_to_queue.get(client_id)
            if queue:
                return list(queue)
            return []

    def clear_queue(self, client_id: str) -> int:
        with self._lock:
            queue = self.client_id_to_queue.get(client_id)
            if queue:
                n = len(queue)
                queue.clear()
                return n
            return 0

    def add_history_point(self, client_id: str, snapshot: dict) -> None:
        with self._lock:
            # Use deque with maxlen for automatic size limiting (more efficient)
            if client_id not in self.client_id_to_history:
                self.client_id_to_history[client_id] = deque(maxlen=200)
            self.client_id_to_history[client_id].append(snapshot)

    def get_history(self, client_id: str) -> List[dict]:
        with self._lock:
            # Trả về bản sao để tránh sửa list nội bộ
            history = self.client_id_to_history.get(client_id)
            if history:
                return list(history)
            return []

    def clear_history(self, client_id: str) -> int:
        with self._lock:
            history = self.client_id_to_history.get(client_id)
            if history:
                n = len(history)
                history.clear()
                return n
            return 0

    def get_last_snapshot(self, client_id: str) -> dict | None:
        with self._lock:
            history = self.client_id_to_history.get(client_id)
            if history and len(history) > 0:
                return history[-1]
            return None

    def write_log(self, entry: LogEntry) -> None:
        line = entry.model_dump_json()
        with self._lock:
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

    def get_patterns(self) -> dict:
        with self._lock:
            try:
                return json.loads(PATTERN_FILE.read_text(encoding="utf-8") or "{}")
            except Exception:
                return {}

    def set_patterns(self, patterns: dict) -> None:
        payload = json.dumps(patterns, ensure_ascii=False, indent=2)
        with self._lock:
            PATTERN_FILE.write_text(payload, encoding="utf-8")

    def store_command_result(self, result: CommandResult) -> None:
        """Store command execution result"""
        with self._lock:
            self.command_id_to_result[result.command_id] = result
            # Keep only last 1000 results
            if len(self.command_id_to_result) > 1000:
                # Remove oldest entries (simple FIFO)
                oldest_keys = list(self.command_id_to_result.keys())[:-1000]
                for key in oldest_keys:
                    del self.command_id_to_result[key]
    
    def get_command_result(self, command_id: str) -> CommandResult | None:
        """Get command execution result by command_id"""
        with self._lock:
            return self.command_id_to_result.get(command_id)

    def get_stats(self) -> dict:
        with self._lock:
            num_clients = len(self.client_id_to_client)
            num_blocked = sum(1 for c in self.client_id_to_client.values() if c.blocked)
            # Optimized: deque has len() which is O(1)
            num_queued = sum(len(q) for q in self.client_id_to_queue.values() if q)
        last_log_ts = 0.0
        try:
            with LOG_FILE.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        ts = float(obj.get("ts", 0.0))
                        if ts > last_log_ts:
                            last_log_ts = ts
                    except Exception:
                        continue
        except FileNotFoundError:
            last_log_ts = 0.0
        return {
            "num_clients": num_clients,
            "num_blocked": num_blocked,
            "num_queued_commands": num_queued,
            "last_log_ts": last_log_ts,
            "now": time.time(),
        }


STATE = InMemoryState()

