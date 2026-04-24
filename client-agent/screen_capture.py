#!/usr/bin/env python3
"""
screen_capture.py

Screen capture service for remote desktop viewing.
Uses mss for fast screen capture and PIL for image processing.
"""

from __future__ import annotations

import base64
import io
import time
from typing import Optional, Tuple

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from PIL import ImageGrab
    HAS_IMAGEGRAB = True
except ImportError:
    HAS_IMAGEGRAB = False


class ScreenCapture:
    """Capture screen and convert to base64 or bytes."""
    
    def __init__(self):
        self._mss_instance = None
        self._has_display = self._check_display()
        self._mss_available = False
        
        if HAS_MSS and self._has_display:
            try:
                # Try to initialize mss - but don't fail if it doesn't work
                self._mss_instance = mss.mss()
                # Test if mss actually works by trying to get monitors
                try:
                    _ = self._mss_instance.monitors
                    self._mss_available = True
                except Exception:
                    self._mss_instance = None
                    self._mss_available = False
            except Exception:
                self._mss_instance = None
                self._mss_available = False
    
    def _check_display(self) -> bool:
        """Check if X display is available (Linux/Unix)."""
        import os
        import platform
        
        # On Windows, always assume display is available
        if platform.system() == "Windows":
            return True
        
        # On Linux/Unix, check DISPLAY environment variable
        display = os.environ.get("DISPLAY")
        if not display:
            return False
        
        # Try to check if X server is actually running
        try:
            import subprocess
            result = subprocess.run(
                ["xdpyinfo"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            # xdpyinfo not available or timeout - assume display might be available
            return display is not None
    
    def capture_screen(self, quality: int = 70, max_width: Optional[int] = 1920, max_height: Optional[int] = 1080) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Capture current screen.
        
        Args:
            quality: JPEG quality (1-100)
            max_width: Max width to resize (None = no resize)
            max_height: Max height to resize (None = no resize)
        
        Returns:
            (image_bytes, error_message)
        """
        if not self._has_display:
            return None, "No display available (headless environment or DISPLAY not set)"
        
        try:
            # Try mss first (fastest) - but only if it's actually available
            if self._mss_available and self._mss_instance:
                try:
                    screenshot = self._mss_instance.grab(self._mss_instance.monitors[1])  # Primary monitor
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                except Exception as mss_error:
                    # mss failed, mark as unavailable and try PIL ImageGrab
                    self._mss_available = False
                    self._mss_instance = None
                    if HAS_IMAGEGRAB:
                        try:
                            img = ImageGrab.grab()
                        except Exception as pil_error:
                            # Try scrot as last resort
                            if self._try_scrot():
                                img_bytes, error = self._capture_with_scrot()
                                if img_bytes:
                                    try:
                                        img = Image.open(io.BytesIO(img_bytes))
                                    except Exception as scrot_error:
                                        return None, f"Screen capture failed: mss={str(mss_error)}, PIL={str(pil_error)}, scrot={str(scrot_error)}"
                                else:
                                    return None, f"Screen capture failed: mss={str(mss_error)}, PIL={str(pil_error)}, scrot={error}"
                            else:
                                return None, f"Screen capture failed: mss={str(mss_error)}, PIL={str(pil_error)}"
                    elif self._try_scrot():
                        # Try scrot if PIL ImageGrab not available
                        img_bytes, error = self._capture_with_scrot()
                        if img_bytes:
                            try:
                                img = Image.open(io.BytesIO(img_bytes))
                            except Exception as scrot_error:
                                return None, f"mss failed: {str(mss_error)}, scrot load failed: {str(scrot_error)}"
                        else:
                            return None, f"mss failed: {str(mss_error)}, scrot failed: {error}"
                    else:
                        return None, f"mss failed: {str(mss_error)}"
            elif HAS_IMAGEGRAB:
                # Fallback to PIL ImageGrab
                try:
                    img = ImageGrab.grab()
                except Exception as e:
                    return None, f"PIL ImageGrab failed: {str(e)}"
            elif self._try_scrot():
                # Try scrot command line tool as last resort
                img_bytes, error = self._capture_with_scrot()
                if img_bytes:
                    try:
                        img = Image.open(io.BytesIO(img_bytes))
                    except Exception as e:
                        return None, f"Failed to load scrot image: {str(e)}"
                else:
                    return None, error or "scrot capture failed"
            else:
                return None, "No screen capture library available (install mss, Pillow with ImageGrab, or scrot)"
            
            # Resize if needed
            if max_width or max_height:
                img.thumbnail((max_width or 9999, max_height or 9999), Image.Resampling.LANCZOS)
            
            # Convert to JPEG bytes
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            return buffer.getvalue(), None
            
        except Exception as e:
            return None, f"Screen capture error: {str(e)}"
    
    def capture_screen_base64(self, quality: int = 70, max_width: Optional[int] = 1920, max_height: Optional[int] = 1080) -> Tuple[Optional[str], Optional[str]]:
        """
        Capture screen and return as base64 string.
        
        Returns:
            (base64_string, error_message)
        """
        img_bytes, error = self.capture_screen(quality, max_width, max_height)
        if error:
            return None, error
        
        if img_bytes:
            return base64.b64encode(img_bytes).decode('utf-8'), None
        return None, "Failed to capture screen"
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get primary screen size."""
        try:
            if self._mss_available and self._mss_instance:
                try:
                    monitor = self._mss_instance.monitors[1]
                    return monitor['width'], monitor['height']
                except Exception:
                    # mss failed, try PIL
                    if HAS_PIL:
                        try:
                            img = Image.grab()
                            return img.size
                        except Exception:
                            pass
            elif HAS_IMAGEGRAB:
                try:
                    img = ImageGrab.grab()
                    return img.size
                except Exception:
                    pass
            return 1920, 1080  # Default
        except Exception:
            return 1920, 1080  # Default
    
    def _try_scrot(self) -> bool:
        """Check if scrot command is available."""
        try:
            import subprocess
            result = subprocess.run(
                ["which", "scrot"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _capture_with_scrot(self) -> Tuple[Optional[bytes], Optional[str]]:
        """Capture screen using scrot command line tool."""
        try:
            import subprocess
            import tempfile
            import os
            
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                # Run scrot
                result = subprocess.run(
                    ["scrot", "-q", "100", tmp_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else "Unknown error"
                    return None, f"scrot failed: {error_msg}"
                
                # Read image file
                if os.path.exists(tmp_path):
                    with open(tmp_path, 'rb') as f:
                        img_data = f.read()
                    os.unlink(tmp_path)
                    return img_data, None
                else:
                    return None, "scrot did not create output file"
                    
            except subprocess.TimeoutExpired:
                return None, "scrot timeout"
            except Exception as e:
                return None, f"scrot error: {str(e)}"
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                        
        except Exception as e:
            return None, f"scrot capture error: {str(e)}"

