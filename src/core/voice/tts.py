"""
Alicia Text-to-Speech (TTS) Engine
Asynchronous speech generation with queue management, voice pitch/speed controls,
and UI state synchronization.
"""

import os
import queue
import threading
import time
from typing import Callable, Optional

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

from config.settings import settings


class TextToSpeech:
    """Handles speech synthesis using pyttsx3 with background worker thread."""

    def __init__(
        self,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
        voice_gender: Optional[str] = None
    ):
        self.rate = rate or settings.voice.speech_rate
        self.volume = volume or settings.voice.volume
        self.voice_gender = voice_gender or settings.voice.voice_gender

        self.engine = None
        self.currently_speaking = False
        self.speech_queue = queue.Queue()
        self.running = True

        # Callbacks for GUI / visual feedback
        self.on_start_speaking: Optional[Callable[[str], None]] = None
        self.on_finish_speaking: Optional[Callable[[], None]] = None

        self._initialize_engine()

        # Background speech worker thread
        self.worker_thread = threading.Thread(
            target=self._speech_worker,
            name="TTSWorkerThread",
            daemon=True
        )
        self.worker_thread.start()

    def _initialize_engine(self):
        if pyttsx3 is None:
            print("[TTS] pyttsx3 is not installed; TTS will run in simulated console mode.")
            return

        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", self.rate)
            self.engine.setProperty("volume", self.volume)
            self._select_voice()
            print("[TTS] Engine initialized successfully.")
        except Exception as error:
            print(f"[TTS] Initialization failed: {error}")
            self.engine = None

    def _select_voice(self):
        if not self.engine:
            return
        try:
            voices = self.engine.getProperty("voices")
            if not voices:
                return

            selected_voice = None
            target_gender = self.voice_gender.lower()

            for voice in voices:
                name_lower = voice.name.lower()
                if target_gender in name_lower or "female" in name_lower or "zira" in name_lower:
                    selected_voice = voice
                    break

            if selected_voice is None and voices:
                selected_voice = voices[0]

            if selected_voice:
                self.engine.setProperty("voice", selected_voice.id)
        except Exception as e:
            print(f"[TTS] Voice selection error: {e}")

    def speak(self, text: str):
        """Queue text to be spoken asynchronously."""
        if not text:
            return
        clean_text = str(text).strip()
        if not clean_text:
            return
        self.speech_queue.put(clean_text)

    def speak_now(self, text: str):
        """Speak synchronously or bypass queue."""
        if not text:
            return
        clean_text = str(text).strip()
        if not clean_text:
            return

        self.currently_speaking = True
        print(f"[Alicia]: {clean_text}")

        if self.on_start_speaking:
            try:
                self.on_start_speaking(clean_text)
            except Exception:
                pass

        if self.engine:
            try:
                self.engine.say(clean_text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"[TTS] Speech synthesis error: {e}")
        else:
            # Fallback delay to simulate natural reading pace
            time.sleep(min(3.0, max(0.5, len(clean_text) * 0.05)))

        self.currently_speaking = False
        if self.on_finish_speaking:
            try:
                self.on_finish_speaking()
            except Exception:
                pass

    def _speech_worker(self):
        while self.running:
            try:
                text = self.speech_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            try:
                self.speak_now(text)
            finally:
                self.speech_queue.task_done()

    def stop(self):
        """Stop current and queued speech."""
        try:
            if self.engine:
                self.engine.stop()
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
                except queue.Empty:
                    break
            self.currently_speaking = False
        except Exception as e:
            print(f"[TTS] Stop error: {e}")

    def is_speaking(self) -> bool:
        return self.currently_speaking

    def shutdown(self):
        self.running = False
        self.stop()


tts = TextToSpeech()

def speak(text: str):
    tts.speak(text)

def stop_speaking():
    tts.stop()

def is_speaking() -> bool:
    return tts.is_speaking()
