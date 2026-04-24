#!/usr/bin/env python3
"""
vnc_manager.py

VNC server manager for remote desktop access.
Supports TigerVNC, TightVNC, and x11vnc on Linux.
On Windows, uses TightVNC Server.
"""

from __future__ import annotations

import os
import platform
import subprocess
import socket
import time
from typing import Optional, Dict, Any, Tuple

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class VNCManager:
    """Manage VNC server for remote desktop access."""
    
    def __init__(self):
        self._vnc_process: Optional[subprocess.Popen] = None
        self._vnc_port: int = 5900
        self._vnc_display: int = 1
        self._system = platform.system()
    
    def _find_vnc_command(self) -> Optional[str]:
        """Find available VNC server command."""
        commands = []
        
        if self._system == "Windows":
            # Windows: Try TightVNC Server
            commands = [
                "tvnserver.exe",
                r"C:\Program Files\TightVNC\tvnserver.exe",
                r"C:\Program Files (x86)\TightVNC\tvnserver.exe",
            ]
        else:
            # Linux/Unix: Try various VNC servers
            commands = [
                "x11vnc",
                "tigervncserver",
                "vncserver",
                "Xvnc",
            ]
        
        for cmd in commands:
            try:
                if self._system == "Windows":
                    # On Windows, check if file exists
                    if os.path.exists(cmd) or self._command_exists(cmd):
                        return cmd
                else:
                    # On Linux, use which
                    result = subprocess.run(
                        ["which", cmd],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=1
                    )
                    if result.returncode == 0:
                        return cmd
            except Exception:
                continue
        
        return None
    
    def _command_exists(self, cmd: str) -> bool:
        """Check if command exists (Windows)."""
        try:
            subprocess.run(
                [cmd, "-help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1
            )
            return True
        except Exception:
            return False
    
    def _find_free_port(self, start_port: int = 5900) -> int:
        """Find a free port starting from start_port."""
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        return start_port  # Fallback
    
    def start_vnc_server(self, password: str = "", port: Optional[int] = None, display: Optional[int] = None) -> Dict[str, Any]:
        """
        Start VNC server.
        
        Args:
            password: VNC password (if empty, will be generated or use default)
            port: VNC port (default: auto-detect free port starting from 5900)
            display: Display number for Linux (default: 1)
        
        Returns:
            Dict with success, port, password, error
        """
        if self._vnc_process and self._vnc_process.poll() is None:
            return {
                "success": True,
                "port": self._vnc_port,
                "display": self._vnc_display,
                "message": "VNC server already running",
            }
        
        vnc_cmd = self._find_vnc_command()
        if not vnc_cmd:
            return {
                "success": False,
                "error": "No VNC server found. Please install TigerVNC, TightVNC, or x11vnc.",
                "hint_linux": "Install with: sudo apt-get install tigervnc-standalone-server tigervnc-common",
                "hint_windows": "Install TightVNC Server from https://www.tightvnc.com/",
            }
        
        try:
            if self._system == "Windows":
                # Windows: TightVNC Server
                if port is None:
                    port = self._find_free_port(5900)
                self._vnc_port = port
                
                # Set password if provided
                if password:
                    # TightVNC stores password in registry, need to set it
                    # For now, just start server and return info
                    pass
                
                # Start TightVNC Server
                # Note: TightVNC Server usually runs as service, but we can try to start it
                cmd = [vnc_cmd, "-controlapp", "-start"]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                
                # Wait a bit to see if it starts
                time.sleep(2)
                if process.poll() is None or process.returncode == 0:
                    self._vnc_process = process
                    return {
                        "success": True,
                        "port": port,
                        "display": 0,
                        "password": password or "Set in TightVNC Server settings",
                        "message": "VNC server started",
                    }
                else:
                    stdout, stderr = process.communicate()
                    return {
                        "success": False,
                        "error": f"Failed to start VNC server: {stderr.decode('utf-8', errors='ignore')}",
                    }
            else:
                # Linux: x11vnc or TigerVNC
                if display is None:
                    display = 1
                self._vnc_display = display
                
                if port is None:
                    port = 5900 + display
                self._vnc_port = port
                
                # Check if display is available
                display_env = os.environ.get("DISPLAY")
                if not display_env:
                    return {
                        "success": False,
                        "error": "No DISPLAY environment variable set. Cannot start VNC server.",
                        "hint": "Set DISPLAY with: export DISPLAY=:0",
                    }
                
                # Kill any existing x11vnc process before starting to avoid
                # "Address already in use" and half-dead VNC states
                try:
                    if HAS_PSUTIL:
                        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                            try:
                                cmdline = ' '.join(proc.info['cmdline'] or [])
                                if 'x11vnc' in cmdline:
                                    print(f"Killing existing x11vnc process: PID {proc.info['pid']}")
                                    proc.kill()
                                    time.sleep(0.5)  # Wait a bit for process to die
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                    else:
                        # Fallback: try to kill using pkill or killall
                        try:
                            subprocess.run(["pkill", "x11vnc"], 
                                         stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL, 
                                         timeout=2)
                        except:
                            pass
                except Exception as e:
                    print(f"Warning: Could not kill existing x11vnc processes: {e}")
                
                if "x11vnc" in vnc_cmd:
                    # x11vnc - shares existing X display
                    # Note: x11vnc by default listens on all interfaces (0.0.0.0) unless restricted
                    # We don't need to specify -bind or -listen as it's the default behavior
                    cmd = [
                        "x11vnc",
                        "-display", display_env,
                        "-rfbport", str(port),
                        "-forever",
                        "-shared",
                        "-noxdamage",
                        "-noxfixes",
                    ]
                    # Add password option only if password is provided
                    if password:
                        cmd.extend(["-passwd", password])
                    else:
                        cmd.append("-nopw")
                else:
                    # TigerVNC or vncserver - creates new virtual display
                    # This is more complex, so prefer x11vnc
                    return {
                        "success": False,
                        "error": f"VNC server '{vnc_cmd}' requires manual setup. Please use x11vnc instead.",
                        "hint": "Install x11vnc: sudo apt-get install x11vnc",
                    }
                
                # Start process with stdout discarded and stderr logged to file
                # to avoid PIPE buffers filling up and to allow debugging.
                log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x11vnc_agent.log")
                # Open in append-binary, unbuffered
                log_file = open(log_path, "ab", buffering=0)
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=log_file,
                    # Don't wait for process - let it run in background
                )
                
                # Wait a bit to check if it started
                time.sleep(2)  # Give it more time to start
                
                # Check if process is still running (None means still running)
                if process.poll() is None:
                    # Process is running - verify port is actually listening
                    try:
                        # Try to connect to port to verify it's listening
                        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        test_socket.settimeout(1)
                        result_connect = test_socket.connect_ex(('127.0.0.1', port))
                        test_socket.close()
                        
                        if result_connect == 0:
                            # Port is listening - success!
                            self._vnc_process = process
                            return {
                                "success": True,
                                "port": port,
                                "display": display,
                                "password": password or "No password set",
                                "message": "VNC server started",
                            }
                        else:
                            # Process running but port not listening yet - wait a bit more
                            time.sleep(1)
                            if process.poll() is None:
                                # Still running, assume it's starting up
                                self._vnc_process = process
                                return {
                                    "success": True,
                                    "port": port,
                                    "display": display,
                                    "password": password or "No password set",
                                    "message": "VNC server started (verifying)",
                                }
                    except Exception as e:
                        # Socket check failed, but process is running - assume success
                        if process.poll() is None:
                            self._vnc_process = process
                            return {
                                "success": True,
                                "port": port,
                                "display": display,
                                "password": password or "No password set",
                                "message": "VNC server started",
                            }
                
                # Process exited - check error
                stdout, stderr = process.communicate()
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else stdout.decode('utf-8', errors='ignore')
                
                # Check if port is actually listening (maybe process forked and parent exited)
                try:
                    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    test_socket.settimeout(1)
                    result_connect = test_socket.connect_ex(('127.0.0.1', port))
                    test_socket.close()
                    
                    if result_connect == 0:
                        # Port is listening even though process exited - might have forked
                        # Try to find the actual process
                        if HAS_PSUTIL:
                            try:
                                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                                    try:
                                        cmdline = ' '.join(proc.info['cmdline'] or [])
                                        if 'x11vnc' in cmdline and str(port) in cmdline:
                                            # Found x11vnc process with our port
                                            self._vnc_process = None  # Can't track forked process
                                            return {
                                                "success": True,
                                                "port": port,
                                                "display": display,
                                                "password": password or "No password set",
                                                "message": "VNC server started",
                                            }
                                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                                        continue
                            except Exception:
                                pass
                        
                        # Port is listening, assume success even if we can't find process
                        self._vnc_process = None
                        return {
                            "success": True,
                            "port": port,
                            "display": display,
                            "password": password or "No password set",
                            "message": "VNC server started (port verified)",
                        }
                except Exception:
                    pass
                
                return {
                    "success": False,
                    "error": f"Failed to start VNC server: {error_msg[:500] if error_msg else 'Process exited'}",
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"VNC server error: {str(e)}",
            }
    
    def stop_vnc_server(self) -> Dict[str, Any]:
        """Stop VNC server."""
        if not self._vnc_process:
            return {"success": False, "error": "VNC server not running"}
        
        try:
            if self._system == "Windows":
                # Windows: Stop TightVNC Server
                subprocess.run(
                    ["tvnserver.exe", "-controlapp", "-stop"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                )
            else:
                # Linux: Kill x11vnc process
                self._vnc_process.terminate()
                try:
                    self._vnc_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._vnc_process.kill()
            
            self._vnc_process = None
            return {"success": True, "message": "VNC server stopped"}
        except Exception as e:
            return {"success": False, "error": f"Failed to stop VNC server: {str(e)}"}
    
    def get_vnc_info(self) -> Dict[str, Any]:
        """Get current VNC server info."""
        if self._vnc_process and self._vnc_process.poll() is None:
            return {
                "running": True,
                "port": self._vnc_port,
                "display": self._vnc_display,
            }
        return {"running": False}

