from __future__ import annotations

from typing import Literal, Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    client_id: str
    ip: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class MetricsPayload(BaseModel):
    client_id: str
    ip: Optional[str] = None
    cpu: float
    network_out: float
    connections_per_min: int
    uptime_sec: Optional[int] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ControlRequest(BaseModel):
    client_id: str
    # thêm 'request_control' để server có thể gửi yêu cầu điều khiển chủ động
    action: Literal["shutdown", "restart", "block", "notify", "unblock", "request_control", "request_metrics", "execute_command", "get_system_info", "upload_file", "download_file", "get_screenshot", "start_vnc_server", "disable_network", "enable_network", "list_processes", "kill_process", "list_connections", "list_files", "control_service"]
    message: Optional[str] = None
    source: Literal["Admin", "AI"] = "Admin"
    source_user: Optional[str] = None
    # Command-specific parameters
    command: Optional[str] = None  # For execute_command: shell command to run
    file_path: Optional[str] = None  # For upload_file/download_file: file path
    file_data: Optional[str] = None  # For upload_file: base64 encoded file data
    target_path: Optional[str] = None  # For download_file: target path on server
    # New parameters for advanced features
    process_id: Optional[int] = None  # For kill_process: PID to kill
    service_name: Optional[str] = None  # For control_service: service name
    service_action: Optional[str] = None  # For control_service: start/stop/restart/status
    directory_path: Optional[str] = None  # For list_files: directory to list


class CommandItem(BaseModel):
    client_id: str
    # đồng bộ với ControlRequest.action
    action: Literal["shutdown", "restart", "block", "notify", "unblock", "request_control", "request_metrics", "execute_command", "get_system_info", "upload_file", "download_file", "get_screenshot", "start_vnc_server", "disable_network", "enable_network", "list_processes", "kill_process", "list_connections", "list_files", "control_service"]
    message: Optional[str] = None
    source: Literal["Admin", "AI"]
    source_user: Optional[str] = None
    # Command-specific parameters
    command: Optional[str] = None  # For execute_command: shell command to run
    file_path: Optional[str] = None  # For upload_file/download_file: file path
    file_data: Optional[str] = None  # For upload_file: base64 encoded file data
    target_path: Optional[str] = None  # For download_file: target path on server
    command_id: Optional[str] = None  # Unique ID for tracking command execution
    # New parameters for advanced features
    process_id: Optional[int] = None  # For kill_process: PID to kill
    service_name: Optional[str] = None  # For control_service: service name
    service_action: Optional[str] = None  # For control_service: start/stop/restart/status
    directory_path: Optional[str] = None  # For list_files: directory to list


class ClientInfo(BaseModel):
    client_id: str
    ip: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    last_seen_ts: float = 0.0
    blocked: bool = False
    tags: List[str] = Field(default_factory=list)
    note: Optional[str] = None


class LogEntry(BaseModel):
    ts: float
    source: Literal["Admin", "AI"]
    action: str
    client_id: str
    reason: Optional[str] = None
    source_user: Optional[str] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class AIAnalyzeInput(BaseModel):
    client_id: str
    cpu: float
    network_out: float
    connections_per_min: int
    history: List[Dict[str, Any]] = Field(default_factory=list)


class AIAnalyzeResult(BaseModel):
    client_id: str
    status: Literal["allow", "warn", "block"]
    reason: str


class PatternsUpdate(BaseModel):
    patterns: Dict[str, Any] = Field(default_factory=dict)


class BulkControlRequest(BaseModel):
    client_ids: List[str] = Field(default_factory=list)
    # hỗ trợ bulk request_control luôn
    action: Literal["shutdown", "restart", "block", "notify", "unblock", "request_control", "request_metrics", "execute_command", "get_system_info", "upload_file", "download_file", "get_screenshot", "start_vnc_server", "disable_network", "enable_network", "list_processes", "kill_process", "list_connections", "list_files", "control_service"]
    message: Optional[str] = None
    source: Literal["Admin", "AI"] = "Admin"
    source_user: Optional[str] = None
    # Command-specific parameters
    command: Optional[str] = None
    file_path: Optional[str] = None
    file_data: Optional[str] = None
    target_path: Optional[str] = None
    # New parameters for advanced features
    process_id: Optional[int] = None
    service_name: Optional[str] = None
    service_action: Optional[str] = None
    directory_path: Optional[str] = None

    # Optional filters when client_ids empty
    q: Optional[str] = None
    tag: Optional[str] = None
    blocked: Optional[bool] = None


class CommandResult(BaseModel):
    """Result from agent after executing a command"""
    command_id: str
    client_id: str
    action: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('metadata', mode='before')
    @classmethod
    def normalize_metadata(cls, v: Any) -> Dict[str, Any]:
        """Convert list to dict if needed, ensure it's always a dict"""
        if v is None:
            return {}
        if isinstance(v, list):
            # Convert list to dict with index keys, or empty dict if empty
            if len(v) == 0:
                return {}
            # Try to convert list of key-value pairs to dict
            if all(isinstance(item, (list, tuple)) and len(item) == 2 for item in v):
                return {str(k): v for k, v in v}
            # Otherwise, convert to dict with index keys
            return {str(i): item for i, item in enumerate(v)}
        if isinstance(v, dict):
            return v
        # For any other type, wrap in a dict
        return {"value": v}


class ClientUpdate(BaseModel):
    tags: Optional[List[str]] = None
    note: Optional[str] = None
    blocked: Optional[bool] = None


class BulkTagsRequest(BaseModel):
    client_ids: List[str] = Field(default_factory=list)
    add: List[str] = Field(default_factory=list)
    remove: List[str] = Field(default_factory=list)
    # optional filters if client_ids empty
    q: Optional[str] = None
    tag: Optional[str] = None
    blocked: Optional[bool] = None