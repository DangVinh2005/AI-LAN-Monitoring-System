#!/usr/bin/env python3
"""
command_executor.py

Command router and executor for client-agent.
Handles execution of commands received from server:
- execute_command: Run shell commands
- get_system_info: Collect system information
- upload_file: Receive file from server
- download_file: Send file to server

Designed for Python 3.13. Thread-safe execution.
"""

from __future__ import annotations

import base64
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import psutil

# Import screen capture
try:
    from screen_capture import ScreenCapture
    HAS_SCREEN_CAPTURE = True
except ImportError:
    HAS_SCREEN_CAPTURE = False


class CommandExecutor:
    """Execute commands received from server in a safe, controlled manner."""

    def __init__(self, base_path: Optional[str] = None):
        """
        Args:
            base_path: Base directory for file operations (default: current directory)
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._screen_capture = ScreenCapture() if HAS_SCREEN_CAPTURE else None

    def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route command to appropriate handler based on action.

        Args:
            command: Command dictionary from server

        Returns:
            Result dictionary with success, output, error, etc.
        """
        action = str(command.get("action", "")).lower()
        command_id = command.get("command_id") or f"cmd_{int(time.time() * 1000)}"
        
        start_time = time.time()
        result = {
            "command_id": command_id,
            "client_id": command.get("client_id", ""),
            "action": action,
            "success": False,
            "output": None,
            "error": None,
            "exit_code": None,
            "execution_time_ms": 0.0,
            "metadata": {},
        }

        try:
            if action == "execute_command":
                result.update(self.handle_execute_command(command))
            elif action == "get_system_info":
                result.update(self.handle_get_system_info(command))
            elif action == "upload_file":
                result.update(self.handle_upload_file(command))
            elif action == "download_file":
                result.update(self.handle_download_file(command))
            elif action == "get_screenshot":
                result.update(self.handle_get_screenshot(command))
            elif action == "start_vnc_server":
                result.update(self.handle_start_vnc_server(command))
            elif action == "disable_network":
                result.update(self.handle_disable_network(command))
            elif action == "enable_network":
                result.update(self.handle_enable_network(command))
            elif action == "list_processes":
                result.update(self.handle_list_processes(command))
            elif action == "kill_process":
                result.update(self.handle_kill_process(command))
            elif action == "list_connections":
                result.update(self.handle_list_connections(command))
            elif action == "list_files":
                result.update(self.handle_list_files(command))
            elif action == "control_service":
                result.update(self.handle_control_service(command))
            else:
                result["error"] = f"Unknown action: {action}"
                result["success"] = False
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
        finally:
            result["execution_time_ms"] = (time.time() - start_time) * 1000

        return result

    def handle_execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute shell command.

        Args:
            command: Must contain 'command' field with shell command string

        Returns:
            Result dict with output, error, exit_code
        """
        cmd_str = command.get("command")
        if not cmd_str:
            return {
                "success": False,
                "error": "No command specified",
                "output": None,
                "exit_code": -1,
            }

        try:
            # Security: Limit command execution time and output size
            process = subprocess.Popen(
                cmd_str,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,  # 5 minutes max
            )
            stdout, stderr = process.communicate()
            exit_code = process.returncode

            # Limit output size (prevent huge outputs)
            max_output_size = 100000  # 100KB
            if stdout and len(stdout) > max_output_size:
                stdout = stdout[:max_output_size] + "\n... (truncated)"
            if stderr and len(stderr) > max_output_size:
                stderr = stderr[:max_output_size] + "\n... (truncated)"

            return {
                "success": exit_code == 0,
                "output": stdout,
                "error": stderr if stderr else None,
                "exit_code": exit_code,
                "metadata": {"command": cmd_str},
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command execution timeout (5 minutes)",
                "output": None,
                "exit_code": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "output": None,
                "exit_code": -1,
            }

    def handle_get_system_info(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect system information (CPU, RAM, OS, uptime, etc.).

        Returns:
            Result dict with system info in output/metadata
        """
        try:
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # Memory info
            vm = psutil.virtual_memory()
            memory_info = {
                "total_mb": round(vm.total / (1024 * 1024), 2),
                "available_mb": round(vm.available / (1024 * 1024), 2),
                "used_mb": round(vm.used / (1024 * 1024), 2),
                "percent": vm.percent,
            }

            # Disk info
            disk = psutil.disk_usage("/")
            disk_info = {
                "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                "used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                "free_gb": round(disk.free / (1024 * 1024 * 1024), 2),
                "percent": disk.percent,
            }

            # Uptime
            boot_time = psutil.boot_time()
            uptime_sec = int(time.time() - boot_time)

            # OS info
            os_info = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
            }

            # Network info
            try:
                net_io = psutil.net_io_counters()
                network_info = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                }
            except Exception:
                network_info = {}

            info = {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                },
                "memory": memory_info,
                "disk": disk_info,
                "uptime_sec": uptime_sec,
                "os": os_info,
                "network": network_info,
                "timestamp": time.time(),
            }

            import json
            output = json.dumps(info, indent=2)

            return {
                "success": True,
                "output": output,
                "error": None,
                "exit_code": 0,
                "metadata": info,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to collect system info: {str(e)}",
                "output": None,
                "exit_code": -1,
            }

    def handle_upload_file(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receive file from server and save locally.

        Args:
            command: Must contain 'file_path' (target path) and 'file_data' (base64 encoded)

        Returns:
            Result dict
        """
        file_path = command.get("file_path")
        file_data_b64 = command.get("file_data")

        if not file_path:
            return {
                "success": False,
                "error": "No file_path specified",
                "output": None,
                "exit_code": -1,
            }

        if not file_data_b64:
            return {
                "success": False,
                "error": "No file_data specified",
                "output": None,
                "exit_code": -1,
            }

        try:
            # Decode base64 data
            file_data = base64.b64decode(file_data_b64)

            # Resolve target path (relative to base_path)
            target_path = self.base_path / file_path.lstrip("/")
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            target_path.write_bytes(file_data)

            return {
                "success": True,
                "output": f"File saved to: {target_path}",
                "error": None,
                "exit_code": 0,
                "metadata": {
                    "file_path": str(target_path),
                    "size_bytes": len(file_data),
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save file: {str(e)}",
                "output": None,
                "exit_code": -1,
            }

    def handle_download_file(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read local file and return base64 encoded data.

        Args:
            command: Must contain 'file_path' (local file path)

        Returns:
            Result dict with file_data in output/metadata
        """
        file_path = command.get("file_path")

        if not file_path:
            return {
                "success": False,
                "error": "No file_path specified",
                "output": None,
                "exit_code": -1,
            }

        try:
            # Resolve file path (relative to base_path or absolute)
            if os.path.isabs(file_path):
                target_path = Path(file_path)
            else:
                target_path = self.base_path / file_path.lstrip("/")

            if not target_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {target_path}",
                    "output": None,
                    "exit_code": -1,
                }

            # Check file size limit (10MB)
            max_size = 10 * 1024 * 1024
            file_size = target_path.stat().st_size
            if file_size > max_size:
                return {
                    "success": False,
                    "error": f"File too large: {file_size} bytes (max {max_size})",
                    "output": None,
                    "exit_code": -1,
                }

            # Read and encode file
            file_data = target_path.read_bytes()
            file_data_b64 = base64.b64encode(file_data).decode("utf-8")

            return {
                "success": True,
                "output": file_data_b64,  # Base64 encoded file data
                "error": None,
                "exit_code": 0,
                "metadata": {
                    "file_path": str(target_path),
                    "size_bytes": file_size,
                    "file_data": file_data_b64,  # Also in metadata for convenience
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read file: {str(e)}",
                "output": None,
                "exit_code": -1,
            }

    def handle_get_screenshot(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Capture screen and return as base64 encoded JPEG.
        
        Args:
            command: Optional 'quality' (1-100, default 70), 'max_width', 'max_height'
        
        Returns:
            Result dict with base64 screenshot in output
        """
        if not self._screen_capture:
            return {
                "success": False,
                "error": "Screen capture not available (install mss or Pillow)",
                "output": None,
                "exit_code": -1,
            }
        
        try:
            quality = int(command.get("quality", 70))
            max_width = command.get("max_width")
            max_height = command.get("max_height")
            
            screenshot_b64, error = self._screen_capture.capture_screen_base64(
                quality=quality,
                max_width=max_width,
                max_height=max_height
            )
            
            if error:
                return {
                    "success": False,
                    "error": error,
                    "output": None,
                    "exit_code": -1,
                }
            
            screen_width, screen_height = self._screen_capture.get_screen_size()
            
            return {
                "success": True,
                "output": screenshot_b64,
                "error": None,
                "exit_code": 0,
                "metadata": {
                    "format": "jpeg",
                    "quality": quality,
                    "screen_width": screen_width,
                    "screen_height": screen_height,
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Screenshot error: {str(e)}",
                "output": None,
                "exit_code": -1,
            }
    
    def handle_start_vnc_server(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start VNC server for remote desktop access.
        
        Args:
            command: Optional 'password', 'port', 'display'
        
        Returns:
            Result dict with VNC server info
        """
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
                # Get client IP for VNC connection
                import socket
                try:
                    # Get local IP
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    client_ip = s.getsockname()[0]
                    s.close()
                except Exception:
                    client_ip = "127.0.0.1"
                
                return {
                    "success": True,
                    "output": f"VNC server started on port {result.get('port')}",
                    "error": None,
                    "exit_code": 0,
                    "metadata": {
                        "action": "start_vnc_server",  # Mark as VNC start
                        "port": result.get("port"),
                        "display": result.get("display"),
                        "password_set": bool(result.get("password")),
                        "client_ip": client_ip,
                    },
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "output": None,
                    "exit_code": -1,
                    "metadata": result,
                }
        except ImportError:
            return {
                "success": False,
                "error": "VNC manager not available",
                "output": None,
                "exit_code": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"VNC server error: {str(e)}",
                "output": None,
                "exit_code": -1,
            }
    
    def handle_disable_network(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Disable network connectivity (block all network traffic).
        
        Returns:
            Result dict with success status
        """
        try:
            system = platform.system()
            if system == "Linux":
                # Use iptables to block all outgoing traffic
                cmd = "sudo iptables -A OUTPUT -j DROP"
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = process.communicate()
                exit_code = process.returncode
                
                if exit_code == 0:
                    return {
                        "success": True,
                        "output": "Network disabled (all outgoing traffic blocked)",
                        "error": None,
                        "exit_code": 0,
                        "metadata": {"method": "iptables"},
                    }
                else:
                    # Try alternative: disable network interface
                    interface = command.get("interface", "eth0")
                    cmd2 = f"sudo ifdown {interface}"
                    process2 = subprocess.Popen(
                        cmd2,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    stdout2, stderr2 = process2.communicate()
                    if process2.returncode == 0:
                        return {
                            "success": True,
                            "output": f"Network interface {interface} disabled",
                            "error": None,
                            "exit_code": 0,
                            "metadata": {"method": "ifdown"},
                        }
                    return {
                        "success": False,
                        "error": f"Failed to disable network: {stderr or stderr2}",
                        "output": None,
                        "exit_code": exit_code,
                    }
            elif system == "Windows":
                # Disable network adapter using netsh
                adapter = command.get("adapter", "*")
                cmd = f'netsh interface set interface "{adapter}" admin=disable'
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = process.communicate()
                exit_code = process.returncode
                
                if exit_code == 0:
                    return {
                        "success": True,
                        "output": f"Network adapter {adapter} disabled",
                        "error": None,
                        "exit_code": 0,
                        "metadata": {"method": "netsh"},
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to disable network: {stderr}",
                        "output": None,
                        "exit_code": exit_code,
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported system: {system}",
                    "output": None,
                    "exit_code": -1,
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Network disable error: {str(e)}",
                "output": None,
                "exit_code": -1,
            }
    
    def handle_enable_network(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enable network connectivity (restore network traffic).
        
        Returns:
            Result dict with success status
        """
        try:
            system = platform.system()
            if system == "Linux":
                # Remove iptables DROP rule
                cmd = "sudo iptables -D OUTPUT -j DROP 2>/dev/null || sudo iptables -F OUTPUT"
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = process.communicate()
                exit_code = process.returncode
                
                if exit_code == 0:
                    # Also try to bring up interface
                    interface = command.get("interface", "eth0")
                    cmd2 = f"sudo ifup {interface}"
                    process2 = subprocess.Popen(
                        cmd2,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    process2.communicate()  # Ignore result, just try
                    
                    return {
                        "success": True,
                        "output": "Network enabled (iptables rules removed)",
                        "error": None,
                        "exit_code": 0,
                        "metadata": {"method": "iptables"},
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to enable network: {stderr}",
                        "output": None,
                        "exit_code": exit_code,
                    }
            elif system == "Windows":
                # Enable network adapter using netsh
                adapter = command.get("adapter", "*")
                cmd = f'netsh interface set interface "{adapter}" admin=enable'
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = process.communicate()
                exit_code = process.returncode
                
                if exit_code == 0:
                    return {
                        "success": True,
                        "output": f"Network adapter {adapter} enabled",
                        "error": None,
                        "exit_code": 0,
                        "metadata": {"method": "netsh"},
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to enable network: {stderr}",
                        "output": None,
                        "exit_code": exit_code,
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported system: {system}",
                    "output": None,
                    "exit_code": -1,
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Network enable error: {str(e)}",
                "output": None,
                "exit_code": -1,
            }
    
    def handle_list_processes(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        List running processes with details.
        
        Returns:
            Result dict with process list in JSON format
        """
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'cmdline', 'create_time']):
                try:
                    pinfo = proc.info
                    processes.append({
                        "pid": pinfo.get('pid'),
                        "name": pinfo.get('name'),
                        "username": pinfo.get('username'),
                        "cpu_percent": round(pinfo.get('cpu_percent', 0), 2),
                        "memory_percent": round(pinfo.get('memory_percent', 0), 2),
                        "cmdline": ' '.join(pinfo.get('cmdline', []))[:200] if pinfo.get('cmdline') else '',
                        "create_time": pinfo.get('create_time'),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage (descending)
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            import json
            output = json.dumps(processes, indent=2)
            
            return {
                "success": True,
                "output": output,
                "error": None,
                "exit_code": 0,
                "metadata": {
                    "count": len(processes),
                    "processes": processes[:100],  # Limit to top 100 in metadata
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list processes: {str(e)}",
                "output": None,
                "exit_code": -1,
            }
    
    def handle_kill_process(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kill a process by PID.
        
        Args:
            command: Must contain 'process_id' (PID)
        
        Returns:
            Result dict
        """
        process_id = command.get("process_id")
        if not process_id:
            return {
                "success": False,
                "error": "No process_id specified",
                "output": None,
                "exit_code": -1,
            }
        
        try:
            process_id = int(process_id)
            proc = psutil.Process(process_id)
            proc_name = proc.name()
            
            # Try terminate first (graceful)
            proc.terminate()
            try:
                proc.wait(timeout=3)
                method = "terminate"
            except psutil.TimeoutExpired:
                # Force kill if terminate didn't work
                proc.kill()
                proc.wait(timeout=1)
                method = "kill"
            
            return {
                "success": True,
                "output": f"Process {process_id} ({proc_name}) killed using {method}",
                "error": None,
                "exit_code": 0,
                "metadata": {
                    "pid": process_id,
                    "name": proc_name,
                    "method": method,
                },
            }
        except psutil.NoSuchProcess:
            return {
                "success": False,
                "error": f"Process {process_id} not found",
                "output": None,
                "exit_code": -1,
            }
        except psutil.AccessDenied:
            return {
                "success": False,
                "error": f"Permission denied to kill process {process_id}",
                "output": None,
                "exit_code": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to kill process: {str(e)}",
                "output": None,
                "exit_code": -1,
            }
    
    def handle_list_connections(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        List network connections (active TCP/UDP connections).
        
        Returns:
            Result dict with connection list in JSON format
        """
        try:
            connections = []
            for conn in psutil.net_connections(kind='inet'):
                try:
                    conn_info = {
                        "fd": conn.fd,
                        "family": str(conn.family),
                        "type": str(conn.type),
                        "laddr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        "raddr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        "status": conn.status,
                        "pid": conn.pid,
                    }
                    # Try to get process name
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            conn_info["process_name"] = proc.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    connections.append(conn_info)
                except Exception:
                    continue
            
            import json
            output = json.dumps(connections, indent=2)
            
            return {
                "success": True,
                "output": output,
                "error": None,
                "exit_code": 0,
                "metadata": {
                    "count": len(connections),
                    "connections": connections[:200],  # Limit to top 200 in metadata
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list connections: {str(e)}",
                "output": None,
                "exit_code": -1,
            }
    
    def handle_list_files(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        List files in a directory.
        
        Args:
            command: Optional 'directory_path' (default: current directory)
        
        Returns:
            Result dict with file list in JSON format
        """
        try:
            directory_path = command.get("directory_path", ".")
            if not directory_path:
                directory_path = "."
            
            # Resolve path
            if os.path.isabs(directory_path):
                target_path = Path(directory_path)
            else:
                target_path = self.base_path / directory_path.lstrip("/")
            
            if not target_path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {target_path}",
                    "output": None,
                    "exit_code": -1,
                }
            
            if not target_path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {target_path}",
                    "output": None,
                    "exit_code": -1,
                }
            
            files = []
            try:
                for item in target_path.iterdir():
                    try:
                        stat = item.stat()
                        file_info = {
                            "name": item.name,
                            "path": str(item),
                            "type": "directory" if item.is_dir() else "file",
                            "size": stat.st_size if item.is_file() else None,
                            "modified": stat.st_mtime,
                            "permissions": oct(stat.st_mode)[-3:] if hasattr(stat, 'st_mode') else None,
                        }
                        files.append(file_info)
                    except (PermissionError, OSError):
                        # Skip files we can't access
                        continue
            except PermissionError:
                return {
                    "success": False,
                    "error": f"Permission denied: {target_path}",
                    "output": None,
                    "exit_code": -1,
                }
            
            # Sort: directories first, then by name
            files.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            
            import json
            output = json.dumps(files, indent=2)
            
            return {
                "success": True,
                "output": output,
                "error": None,
                "exit_code": 0,
                "metadata": {
                    "directory": str(target_path),
                    "count": len(files),
                    "files": files,
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list files: {str(e)}",
                "output": None,
                "exit_code": -1,
            }
    
    def handle_control_service(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Control system service (start/stop/restart/status).
        
        Args:
            command: Must contain 'service_name' and 'service_action' (start/stop/restart/status)
        
        Returns:
            Result dict
        """
        service_name = command.get("service_name")
        service_action = command.get("service_action", "status").lower()
        
        if not service_name:
            return {
                "success": False,
                "error": "No service_name specified",
                "output": None,
                "exit_code": -1,
            }
        
        if service_action not in ("start", "stop", "restart", "status"):
            return {
                "success": False,
                "error": f"Invalid service_action: {service_action} (must be start/stop/restart/status)",
                "output": None,
                "exit_code": -1,
            }
        
        try:
            system = platform.system()
            if system == "Linux":
                # Use systemctl
                cmd = f"sudo systemctl {service_action} {service_name}"
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = process.communicate()
                exit_code = process.returncode
                
                if exit_code == 0:
                    return {
                        "success": True,
                        "output": stdout or f"Service {service_name} {service_action} completed",
                        "error": None,
                        "exit_code": 0,
                        "metadata": {
                            "service": service_name,
                            "action": service_action,
                            "method": "systemctl",
                        },
                    }
                else:
                    return {
                        "success": False,
                        "error": stderr or f"Failed to {service_action} service {service_name}",
                        "output": stdout,
                        "exit_code": exit_code,
                    }
            elif system == "Windows":
                # Use sc or net commands
                if service_action == "status":
                    cmd = f'sc query "{service_name}"'
                elif service_action == "start":
                    cmd = f'net start "{service_name}"'
                elif service_action == "stop":
                    cmd = f'net stop "{service_name}"'
                elif service_action == "restart":
                    # Windows doesn't have direct restart, so stop then start
                    cmd = f'net stop "{service_name}" && net start "{service_name}"'
                else:
                    cmd = f'sc query "{service_name}"'
                
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = process.communicate()
                exit_code = process.returncode
                
                if exit_code == 0:
                    return {
                        "success": True,
                        "output": stdout or f"Service {service_name} {service_action} completed",
                        "error": None,
                        "exit_code": 0,
                        "metadata": {
                            "service": service_name,
                            "action": service_action,
                            "method": "net/sc",
                        },
                    }
                else:
                    return {
                        "success": False,
                        "error": stderr or f"Failed to {service_action} service {service_name}",
                        "output": stdout,
                        "exit_code": exit_code,
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported system: {system}",
                    "output": None,
                    "exit_code": -1,
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Service control error: {str(e)}",
                "output": None,
                "exit_code": -1,
            }

