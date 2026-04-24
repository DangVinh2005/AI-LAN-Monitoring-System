#!/usr/bin/env python3
# ui.py — PySide6 UI for Agent Client
from __future__ import annotations

import os
import sys
import time
from typing import Optional, Callable, List, Dict, Any

from PySide6 import QtCore, QtGui, QtWidgets

# Import your logic (api.py must be alongside)
from api import ApiClient, AgentRunner

# Config (assets via constants — no hard-coded inline paths)
ICON_CONNECT = "./icons/connect.svg"
ICON_START = "./icons/play.svg"
ICON_STOP = "./icons/stop.svg"
ICON_ACCEPT = "./icons/accept.svg"
ICON_MINIMIZE = "./icons/minimize.svg"
ICON_CLOSE = "./icons/close.svg"
ICON_APP = "./icons/app.svg"

HEALTH_INTERVAL = 10.0
LOG_MAX_LINES = 20000

# Speech bubble settings
SPEECH_DURATION_MS = 2600
SPEECH_THROTTLE_MS = 1000  # min gap between speech events


# ---------------------------
# Floating Pet Window (frameless, draggable) - DISABLED for academic project
# ---------------------------
class PetWindow(QtWidgets.QWidget):
    """Pet window feature disabled for academic project.
    This class is kept for compatibility but functionality is disabled.
    """

    def __init__(self, click_callback: Optional[Callable[[], None]] = None, parent=None):
        super().__init__(parent)
        self.click_callback = click_callback
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.Tool  # doesn't show in taskbar
        )
        # transparent background
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # Main label for graphic (supports QMovie or QPixmap)
        self.label = QtWidgets.QLabel(self)
        self.label.setScaledContents(True)

        # Speech bubble label (small)
        self.speech = QtWidgets.QLabel(self)
        self.speech.setVisible(False)
        self.speech.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # Cyberpunk neon speech bubble
        self.speech.setStyleSheet(
            """
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 255, 255, 200),
                    stop:1 rgba(0, 200, 255, 220));
                color: #0a0a1a;
                border: 2px solid rgba(0, 255, 255, 255);
                border-radius: 10px;
                padding: 8px 10px;
                font-size: 12px;
                font-weight: 600;
            }
            """
        )
        self.speech.setWordWrap(True)
        self.speech.setMaximumWidth(240)

        self._movie: Optional[QtGui.QMovie] = None
        self._load_media()

        # default size and position
        pix = self._current_pixmap()
        size = pix.size() if pix else QtCore.QSize(300, 480)
        self.label.resize(size)
        self.resize(size)
        self._drag_offset = None

        # bobbing animation using QPropertyAnimation
        self.label.move(0, 0)
        self._bob_anim = QtCore.QPropertyAnimation(self.label, b"pos", self)
        self._bob_anim.setStartValue(QtCore.QPoint(0, -6))
        self._bob_anim.setEndValue(QtCore.QPoint(0, 6))
        self._bob_anim.setDuration(1400)
        self._bob_anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutSine)
        self._bob_anim.finished.connect(self._toggle_bob_direction)
        self._bob_anim.start()

        # Keep track of last speech time for throttle
        self._last_speech_ts = 0.0

    def _current_pixmap(self) -> Optional[QtGui.QPixmap]:
        # Feature disabled - return None
        return None

    def _load_media(self) -> None:
        # Feature disabled - create empty placeholder
        s = QtCore.QSize(300, 450)
        pix = QtGui.QPixmap(s)
        pix.fill(QtCore.Qt.GlobalColor.transparent)
        self.label.setPixmap(pix)
        self.label.setFixedSize(pix.size())

        # position speech bubble initially
        self._position_speech()

    def _position_speech(self) -> None:
        # Place speech above label, shifted left a bit
        w = self.label.width()
        bubble_w = min(240, int(w * 0.8))
        self.speech.setFixedWidth(bubble_w)
        # target: above top-left of label
        bx = max(0, (w - bubble_w) - 10)
        by = -self.speech.height() - 10
        self.speech.move(bx, by)

    def show_speech(self, text: str) -> None:
        now = time.time() * 1000
        if now - self._last_speech_ts < SPEECH_THROTTLE_MS:
            return
        self._last_speech_ts = now
        self.speech.setText(text)
        self.speech.adjustSize()
        # reposition based on current label size
        self._position_speech()
        self.speech.show()
        QtCore.QTimer.singleShot(SPEECH_DURATION_MS, self.speech.hide)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_offset = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._drag_offset is not None:
            new_pos = self.mapToGlobal(event.pos() - self._drag_offset)
            self.move(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # click if little movement
            if self._drag_offset and (event.pos() - self._drag_offset).manhattanLength() < 6:
                if self.click_callback:
                    QtCore.QTimer.singleShot(0, self.click_callback)
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def _toggle_bob_direction(self) -> None:
        # ping-pong effect
        if self._bob_anim.startValue().y() < self._bob_anim.endValue().y():
            self._bob_anim.setStartValue(QtCore.QPoint(0, 6))
            self._bob_anim.setEndValue(QtCore.QPoint(0, -6))
        else:
            self._bob_anim.setStartValue(QtCore.QPoint(0, -6))
            self._bob_anim.setEndValue(QtCore.QPoint(0, 6))
        self._bob_anim.start()
        # keep speech positioned relative to label while animating
        self._position_speech()


# ---------------------------
# Helper UI components
# ---------------------------
class GlassFrame(QtWidgets.QFrame):
    """Rounded frame with subtle translucent background and drop shadow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassFrame")
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        effect = QtWidgets.QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(36)
        effect.setOffset(0, 14)
        effect.setColor(QtGui.QColor(0, 0, 0, 160))
        self.setGraphicsEffect(effect)
        # Cyberpunk gradient background với độ đậm cao hơn
        self.setStyleSheet(
            """
            #GlassFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(20, 10, 40, 245),
                    stop:0.5 rgba(15, 5, 35, 250),
                    stop:1 rgba(10, 0, 30, 255));
                border: 2px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 255, 255, 120),
                    stop:0.5 rgba(255, 0, 255, 120),
                    stop:1 rgba(0, 255, 255, 120));
                border-radius: 16px;
            }
            """
        )


class HeaderBar(QtWidgets.QWidget):
    """Custom header bar for dragging and window controls."""

    def __init__(self, title: str = "Agent Client", parent=None):
        super().__init__(parent)
        self._drag_pos: Optional[QtCore.QPoint] = None

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self.icon_label = QtWidgets.QLabel()
        if os.path.exists(ICON_APP):
            self.icon_label.setPixmap(QtGui.QPixmap(ICON_APP).scaled(20, 20, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.icon_label)

        self.title_label = QtWidgets.QLabel(title)
        # Cyberpunk neon title
        self.title_label.setStyleSheet(
            """
            QLabel {
                color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ffff,
                    stop:0.5 #ff00ff,
                    stop:1 #00ffff);
                font-weight: 700;
                font-size: 14px;
            }
            """
        )
        layout.addWidget(self.title_label)

        layout.addStretch(1)

        self.min_btn = QtWidgets.QToolButton()
        self.min_btn.setIcon(QtGui.QIcon(ICON_MINIMIZE) if os.path.exists(ICON_MINIMIZE) else self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarMinButton))
        self.min_btn.setIconSize(QtCore.QSize(16, 16))
        self.min_btn.setStyleSheet(
            """
            QToolButton {
                border: 1px solid rgba(0, 255, 255, 80);
                padding: 6px;
                border-radius: 8px;
                background: rgba(0, 20, 40, 150);
            }
            QToolButton:hover {
                background: rgba(0, 255, 255, 100);
                border: 1px solid rgba(0, 255, 255, 255);
            }
            """
        )
        self.min_btn.clicked.connect(self._on_minimize)
        layout.addWidget(self.min_btn)

        self.close_btn = QtWidgets.QToolButton()
        self.close_btn.setIcon(QtGui.QIcon(ICON_CLOSE) if os.path.exists(ICON_CLOSE) else self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarCloseButton))
        self.close_btn.setIconSize(QtCore.QSize(16, 16))
        self.close_btn.setStyleSheet(
            """
            QToolButton {
                border: 1px solid rgba(255, 0, 100, 100);
                padding: 6px;
                border-radius: 8px;
                background: rgba(40, 0, 10, 150);
            }
            QToolButton:hover {
                background: rgba(255, 0, 100, 150);
                border: 1px solid rgba(255, 0, 100, 255);
            }
            """
        )
        self.close_btn.clicked.connect(self._on_close)
        layout.addWidget(self.close_btn)

        self.setFixedHeight(40)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._win_pos = self.window().frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.window().move(self._win_pos + delta)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _on_minimize(self) -> None:
        self.window().showMinimized()

    def _on_close(self) -> None:
        self.window().close()


class AuthScreen(QtWidgets.QWidget):
    """Login/Register screen using internal stacked forms."""

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(12)

        # Toggle buttons
        toggle_row = QtWidgets.QHBoxLayout()
        self.login_toggle = QtWidgets.QPushButton("Đăng nhập")
        self.register_toggle = QtWidgets.QPushButton("Đăng ký")
        for b in (self.login_toggle, self.register_toggle):
            b.setCheckable(True)
            b.setMinimumHeight(36)
        self.login_toggle.setChecked(True)
        toggle_row.addWidget(self.login_toggle)
        toggle_row.addWidget(self.register_toggle)
        outer.addLayout(toggle_row)

        # Forms stacked
        self.stack = QtWidgets.QStackedWidget()
        outer.addWidget(self.stack, 1)

        # Login form
        login_w = QtWidgets.QWidget()
        login_form = QtWidgets.QFormLayout(login_w)
        login_form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop)
        self.login_user = QtWidgets.QLineEdit()
        self.login_pass = QtWidgets.QLineEdit()
        self.login_pass.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.login_btn = QtWidgets.QPushButton("Đăng nhập")
        login_form.addRow("Username:", self.login_user)
        login_form.addRow("Password:", self.login_pass)
        login_form.addRow(self.login_btn)

        # Register form
        reg_w = QtWidgets.QWidget()
        reg_form = QtWidgets.QFormLayout(reg_w)
        reg_form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop)
        self.reg_email = QtWidgets.QLineEdit()
        self.reg_pass = QtWidgets.QLineEdit()
        self.reg_pass.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.reg_btn = QtWidgets.QPushButton("Đăng ký")
        reg_form.addRow("Email:", self.reg_email)
        reg_form.addRow("Password:", self.reg_pass)
        reg_form.addRow(self.reg_btn)

        self.stack.addWidget(login_w)
        self.stack.addWidget(reg_w)

        self.login_toggle.clicked.connect(lambda: self._set_mode(0))
        self.register_toggle.clicked.connect(lambda: self._set_mode(1))

    def _set_mode(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.login_toggle.setChecked(index == 0)
        self.register_toggle.setChecked(index == 1)


class ConnectScreen(QtWidgets.QWidget):
    """Initial screen to connect to server before authentication."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        title = QtWidgets.QLabel("Kết nối Server")
        title.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: 700;
                color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ffff,
                    stop:0.5 #ff00ff,
                    stop:1 #00ffff);
            }
            """
        )
        lay.addWidget(title)

        row = QtWidgets.QHBoxLayout()
        self.server_edit = QtWidgets.QLineEdit("http://127.0.0.1:8000")
        self.server_edit.setPlaceholderText("Server URL")
        self.connect_btn = QtWidgets.QPushButton(" Kết nối")
        self.connect_btn.setIcon(QtGui.QIcon(ICON_CONNECT) if os.path.exists(ICON_CONNECT) else self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload))
        self.connect_btn.setIconSize(QtCore.QSize(18, 18))
        self.connect_btn.setMinimumHeight(36)
        row.addWidget(self.server_edit, 1)
        row.addWidget(self.connect_btn)
        lay.addLayout(row)

        self.status_label = QtWidgets.QLabel("🔌 Server: - | 🟡 Unknown")
        self.status_label.setStyleSheet("QLabel{ color: #00ffff; font-weight: 600; }")
        lay.addWidget(self.status_label)

        hint = QtWidgets.QLabel("Vui lòng kết nối server trước khi đăng nhập/đăng ký.")
        hint.setStyleSheet("QLabel{ color: rgba(0, 255, 255, 150); font-size: 12px; }")
        lay.addWidget(hint)

        lay.addStretch(1)


class MainScreen(QtWidgets.QWidget):
    """Main control screen with server connect, agent controls, and logs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(20, 12, 20, 20)
        main.setSpacing(10)

        # Server row
        srow = QtWidgets.QHBoxLayout()
        self.server_edit = QtWidgets.QLineEdit("http://127.0.0.1:8000")
        self.server_edit.setPlaceholderText("Server URL")
        self.connect_btn = QtWidgets.QPushButton(" Kết nối")
        self.connect_btn.setIcon(QtGui.QIcon(ICON_CONNECT) if os.path.exists(ICON_CONNECT) else self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload))
        self.connect_btn.setIconSize(QtCore.QSize(18, 18))
        self.connect_btn.setMinimumHeight(36)
        srow.addWidget(self.server_edit, 1)
        srow.addWidget(self.connect_btn)
        main.addLayout(srow)

        # Status line
        self.status_label = QtWidgets.QLabel("🔌 Server: - | 🟡 Unknown")
        self.status_label.setStyleSheet("QLabel{ color: #00ffff; font-weight: 600; }")
        main.addWidget(self.status_label)
        
        # Agent status info (uptime, last heartbeat, last metrics)
        info_frame = QtWidgets.QFrame()
        info_frame.setObjectName("InfoFrame")
        info_layout = QtWidgets.QHBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 4, 8, 4)
        info_layout.setSpacing(12)
        
        self.uptime_label = QtWidgets.QLabel("⏱ Uptime: -")
        self.heartbeat_label = QtWidgets.QLabel("💓 Last heartbeat: -")
        self.metrics_label = QtWidgets.QLabel("📊 Last metrics: -")
        
        for lbl in (self.uptime_label, self.heartbeat_label, self.metrics_label):
            lbl.setStyleSheet("QLabel{ color: rgba(0, 255, 255, 180); font-size: 11px; }")
            info_layout.addWidget(lbl)
        
        info_layout.addStretch(1)
        main.addWidget(info_frame)

        # Controls row
        crow = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton(" Start Agent")
        self.start_btn.setIcon(QtGui.QIcon(ICON_START) if os.path.exists(ICON_START) else self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
        self.start_btn.setIconSize(QtCore.QSize(18, 18))
        self.start_btn.setMinimumHeight(36)

        self.stop_btn = QtWidgets.QPushButton(" Stop Agent")
        self.stop_btn.setIcon(QtGui.QIcon(ICON_STOP) if os.path.exists(ICON_STOP) else self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaStop))
        self.stop_btn.setIconSize(QtCore.QSize(18, 18))
        self.stop_btn.setMinimumHeight(36)
        self.stop_btn.setEnabled(False)

        self.accept_btn = QtWidgets.QPushButton(" Accept Control")
        self.accept_btn.setIcon(QtGui.QIcon(ICON_ACCEPT) if os.path.exists(ICON_ACCEPT) else self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogYesButton))
        self.accept_btn.setIconSize(QtCore.QSize(18, 18))
        self.accept_btn.setMinimumHeight(36)
        self.accept_btn.setObjectName("secondary")

        # Spam test controls (cho phép tùy chỉnh số request và CPM gửi lên server)
        self.spam_btn = QtWidgets.QPushButton(" Spam Test (AI Block)")
        self.spam_btn.setMinimumHeight(36)
        self.spam_btn.setObjectName("secondary")
        self.spam_count_spin = QtWidgets.QSpinBox()
        self.spam_count_spin.setRange(1, 2000)
        self.spam_count_spin.setValue(100)
        self.spam_count_spin.setPrefix("Count: ")
        self.spam_cpm_spin = QtWidgets.QSpinBox()
        self.spam_cpm_spin.setRange(0, 10000)
        self.spam_cpm_spin.setValue(1200)
        self.spam_cpm_spin.setPrefix("CPM: ")

        # Auto metrics disabled - metrics only sent when server requests via "request_metrics" action
        # Keep checkbox for backward compatibility but it's disabled by default
        self.auto_metrics_chk = QtWidgets.QCheckBox("Auto metrics (disabled - use server request)")
        self.auto_metrics_chk.setChecked(False)
        self.auto_metrics_chk.setEnabled(False)  # Disable checkbox - metrics only on server request

        crow.addWidget(self.start_btn)
        crow.addWidget(self.stop_btn)
        crow.addWidget(self.accept_btn)
        crow.addWidget(self.spam_btn)
        crow.addWidget(self.spam_count_spin)
        crow.addWidget(self.spam_cpm_spin)
        crow.addWidget(self.auto_metrics_chk)
        crow.addStretch(1)
        main.addLayout(crow)

        # Logged in as + Profile section
        profile_row = QtWidgets.QHBoxLayout()
        self.logged_in_label = QtWidgets.QLabel("Not logged in")
        self.logged_in_label.setStyleSheet("QLabel{ color: rgba(255, 0, 255, 200); font-weight: 600; }")
        profile_row.addWidget(self.logged_in_label)
        profile_row.addStretch(1)
        
        # Profile edit button
        self.profile_btn = QtWidgets.QPushButton(" Edit Profile")
        self.profile_btn.setObjectName("secondary")
        self.profile_btn.setMinimumHeight(32)
        profile_row.addWidget(self.profile_btn)
        main.addLayout(profile_row)

        # Logs group (rounded, subtle background)
        logs_box = QtWidgets.QFrame()
        logs_box.setObjectName("LogsBox")
        logs_layout = QtWidgets.QVBoxLayout(logs_box)
        logs_layout.setContentsMargins(10, 10, 10, 10)
        logs_layout.setSpacing(6)
        logs_title = QtWidgets.QLabel("Logs / Activity")
        logs_layout.addWidget(logs_title)
        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(LOG_MAX_LINES)
        logs_layout.addWidget(self.log_view)
        main.addWidget(logs_box, 2)

        # Bottom row
        brow = QtWidgets.QHBoxLayout()
        # Pet feature removed for academic project
        brow.addStretch(1)
        self.app_status = QtWidgets.QLabel("Ready")
        self.app_status.setStyleSheet("QLabel{ color: #00ffff; font-weight: 600; }")
        brow.addWidget(self.app_status)
        main.addLayout(brow)

        # Cyberpunk neon logs container
        self.setStyleSheet(
            """
            #LogsBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 10, 30, 220),
                    stop:1 rgba(0, 5, 20, 240));
                border: 2px solid rgba(0, 255, 255, 120);
                border-radius: 12px;
            }
            QPlainTextEdit {
                background: rgba(0, 0, 0, 180);
                border: 1px solid rgba(0, 255, 255, 80);
                border-radius: 8px;
                color: #00ffff;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }
            QLabel {
                color: #00ffff;
                font-weight: 600;
            }
            """
        )


# ---------------------------
# Health worker thread (QThread)
# ---------------------------
class HealthWorker(QtCore.QThread):
    health = QtCore.Signal(bool, str)
    log = QtCore.Signal(str)

    def __init__(self, api_client: ApiClient, interval: float = HEALTH_INTERVAL):
        super().__init__()
        self.api = api_client
        self.interval = interval
        self._running = True

    def run(self) -> None:
        self.log.emit("Health monitor started.")
        while self._running and not self.isInterruptionRequested():
            if not getattr(self.api, "base_url", None):
                self.health.emit(False, "no-url")
                self.log.emit("No server URL set.")
            else:
                try:
                    ok, msg = self.api.health()
                    self.health.emit(bool(ok), str(msg))
                    # Only log health if message is meaningful (not "None" or empty)
                    if msg and str(msg).lower() not in ("none", "null", ""):
                        self.log.emit(f"Health: {'Online' if ok else 'Offline'} ({msg})")
                    elif ok:
                        # Just log "Online" without message if it's None, but throttle it
                        if not hasattr(self, '_last_health_log_ts') or (time.time() - getattr(self, '_last_health_log_ts', 0)) >= 30.0:
                            self.log.emit("Health: Online")
                            self._last_health_log_ts = time.time()
                except Exception as e:
                    self.health.emit(False, f"error:{e}")
                    self.log.emit(f"Health error: {e!r}")
            # sleep in small steps so we can be responsive to stop
            slept = 0.0
            step = 0.25
            while self._running and not self.isInterruptionRequested() and slept < self.interval:
                self.msleep(int(step * 1000))
                slept += step
        self.log.emit("Health monitor stopped.")

    def stop(self) -> None:
        self._running = False
        self.requestInterruption()


# ---------------------------
# One-off Task Worker (QThread)
# ---------------------------
class TaskWorker(QtCore.QThread):
    finished = QtCore.Signal(bool, str)
    log = QtCore.Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            ok, msg = self._fn(*self._args, **self._kwargs)
            self.log.emit(f"Task done: {msg}")
            self.finished.emit(bool(ok), str(msg))
        except Exception as e:
            self.log.emit(f"Task exception: {e!r}")
            self.finished.emit(False, f"Exception: {e}")


# ---------------------------
# Main Application Window (AgentClientApp)
# ---------------------------
class AgentClientApp(QtWidgets.QMainWindow):
    ui_log = QtCore.Signal(str)
    ui_invoke = QtCore.Signal(object)
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Agent Client")
        self.resize(860, 600)
        self.setMinimumSize(720, 460)

        # Frameless transparent window
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Core logic
        self.api = ApiClient()
        self.agent_runner = AgentRunner(
            api_client=self.api,
            log_fn=self.log,
            on_control_request=self._on_server_control_request,
            ui_executor=self.run_on_ui,
            on_command=self._on_server_command,
        )

        # Health worker
        self._health_worker: Optional[HealthWorker] = None

        # keep running TaskWorkers to prevent GC
        self._workers: List[TaskWorker] = []
        
        # Track agent state
        self._agent_start_time: Optional[float] = None
        self._last_heartbeat_ts: Optional[float] = None
        self._last_metrics_ts: Optional[float] = None
        self._last_metrics_data: Optional[Dict[str, Any]] = None
        self._current_profile: Optional[Dict[str, Any]] = None
        
        # Timer to update status info
        self._status_timer = QtCore.QTimer(self)
        self._status_timer.timeout.connect(self._update_status_info)
        self._status_timer.start(1000)  # Update every second

        # Build UI with stacked screens
        self._build_ui()
        self._apply_style()

        # Wire UI thread helpers
        self.ui_log.connect(self._append_log)
        self.ui_invoke.connect(self._invoke)
        
        # Set metrics callback for AgentRunner
        self.agent_runner.set_metrics_sent_callback(self._on_metrics_sent)

        # Pet feature disabled for academic project
        self.pet_window = PetWindow(click_callback=self._on_pet_clicked)
        self.pet_window.hide()

    # -------------------------
    # UI construction
    # -------------------------
    def _build_ui(self) -> None:
        # Central translucent container with header and pages
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        self.glass = GlassFrame()
        root.addWidget(self.glass, 1)

        shell = QtWidgets.QVBoxLayout(self.glass)
        shell.setContentsMargins(0, 0, 0, 10)
        shell.setSpacing(6)

        # Header bar (drag area + window controls)
        header = HeaderBar("Agent Client")
        shell.addWidget(header)

        # Pages
        self.stacked = QtWidgets.QStackedWidget()
        shell.addWidget(self.stacked, 1)

        # Connect screen
        self.connect_screen = ConnectScreen()
        self.stacked.addWidget(self.connect_screen)

        # Auth screen
        self.auth_screen = AuthScreen()
        self.stacked.addWidget(self.auth_screen)

        # Main screen
        self.main_screen = MainScreen()
        self.stacked.addWidget(self.main_screen)

        # Default to connect page first
        self.stacked.setCurrentWidget(self.connect_screen)

        # Wire buttons to existing handlers while preserving logic
        self.connect_screen.connect_btn.clicked.connect(self._connect_clicked)
        self.auth_screen.login_btn.clicked.connect(self._on_login_clicked)
        self.auth_screen.reg_btn.clicked.connect(self._on_register_clicked)

        self.main_screen.connect_btn.clicked.connect(self._connect_clicked)
        self.main_screen.start_btn.clicked.connect(self._on_start_agent)
        self.main_screen.stop_btn.clicked.connect(self._on_stop_agent)
        self.main_screen.accept_btn.clicked.connect(self._on_accept_control_clicked)
        self.main_screen.spam_btn.clicked.connect(self._on_spam_clicked)
        # Pet toggle button removed for academic project
        self.main_screen.auto_metrics_chk.toggled.connect(self._on_auto_metrics_toggled)
        self.main_screen.profile_btn.clicked.connect(self._on_edit_profile)

        # Expose commonly used widgets to keep existing method logic minimal
        # Initially point to Connect screen controls
        self.server_edit = self.connect_screen.server_edit
        self.connect_btn = self.connect_screen.connect_btn
        self.status_label = self.connect_screen.status_label
        self.start_btn = self.main_screen.start_btn
        self.stop_btn = self.main_screen.stop_btn
        self.accept_btn = self.main_screen.accept_btn
        self.spam_btn = self.main_screen.spam_btn
        self.auto_metrics_chk = self.main_screen.auto_metrics_chk
        self.logged_in_label = self.main_screen.logged_in_label
        self.log_view = self.main_screen.log_view
        # toggle_pet_btn removed for academic project
        self.app_status = self.main_screen.app_status

    # -------------------------
    # Styling
    # -------------------------
    def _apply_style(self) -> None:
        # Cyberpunk Theme với độ đậm cao, dễ đọc
        s = """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(10, 0, 25, 240),
                stop:1 rgba(5, 0, 15, 250));
            color: #e0ffff;
        }
        QLabel {
            color: #e0ffff;
        }
        QLineEdit {
            background: rgba(0, 20, 40, 200);
            border: 2px solid rgba(0, 255, 255, 100);
            color: #e0ffff;
            padding: 10px 12px;
            border-radius: 10px;
            font-size: 13px;
        }
        QLineEdit:focus {
            border: 2px solid rgba(0, 255, 255, 255);
            background: rgba(0, 30, 50, 220);
        }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(0, 255, 255, 200),
                stop:1 rgba(0, 200, 255, 220));
            color: #0a0a1a;
            border: 2px solid rgba(0, 255, 255, 255);
            padding: 10px 16px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 13px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(0, 255, 255, 255),
                stop:1 rgba(0, 220, 255, 255));
            border: 2px solid rgba(255, 255, 255, 255);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(0, 200, 255, 180),
                stop:1 rgba(0, 150, 200, 200));
        }
        QPushButton:disabled {
            background: rgba(50, 50, 70, 150);
            color: rgba(160, 160, 180, 150);
            border: 2px solid rgba(100, 100, 120, 100);
        }
        /* Secondary buttons (Accept, toggles) - Magenta/Pink neon */
        QPushButton#secondary {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 0, 255, 200),
                stop:1 rgba(200, 0, 200, 220));
            border: 2px solid rgba(255, 0, 255, 255);
            color: #ffffff;
        }
        QPushButton#secondary:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 50, 255, 255),
                stop:1 rgba(255, 0, 255, 255));
        }
        QCheckBox {
            color: #e0ffff;
            font-size: 13px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid rgba(0, 255, 255, 150);
            border-radius: 4px;
            background: rgba(0, 20, 40, 200);
        }
        QCheckBox::indicator:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(0, 255, 255, 255),
                stop:1 rgba(0, 200, 255, 255));
            border: 2px solid rgba(0, 255, 255, 255);
        }
        """
        self.setStyleSheet(s)

    # -------------------------
    # Pet controls - DISABLED for academic project
    # -------------------------
    def _place_pet_default(self) -> None:
        # Feature disabled
        pass

    def _toggle_pet(self) -> None:
        # Feature disabled
        pass

    def _on_pet_clicked(self) -> None:
        # Feature disabled
        pass

    def _show_pet_speech(self, text: str, auto_hide: bool = True, duration_ms: int = SPEECH_DURATION_MS) -> None:
        # Feature disabled - no speech bubbles
        pass

    # -------------------------
    # Logging (thread-safe)
    # -------------------------
    def log(self, text: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.ui_log.emit(f"[{ts}] {text}")

    @QtCore.Slot(str)
    def _append_log(self, text: str) -> None:
        self.log_view.appendPlainText(text)
        # Pet speech feature disabled for academic project

    # UI invoke helpers to replace cross-thread singleShot
    def run_on_ui(self, fn: Callable[[], None]) -> None:
        self.ui_invoke.emit(fn)

    @QtCore.Slot(object)
    def _invoke(self, fn: Callable[[], None]) -> None:
        try:
            fn()
        except Exception:
            pass

    # -------------------------
    # Spam test and metrics toggle
    # -------------------------
    def _on_auto_metrics_toggled(self, checked: bool) -> None:
        try:
            self.agent_runner.set_metrics_enabled(bool(checked))
            self.log(f"Auto metrics {'enabled' if checked else 'disabled'}.")
        except Exception as e:
            self.log(f"Toggle metrics error: {e!r}")

    def _spam_task(self, count: int = 100, interval_ms: int = 50, cpm: int = 1200) -> tuple[bool, str]:
        sent = 0
        failed_count = 0
        count = max(1, int(count))
        interval_ms = max(1, int(interval_ms))
        cpm = max(0, int(cpm))
        
        # Clear URL cache trước khi spam để force re-discover đúng endpoint
        self.api._metrics_url_cache = None
        
        for i in range(count):
            if QtCore.QThread.currentThread().isInterruptionRequested():
                break
            try:
                metrics = self.api.collect_metrics()
                # Only set connections_per_min if CPM is reasonable (not spam test)
                # Spam test should use 0 or low value to avoid triggering AI warnings
                if cpm > 0 and cpm < 100:
                    metrics["connections_per_min"] = cpm
                else:
                    # For spam test, set to 0 to avoid AI detection
                    metrics["connections_per_min"] = 0
                ok, msg = self.api.send_metrics(metrics)
                if ok:
                    sent += 1
                    failed_count = 0  # Reset failed counter on success
                else:
                    failed_count += 1
                    # Nếu liên tiếp fail 3 lần, có thể endpoint không tồn tại -> skip nhanh hơn
                    if failed_count >= 3:
                        self.log(f"Spam {i + 1}/{count}: FAIL ({msg}) - Stopping after {failed_count} consecutive failures")
                        break
                # Chỉ log mỗi 10 lần hoặc khi fail để không spam log quá nhiều
                if (i + 1) % 10 == 0 or not ok:
                    self.log(f"Spam {i + 1}/{count}: {'OK' if ok else 'FAIL'} ({msg})")
            except Exception as e:
                failed_count += 1
                if failed_count >= 3:
                    self.log(f"Spam error: {e!r} - Stopping after {failed_count} consecutive failures")
                    break
                self.log(f"Spam error: {e!r}")
            QtCore.QThread.msleep(interval_ms)
        return True, f"Spam done: {sent}/{count} sent"

    def _on_spam_clicked(self) -> None:
        # fire-and-forget spam to test AI block với tham số người dùng nhập
        try:
            count = getattr(self.main_screen, "spam_count_spin", None)
            cpm = getattr(self.main_screen, "spam_cpm_spin", None)
            n = int(count.value()) if count is not None else 100
            cps = int(cpm.value()) if cpm is not None else 1200
        except Exception:
            n, cps = 100, 1200
        self._run_task(self._spam_task, n, 50, cps)

    # -------------------------
    # Task worker helper (keeps references)
    # -------------------------
    def _run_task(self, fn, *args, connect_finished=None, **kwargs) -> TaskWorker:
        w = TaskWorker(fn, *args, **kwargs)
        self._workers.append(w)
        w.log.connect(self.log)
        if connect_finished:
            w.finished.connect(connect_finished)
        # always cleanup after finish
        w.finished.connect(lambda ok, msg, worker=w: self._cleanup_worker(worker))
        w.start()
        return w

    def _cleanup_worker(self, worker: TaskWorker) -> None:
        try:
            # give it a moment then wait
            worker.wait(200)
        except Exception:
            pass
        if worker in self._workers:
            self._workers.remove(worker)

    # -------------------------
    # Connect & Health
    # -------------------------
    def _connect_clicked(self) -> None:
        url = self.server_edit.text().strip()
        if not url:
            QtWidgets.QMessageBox.warning(self, "Missing URL", "Please enter the Server URL.")
            return
        self.api.set_base_url(url)
        self.log(f"Connected to server: {url}")
        # restart health worker
        if self._health_worker:
            try:
                self._health_worker.stop()
                self._health_worker.wait(1200)
            except Exception:
                pass
        self._health_worker = HealthWorker(self.api, interval=HEALTH_INTERVAL)
        self._health_worker.health.connect(self._on_health)
        self._health_worker.log.connect(self.log)
        self._health_worker.start()
        # immediate health check via TaskWorker
        self._run_task(self.api.health, connect_finished=lambda ok, msg: self._on_health(ok, msg))

    @QtCore.Slot(bool, str)
    def _on_health(self, ok: bool, msg: str) -> None:
        url = getattr(self.api, "base_url", "-")
        status = "🟢 Online" if ok else "🔴 Offline"
        text = f"🔌 Server: {url} | {status}"
        # Update any status labels on screens
        try:
            if hasattr(self, "connect_screen") and hasattr(self.connect_screen, "status_label"):
                self.connect_screen.status_label.setText(text)
        except Exception:
            pass
        try:
            if hasattr(self, "main_screen") and hasattr(self.main_screen, "status_label"):
                self.main_screen.status_label.setText(text)
        except Exception:
            pass
        # If we're on connect screen and server is online, go to auth
        try:
            if ok and self.stacked.currentWidget() is self.connect_screen:
                self.stacked.setCurrentWidget(self.auth_screen)
                # keep self.server_edit pointing to connect screen; main has separate field
        except Exception:
            pass

    # -------------------------
    # Register / Login
    # -------------------------
    def _on_register_clicked(self) -> None:
        # read from AuthScreen fields
        email = self.auth_screen.reg_email.text().strip()
        pwd = self.auth_screen.reg_pass.text().strip()
        if not email or not pwd:
            QtWidgets.QMessageBox.warning(self, "Missing fields", "Please enter email and password.")
            return
        self._run_task(self.api.register, email, pwd, connect_finished=self._on_register_done)

    @QtCore.Slot(bool, str)
    def _on_register_done(self, ok: bool, msg: str) -> None:
        self.log(f"Register: {msg}")
        if ok:
            QtWidgets.QMessageBox.information(self, "Register", msg)
        else:
            QtWidgets.QMessageBox.critical(self, "Register", msg)

    def _on_login_clicked(self) -> None:
        user = self.auth_screen.login_user.text().strip()
        pwd = self.auth_screen.login_pass.text().strip()
        if not user or not pwd:
            QtWidgets.QMessageBox.warning(self, "Missing fields", "Please enter username and password.")
            return
        self._run_task(self.api.login, user, pwd, connect_finished=self._on_login_done)

    @QtCore.Slot(bool, str)
    def _on_login_done(self, ok: bool, msg: str) -> None:
        self.log(f"Login: {msg}")
        if ok:
            name = getattr(self.api, "username", "user")
            self.logged_in_label.setText(f"Logged in as: {name}")
            # switch to main screen
            self.stacked.setCurrentWidget(self.main_screen)
            # remap shared references to main screen widgets after login
            try:
                self.server_edit = self.main_screen.server_edit
                self.connect_btn = self.main_screen.connect_btn
                # status label on main will be updated by future _on_health calls
                self.status_label = self.main_screen.status_label
            except Exception:
                pass
            # Load và hiển thị profile sau khi login
            try:
                ok, profile, profile_msg = self.api.get_profile()
                if ok and profile:
                    self._current_profile = profile
                    status = profile.get("status", 1)
                    # Check if client is blocked before starting agent
                    if status == 3:
                        QtWidgets.QMessageBox.critical(
                            self, 
                            "Client Blocked", 
                            "This client has been blocked by the server. Please contact administrator."
                        )
                        self.log("Client is blocked (status=3), agent will not start")
                        return  # Don't start agent if blocked
                    elif status == 2:
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Client Warning",
                            "This client has a warning status. Please review your account."
                        )
                    self.log(f"Profile loaded: status={status}, online={profile.get('online', False)}")
                else:
                    self.log(f"Failed to load profile: {profile_msg}")
            except Exception as e:
                self.log(f"Load profile error: {e!r}")
            # Tự động start agent sau khi login để client luôn lắng nghe lệnh control / notify
            try:
                self._on_start_agent()
            except Exception as e:
                self.log(f"Auto-start agent after login failed: {e!r}")
            QtWidgets.QMessageBox.information(self, "Login", msg)
        else:
            QtWidgets.QMessageBox.critical(self, "Login", msg)

    # -------------------------
    # Agent controls
    # -------------------------
    def _on_start_agent(self) -> None:
        try:
            started = self.agent_runner.start()
            if started:
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self._agent_start_time = time.time()
                self._last_heartbeat_ts = time.time()
            else:
                self.log("Agent did not start (check login/server).")
        except Exception as e:
            self.log(f"Start error: {e!r}")

    def _on_stop_agent(self) -> None:
        self._stop_agent_safely()
    
    def _stop_agent_safely(self) -> None:
        """Safely stop agent without deadlock"""
        try:
            stopped = self.agent_runner.stop()
            if stopped:
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self._agent_start_time = None
                self._last_heartbeat_ts = None
                self._last_metrics_ts = None
            else:
                self.log("Agent did not stop cleanly.")
        except Exception as e:
            self.log(f"Stop error: {e!r}")

    def _on_accept_control_clicked(self) -> None:
        # manual accept
        self.log("User accepted control.")
        QtWidgets.QMessageBox.information(self, "Control", "Control accepted.")
    
    def _load_profile(self) -> None:
        """Load client profile from server"""
        try:
            ok, profile, msg = self.api.get_profile()
            if ok and profile:
                self._current_profile = profile
                # Log profile info
                status = profile.get("status", 1)
                online = profile.get("online", False)
                tags = profile.get("tags", [])
                note = profile.get("note", "")
                self.log(f"Profile loaded: status={status}, online={online}, tags={tags}, note={note[:50] if note else ''}")
            else:
                self.log(f"Failed to load profile: {msg}")
        except Exception as e:
            self.log(f"Load profile error: {e!r}")
    
    def _on_edit_profile(self) -> None:
        """Open profile edit dialog"""
        try:
            # Load current profile first
            ok, profile, msg = self.api.get_profile()
            if not ok or not profile:
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to load profile: {msg}")
                return
            
            # Create dialog
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Edit Client Profile")
            dialog.setMinimumWidth(400)
            layout = QtWidgets.QVBoxLayout(dialog)
            
            # Client ID
            client_id_label = QtWidgets.QLabel("Client ID:")
            client_id_edit = QtWidgets.QLineEdit()
            current_client_id = self.api._client_id or ""
            client_id_edit.setText(current_client_id)
            client_id_edit.setPlaceholderText("Enter new client ID")
            layout.addWidget(client_id_label)
            layout.addWidget(client_id_edit)
            
            # Tags
            tags_label = QtWidgets.QLabel("Tags (comma-separated):")
            tags_edit = QtWidgets.QLineEdit()
            current_tags = profile.get("tags", [])
            tags_edit.setText(", ".join(current_tags) if current_tags else "")
            layout.addWidget(tags_label)
            layout.addWidget(tags_edit)
            
            # Note
            note_label = QtWidgets.QLabel("Note:")
            note_edit = QtWidgets.QPlainTextEdit()
            note_edit.setPlainText(profile.get("note", "") or "")
            note_edit.setMaximumHeight(100)
            layout.addWidget(note_label)
            layout.addWidget(note_edit)
            
            # Buttons
            btn_layout = QtWidgets.QHBoxLayout()
            save_btn = QtWidgets.QPushButton("Save")
            cancel_btn = QtWidgets.QPushButton("Cancel")
            btn_layout.addStretch()
            btn_layout.addWidget(save_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)
            
            def on_save():
                # Check if client ID changed
                new_client_id = client_id_edit.text().strip()
                old_client_id = self.api._client_id or ""
                client_id_changed = new_client_id and new_client_id != old_client_id
                
                if client_id_changed:
                    # Validate client ID
                    if not new_client_id or len(new_client_id) < 3:
                        QtWidgets.QMessageBox.warning(dialog, "Invalid Client ID", "Client ID must be at least 3 characters long.")
                        return
                    
                    # Confirm change
                    reply = QtWidgets.QMessageBox.question(
                        dialog,
                        "Change Client ID",
                        f"Changing Client ID from '{old_client_id}' to '{new_client_id}'.\n\n"
                        "This will:\n"
                        "- Update your client identity\n"
                        "- You may need to re-register with server\n"
                        "- Agent will restart to use new ID\n\n"
                        "Continue?",
                        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                        QtWidgets.QMessageBox.StandardButton.No
                    )
                    if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                        return
                
                tags_str = tags_edit.text().strip()
                tags_list = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
                note_text = note_edit.toPlainText().strip()
                
                # Store result data in a mutable container for callback
                result_container = {"data": None}
                
                # Wrapper to convert (bool, Optional[Dict], str) -> (bool, str) for TaskWorker
                def update_profile_wrapper():
                    # If client ID changed, update it on server first
                    if client_id_changed:
                        # Update client_id on server (this will rename the existing client)
                        ok_id, data_id, msg_id = self.api.update_client_id(new_client_id)
                        if not ok_id:
                            # If update failed, return error
                            result_container["data"] = None
                            return False, f"Failed to update client ID: {msg_id}"
                        
                        self.log(f"Client ID updated from '{old_client_id}' to '{new_client_id}' on server")
                        # Local client_id is already updated by update_client_id method
                        result_container["data"] = data_id
                    
                    # Update profile on server (tags, note) - this will use current client_id
                    ok, data, msg = self.api.update_profile(
                        tags=tags_list,
                        note=note_text if note_text else None
                    )
                    if not client_id_changed:
                        result_container["data"] = data
                    return ok, msg
                
                def on_finished(ok: bool, msg: str):
                    if ok:
                        if client_id_changed:
                            # Restart agent to use new client ID
                            self.log("Restarting agent with new client ID...")
                            was_running = self.agent_runner.is_running
                            if was_running:
                                self._stop_agent_safely()
                            # Agent will use new client_id on next start
                            if was_running:
                                QtCore.QTimer.singleShot(500, self._on_start_agent)
                    self._on_profile_updated(ok, result_container["data"], msg)
                
                self._run_task(
                    update_profile_wrapper,
                    connect_finished=on_finished
                )
                dialog.accept()
            
            save_btn.clicked.connect(on_save)
            cancel_btn.clicked.connect(dialog.reject)
            
            dialog.exec()
        except Exception as e:
            self.log(f"Edit profile error: {e!r}")
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to open profile editor: {e}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}")
    
    def _on_profile_updated(self, ok: bool, data: Optional[Dict[str, Any]], msg: str) -> None:
        """Callback when profile is updated"""
        if ok:
            self.log(f"Profile updated: {msg}")
            if data:
                self._current_profile = data
            QtWidgets.QMessageBox.information(self, "Success", "Profile updated successfully")
            # Reload profile
            self._load_profile()
        else:
            self.log(f"Profile update failed: {msg}")
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to update profile: {msg}")

    def _on_server_control_request(self) -> None:
        # AgentRunner calls this via ui_executor
        QtWidgets.QMessageBox.question(
            self, "Control Request", "Server requests control access — Accept?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
    
    def _on_metrics_sent(self, metrics: Dict[str, Any]) -> None:
        """Callback when metrics are sent to server"""
        self._last_metrics_ts = time.time()
        self._last_metrics_data = metrics
    
    def _update_status_info(self) -> None:
        """Update uptime, heartbeat, and metrics display"""
        try:
            # Update uptime
            if self._agent_start_time:
                uptime_sec = int(time.time() - self._agent_start_time)
                hours = uptime_sec // 3600
                minutes = (uptime_sec % 3600) // 60
                seconds = uptime_sec % 60
                uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                if hasattr(self.main_screen, 'uptime_label'):
                    self.main_screen.uptime_label.setText(f"⏱ Uptime: {uptime_str}")
            else:
                if hasattr(self.main_screen, 'uptime_label'):
                    self.main_screen.uptime_label.setText("⏱ Uptime: -")
            
            # Update last heartbeat (use last metrics time as heartbeat)
            if self._last_metrics_ts:
                elapsed = int(time.time() - self._last_metrics_ts)
                if elapsed < 60:
                    heartbeat_str = f"{elapsed}s ago"
                elif elapsed < 3600:
                    heartbeat_str = f"{elapsed // 60}m ago"
                else:
                    heartbeat_str = f"{elapsed // 3600}h ago"
                if hasattr(self.main_screen, 'heartbeat_label'):
                    self.main_screen.heartbeat_label.setText(f"💓 Last heartbeat: {heartbeat_str}")
            else:
                if hasattr(self.main_screen, 'heartbeat_label'):
                    self.main_screen.heartbeat_label.setText("💓 Last heartbeat: -")
            
            # Update last metrics
            if self._last_metrics_ts:
                elapsed = int(time.time() - self._last_metrics_ts)
                metrics_info = ""
                if self._last_metrics_data:
                    cpu = self._last_metrics_data.get('cpu_percent', 0)
                    mem = self._last_metrics_data.get('memory_percent', 0)
                    metrics_info = f" (CPU: {cpu:.1f}%, RAM: {mem:.1f}%)"
                if elapsed < 60:
                    metrics_str = f"{elapsed}s ago{metrics_info}"
                elif elapsed < 3600:
                    metrics_str = f"{elapsed // 60}m ago{metrics_info}"
                else:
                    metrics_str = f"{elapsed // 3600}h ago{metrics_info}"
                if hasattr(self.main_screen, 'metrics_label'):
                    self.main_screen.metrics_label.setText(f"📊 Last metrics: {metrics_str}")
            else:
                if hasattr(self.main_screen, 'metrics_label'):
                    self.main_screen.metrics_label.setText("📊 Last metrics: -")
        except Exception:
            pass

    def _on_server_command(self, cmd: dict) -> None:
        try:
            action = str(cmd.get("action", "")).lower()
            message = str(cmd.get("message", "")).strip()
        except Exception:
            action = ""
            message = ""

        # Normalize alternative payload shapes
        try:
            if not action and isinstance(cmd, dict):
                for key in ("type", "cmd", "command", "status", "state"):
                    if key in cmd and isinstance(cmd.get(key), (str, int)):
                        action = str(cmd.get(key)).lower()
                        break
                # boolean flags e.g., {"block": true}
                if not action:
                    if bool(cmd.get("block", False)):
                        action = "block"
                    elif bool(cmd.get("unblock", False)):
                        action = "unblock"
                # message aliases
                if not message:
                    for mkey in ("msg", "text", "note"):
                        if mkey in cmd:
                            message = str(cmd.get(mkey) or "").strip()
                            break
        except Exception:
            pass

        # Nếu action là request_control thì bật dialog confirm control, giữ nguyên message nếu có
        if action == "request_control":
            # Hiện message nếu server gửi kèm
            if message:
                QtWidgets.QMessageBox.information(self, "Control Request", message)
            self._on_server_control_request()
            return

        # Pet speech feature disabled for academic project

        # Route by action
        if action == "notify":
            QtWidgets.QMessageBox.information(self, "Server Message", message or "Notification")
        elif action == "block":
            # Stop agent and mark status (non-blocking to avoid deadlock)
            try:
                # Use QTimer to defer stop() call, avoiding deadlock if called from start()
                QtCore.QTimer.singleShot(100, lambda: self._stop_agent_safely())
            except Exception:
                pass
            self.app_status.setText("Blocked by server")
            QtWidgets.QMessageBox.critical(self, "Blocked", message or "This client has been blocked by the server.")
        elif action == "unblock":
            self.app_status.setText("Ready")
            QtWidgets.QMessageBox.information(self, "Unblocked", message or "This client has been unblocked.")
        elif action in ("shutdown", "restart"):
            # Show confirmation dialog and execute if user accepts
            action_name = "tắt máy" if action == "shutdown" else "khởi động lại máy"
            reply = QtWidgets.QMessageBox.question(
                self,
                action.capitalize(),
                f"Server yêu cầu {action_name}.\n\n{message or ''}\n\nBạn có muốn thực hiện không?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self._execute_system_command(action)
            else:
                self.log(f"User declined {action} request")
        elif action in ("execute_command", "get_system_info", "upload_file", "download_file", "get_screenshot"):
            # These commands are handled by CommandExecutor, but show result if available
            result = cmd.get("result")
            if result:
                success = result.get("success", False)
                output = result.get("output", "")
                error = result.get("error", "")
                metadata = result.get("metadata", {})
                
                if success:
                    if action == "get_screenshot":
                        # For screenshots, show metadata instead of base64 string
                        width = metadata.get("screen_width", "?")
                        height = metadata.get("screen_height", "?")
                        quality = metadata.get("quality", "?")
                        format_type = metadata.get("format", "jpeg")
                        output_size = len(output) if output else 0
                        size_kb = output_size / 1024 if output_size > 0 else 0
                        msg = f"Screenshot captured successfully!\n\n" \
                              f"Resolution: {width}x{height}\n" \
                              f"Format: {format_type.upper()}\n" \
                              f"Quality: {quality}\n" \
                              f"Size: {size_kb:.1f} KB\n\n" \
                              f"(Base64 data sent to server)"
                    else:
                        # For other commands, show output (truncated)
                        msg = f"Command executed successfully.\n\nOutput:\n{output[:500]}" if output else "Command executed successfully."
                    QtWidgets.QMessageBox.information(self, "Command Result", msg)
                else:
                    msg = f"Command failed.\n\nError: {error or 'Unknown error'}"
                    QtWidgets.QMessageBox.warning(self, "Command Failed", msg)
        else:
            # Unknown or empty action -> show as info if there is a message
            if message:
                QtWidgets.QMessageBox.information(self, "Server", message)
    
    def _execute_system_command(self, action: str) -> None:
        """Execute system command (shutdown/restart) based on OS."""
        import platform
        import subprocess
        
        try:
            self.log(f"Executing system command: {action}")
            system = platform.system().lower()
            
            if action == "shutdown":
                if system == "linux":
                    # Linux: shutdown in 1 minute (can be cancelled)
                    subprocess.Popen(["shutdown", "-h", "+1"], shell=False)
                    QtWidgets.QMessageBox.information(
                        self, 
                        "Shutdown", 
                        "Máy sẽ tắt sau 1 phút. Để hủy, chạy: sudo shutdown -c"
                    )
                elif system == "windows":
                    # Windows: shutdown in 60 seconds
                    subprocess.Popen(["shutdown", "/s", "/t", "60"], shell=False)
                    QtWidgets.QMessageBox.information(
                        self,
                        "Shutdown",
                        "Máy sẽ tắt sau 60 giây. Để hủy, chạy: shutdown /a"
                    )
                elif system == "darwin":  # macOS
                    subprocess.Popen(["shutdown", "-h", "+1"], shell=False)
                    QtWidgets.QMessageBox.information(
                        self,
                        "Shutdown",
                        "Máy sẽ tắt sau 1 phút."
                    )
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", f"Shutdown không được hỗ trợ trên {system}")
                    
            elif action == "restart":
                if system == "linux":
                    # Linux: restart in 1 minute
                    subprocess.Popen(["shutdown", "-r", "+1"], shell=False)
                    QtWidgets.QMessageBox.information(
                        self,
                        "Restart",
                        "Máy sẽ khởi động lại sau 1 phút. Để hủy, chạy: sudo shutdown -c"
                    )
                elif system == "windows":
                    # Windows: restart in 60 seconds
                    subprocess.Popen(["shutdown", "/r", "/t", "60"], shell=False)
                    QtWidgets.QMessageBox.information(
                        self,
                        "Restart",
                        "Máy sẽ khởi động lại sau 60 giây. Để hủy, chạy: shutdown /a"
                    )
                elif system == "darwin":  # macOS
                    subprocess.Popen(["shutdown", "-r", "+1"], shell=False)
                    QtWidgets.QMessageBox.information(
                        self,
                        "Restart",
                        "Máy sẽ khởi động lại sau 1 phút."
                    )
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", f"Restart không được hỗ trợ trên {system}")
            else:
                self.log(f"Unknown system command: {action}")
        except Exception as e:
            self.log(f"Failed to execute {action}: {e}")
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Không thể thực thi lệnh {action}:\n{e}"
            )

    # -------------------------
    # Cleanup
    # -------------------------
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        # Stop agent runner first
        try:
            self.agent_runner.stop()
        except Exception:
            pass

        # Stop health worker
        if self._health_worker:
            try:
                self._health_worker.stop()
                self._health_worker.wait(2000)
            except Exception:
                pass

        # Stop any running TaskWorkers
        for w in list(self._workers):
            try:
                w.requestInterruption()
            except Exception:
                pass
            try:
                w.wait(400)
            except Exception:
                pass
        self._workers.clear()

        # Pet feature disabled

        super().closeEvent(event)


# Expose a simple run() used by entrypoint
def run_app() -> int:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    win = AgentClientApp()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_app())
