"""
Alicia GUI Background Threads
Qt worker threads for non-blocking voice recognition, command execution, and system monitoring.
"""

import time
from PyQt6.QtCore import QThread, pyqtSignal

from src.core.voice.stt import stt
from src.core.voice.tts import tts
from src.core.voice.fuzz import matches_wake_word
from src.core.cmd.action import execute_command
from src.core.cmd.system import system


class VoiceListenerThread(QThread):
    """Continuously listens for microphone input or wake words without blocking the UI."""
    speech_detected = pyqtSignal(str)
    wake_word_detected = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, continuous: bool = False):
        super().__init__()
        self.running = True
        self.continuous = continuous

    def run(self):
        while self.running:
            self.status_changed.emit("Listening...")
            try:
                # Listen with comfortable timeout
                phrase = stt.listen(timeout=6, phrase_time_limit=10)
                if phrase:
                    # Check wake word
                    matched, wake_word = matches_wake_word(phrase)
                    if matched:
                        self.wake_word_detected.emit(wake_word)
                    self.speech_detected.emit(phrase)

                    if not self.continuous:
                        break
            except Exception as e:
                print(f"[VoiceThread] Error: {e}")
                time.sleep(0.5)

            time.sleep(0.1)

        self.status_changed.emit("Idle")

    def stop(self):
        self.running = False
        stt.stop_listening()
        self.wait(1000)


class CommandWorkerThread(QThread):
    """Executes commands asynchronously to keep the UI smooth and responsive."""
    response_ready = pyqtSignal(str, str)  # (command, response)
    execution_failed = pyqtSignal(str, str)

    def __init__(self, command: str):
        super().__init__()
        self.command = command

    def run(self):
        try:
            response = execute_command(self.command)
            self.response_ready.emit(self.command, response)
        except Exception as e:
            self.execution_failed.emit(self.command, str(e))


class SystemMonitorThread(QThread):
    """Periodically queries CPU, RAM, and Battery metrics."""
    metrics_updated = pyqtSignal(float, float, dict)  # cpu_percent, ram_percent, battery_info

    def __init__(self, interval: float = 2.5):
        super().__init__()
        self.interval = interval
        self.running = True

    def run(self):
        while self.running:
            try:
                cpu = system.cpu_usage(interval=0.2)
                ram = system.ram_usage()
                bat = system.get_battery()
                self.metrics_updated.emit(cpu, ram.get("percent", 0.0), bat)
            except Exception:
                pass
            time.sleep(self.interval)

    def stop(self):
        self.running = False
        self.wait(500)
