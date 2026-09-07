"""
Alicia Modern Desktop Assistant GUI
Built with PyQt6, featuring real-time speech interaction, telemetry gauges, and animated status orb.
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QPoint
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QSizePolicy
)

from config.settings import settings
from config.theme import load_stylesheet
from database.manager import db
from src.core.utils.crosspath import get_style_file
from src.core.voice.tts import tts
from src.gui.thread import VoiceListenerThread, CommandWorkerThread, SystemMonitorThread


class AliciaOrb(QWidget):
    """Animated glowing status orb showing Alicia's current state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(70, 70)
        self.state = "idle"  # idle, listening, thinking, speaking
        self.phase = 0.0

        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(40)  # 25 FPS

    def set_state(self, state: str):
        self.state = state
        self.update()

    def _animate(self):
        self.phase = (self.phase + 0.1) % 6.28
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = 24.0

        # Select color based on state
        if self.state == "listening":
            base_color = QColor(0, 240, 255)  # Cyan
            glow_radius = radius + 6 + 4 * abs(int(self.phase * 3) % 4)
        elif self.state == "thinking":
            base_color = QColor(224, 64, 251)  # Magenta
            glow_radius = radius + 4
        elif self.state == "speaking":
            base_color = QColor(0, 230, 118)  # Neon Green
            glow_radius = radius + 7
        else:  # idle
            base_color = QColor(124, 77, 255)  # Purple
            glow_radius = radius + 2

        # Outer soft glow
        gradient = QRadialGradient(center_x, center_y, glow_radius)
        glow_c = QColor(base_color)
        glow_c.setAlpha(60)
        gradient.setColorAt(0.0, glow_c)
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(glow_radius), int(glow_radius))

        # Inner solid orb
        inner_gradient = QRadialGradient(center_x - 4, center_y - 4, radius)
        highlight = QColor(255, 255, 255, 220)
        inner_gradient.setColorAt(0.0, highlight)
        inner_gradient.setColorAt(0.5, base_color)
        darkened = base_color.darker(160)
        inner_gradient.setColorAt(1.0, darkened)

        painter.setBrush(QBrush(inner_gradient))
        painter.setPen(QPen(base_color.lighter(130), 1.5))
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(radius), int(radius))


class MainWindow(QMainWindow):
    """Main application window for Alicia Assistant."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(settings.ui.window_title)
        self.resize(settings.ui.window_width, settings.ui.window_height)
        self.setMinimumSize(380, 520)

        # Worker threads
        self.voice_thread: Optional[VoiceListenerThread] = None
        self.monitor_thread: Optional[SystemMonitorThread] = None
        self.command_thread: Optional[CommandWorkerThread] = None

        self._init_ui()
        self._load_styles()
        self._start_monitoring()

        # Connect TTS status events
        tts.on_start_speaking = lambda _: self._on_tts_start()
        tts.on_finish_speaking = lambda: self._on_tts_finish()

        # Welcome message
        user_name = db.get_user_name()
        self.add_message("Alicia", f"Hi {user_name}! I'm Alicia, your personal AI assistant. How can I help you today?")

    def _init_ui(self):
        central_widget = QWidget(self)
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 1. Header Frame
        header_frame = QFrame(self)
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 8, 10, 8)

        # Status orb
        self.orb = AliciaOrb(self)
        header_layout.addWidget(self.orb)

        # Title & Status text
        info_layout = QVBoxLayout()
        self.title_label = QLabel("ALICIA", self)
        self.title_label.setObjectName("titleLabel")
        self.status_label = QLabel("System Online", self)
        self.status_label.setObjectName("statusLabel")
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.status_label)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        # Telemetry pills
        telemetry_layout = QVBoxLayout()
        self.cpu_pill = QLabel("CPU: --%", self)
        self.cpu_pill.setProperty("class", "pillLabel")
        self.ram_pill = QLabel("RAM: --%", self)
        self.ram_pill.setProperty("class", "pillLabel")
        telemetry_layout.addWidget(self.cpu_pill)
        telemetry_layout.addWidget(self.ram_pill)
        header_layout.addLayout(telemetry_layout)

        main_layout.addWidget(header_frame)

        # 2. Chat Conversation Scroll Area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_container.setObjectName("chatContainer")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(4, 8, 4, 8)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area, 1)

        # 3. Quick Action Chips
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(6)

        actions = [
            ("Time", lambda: self.submit_command("what time is it")),
            ("Notes", lambda: self.submit_command("show notes")),
            ("Stats", lambda: self.submit_command("cpu usage")),
            ("Clear", self.clear_chat),
        ]
        for name, callback in actions:
            btn = QPushButton(name, self)
            btn.setFixedHeight(26)
            btn.clicked.connect(callback)
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        main_layout.addLayout(quick_layout)

        # 4. Bottom Input Bar
        input_frame = QFrame(self)
        input_frame.setObjectName("inputFrame")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(6, 4, 6, 4)
        input_layout.setSpacing(8)

        # Microphone Toggle Button
        self.mic_button = QPushButton("🎤", self)
        self.mic_button.setObjectName("micButton")
        self.mic_button.setFixedSize(36, 36)
        self.mic_button.setToolTip("Click to speak")
        self.mic_button.clicked.connect(self.toggle_mic)
        input_layout.addWidget(self.mic_button)

        # Text input field
        self.input_field = QLineEdit(self)
        self.input_field.setObjectName("commandInput")
        self.input_field.setPlaceholderText("Type a command or ask Alicia...")
        self.input_field.returnPressed.connect(self._on_send_clicked)
        input_layout.addWidget(self.input_field, 1)

        # Send Button
        self.send_button = QPushButton("Send", self)
        self.send_button.setObjectName("sendButton")
        self.send_button.setFixedHeight(34)
        self.send_button.clicked.connect(self._on_send_clicked)
        input_layout.addWidget(self.send_button)

        main_layout.addWidget(input_frame)

    def _load_styles(self):
        style_path = get_style_file("main.qss")
        stylesheet = load_stylesheet(style_path, settings.ui.theme)
        self.setStyleSheet(stylesheet)

    def _start_monitoring(self):
        self.monitor_thread = SystemMonitorThread(interval=3.0)
        self.monitor_thread.metrics_updated.connect(self._on_metrics_updated)
        self.monitor_thread.start()

    @pyqtSlot(float, float, dict)
    def _on_metrics_updated(self, cpu: float, ram: float, bat: dict):
        self.cpu_pill.setText(f"CPU: {int(cpu)}%")
        self.ram_pill.setText(f"RAM: {int(ram)}%")

    def add_message(self, sender: str, text: str):
        bubble_frame = QFrame(self)
        is_user = sender.lower() == "you" or sender.lower() == "user"

        bubble_frame.setProperty("class", "userBubble" if is_user else "assistantBubble")
        b_layout = QVBoxLayout(bubble_frame)
        b_layout.setContentsMargins(10, 6, 10, 6)
        b_layout.setSpacing(2)

        sender_label = QLabel(sender, bubble_frame)
        sender_label.setProperty("class", "bubbleSender")
        sender_label.setStyleSheet("color: #38bdf8;" if is_user else "color: #00f0ff;")

        text_label = QLabel(text, bubble_frame)
        text_label.setProperty("class", "bubbleText")
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        b_layout.addWidget(sender_label)
        b_layout.addWidget(text_label)

        # Wrap in alignment container
        container = QWidget()
        c_layout = QHBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        if is_user:
            c_layout.addStretch()
            c_layout.addWidget(bubble_frame)
        else:
            c_layout.addWidget(bubble_frame)
            c_layout.addStretch()

        self.chat_layout.addWidget(container)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear_chat(self):
        for i in reversed(range(self.chat_layout.count())):
            item = self.chat_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        self.chat_layout.addStretch()

    def _on_send_clicked(self):
        cmd = self.input_field.text().strip()
        if cmd:
            self.input_field.clear()
            self.submit_command(cmd)

    def submit_command(self, command: str):
        if not command:
            return

        self.add_message("You", command)
        self.orb.set_state("thinking")
        self.status_label.setText("Processing...")

        # Run command worker
        self.command_thread = CommandWorkerThread(command)
        self.command_thread.response_ready.connect(self._on_command_finished)
        self.command_thread.execution_failed.connect(self._on_command_failed)
        self.command_thread.start()

    @pyqtSlot(str, str)
    def _on_command_finished(self, command: str, response: str):
        self.add_message("Alicia", response)
        self.orb.set_state("speaking")
        self.status_label.setText("Speaking...")
        tts.speak(response)

    @pyqtSlot(str, str)
    def _on_command_failed(self, command: str, error: str):
        err_msg = f"Sorry, command failed: {error}"
        self.add_message("Alicia", err_msg)
        self.orb.set_state("idle")
        self.status_label.setText("Online")

    def toggle_mic(self):
        if self.voice_thread and self.voice_thread.isRunning():
            self.voice_thread.stop()
            self.voice_thread = None
            self.mic_button.setText("🎤")
            self.mic_button.setProperty("active", "false")
            self.mic_button.setStyle(self.mic_button.style())
            self.orb.set_state("idle")
            self.status_label.setText("Online")
        else:
            self.mic_button.setText("⏹")
            self.mic_button.setProperty("active", "true")
            self.mic_button.setStyle(self.mic_button.style())
            self.orb.set_state("listening")
            self.status_label.setText("Listening...")

            self.voice_thread = VoiceListenerThread(continuous=False)
            self.voice_thread.speech_detected.connect(self._on_speech_detected)
            self.voice_thread.status_changed.connect(lambda s: self.status_label.setText(s))
            self.voice_thread.finished.connect(self._on_voice_finished)
            self.voice_thread.start()

    @pyqtSlot(str)
    def _on_speech_detected(self, phrase: str):
        if phrase:
            self.submit_command(phrase)

    def _on_voice_finished(self):
        self.mic_button.setText("🎤")
        self.mic_button.setProperty("active", "false")
        self.mic_button.setStyle(self.mic_button.style())
        if self.orb.state == "listening":
            self.orb.set_state("idle")

    def _on_tts_start(self):
        QTimer.singleShot(0, lambda: self.orb.set_state("speaking"))
        QTimer.singleShot(0, lambda: self.status_label.setText("Speaking..."))

    def _on_tts_finish(self):
        QTimer.singleShot(0, lambda: self.orb.set_state("idle"))
        QTimer.singleShot(0, lambda: self.status_label.setText("Online"))

    def closeEvent(self, event):
        if self.voice_thread:
            self.voice_thread.stop()
        if self.monitor_thread:
            self.monitor_thread.stop()
        tts.shutdown()
        event.accept()


def run_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
