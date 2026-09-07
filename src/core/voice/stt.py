"""
Alicia Speech-to-Text (STT) Engine
Provides resilient microphone capture, dynamic noise clamping, and speech recognition
via Google Speech Recognition and Whisper/Vosk fallbacks.
"""

import os
import sys
import ctypes
import threading
from typing import Optional, Tuple

# Suppress ALSA C-level library warnings on Linux
try:
    asound = ctypes.cdll.LoadLibrary("libasound.so.2")
    ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(
        None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p
    )
    def _py_alsa_err_handler(filename, line, function, err, fmt):
        pass
    _c_alsa_err_handler = ERROR_HANDLER_FUNC(_py_alsa_err_handler)
    asound.snd_lib_error_set_handler(_c_alsa_err_handler)
except Exception:
    pass

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import whisper
except ImportError:
    whisper = None

from config.settings import settings


class SpeechToText:
    """Multi-engine Speech-to-Text with adaptive sensitivity and clipping protection."""

    def __init__(
        self,
        engine: str = "google",
        whisper_model: str = "base",
        default_energy_threshold: int = 600
    ):
        self.engine_name = engine
        self.whisper_model_name = whisper_model
        self.whisper_model = None
        self.recognizer: Optional[sr.Recognizer] = None
        self.microphone: Optional[sr.Microphone] = None
        self.is_listening = False
        self._calibrated = False
        self._lock = threading.Lock()
        self.default_energy_threshold = default_energy_threshold

        self._init_engine()

    def _init_engine(self):
        if sr is None:
            print("[STT] speech_recognition library not found.")
            return

        try:
            self.recognizer = sr.Recognizer()
            # Set balanced sensitivity
            self.recognizer.energy_threshold = self.default_energy_threshold
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.dynamic_energy_adjustment_damping = 0.15
            self.recognizer.dynamic_energy_ratio = 1.5
            self.recognizer.pause_threshold = 0.8
            self.recognizer.non_speaking_duration = 0.5

            # Let PyAudio use native hardware rate to avoid ALSA channel-map corruption
            self.microphone = sr.Microphone()
            print("[STT] Microphone & Recognizer initialized.")
        except Exception as e:
            print(f"[STT] Microphone initialization error: {e}")

    def calibrate(self, duration: float = 0.5):
        """Calibrate ambient noise once and clamp threshold within sane bounds."""
        if not self.recognizer or not self.microphone:
            return

        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                # Clamp between 300 (very sensitive) and 2500 (loud room)
                clamped = min(max(self.recognizer.energy_threshold, 350), 2200)
                self.recognizer.energy_threshold = clamped
                self._calibrated = True
                print(f"[STT] Calibrated energy threshold: {self.recognizer.energy_threshold:.0f}")
        except Exception as e:
            print(f"[STT] Calibration notice: {e}")
            self.recognizer.energy_threshold = self.default_energy_threshold

    def listen(
        self,
        timeout: Optional[int] = None,
        phrase_time_limit: Optional[int] = None
    ) -> str:
        """
        Listen to microphone and return transcribed text.
        """
        if self.recognizer is None or self.microphone is None:
            print("[STT] Recognizer or microphone not available.")
            return ""

        t_out = timeout or settings.voice.listen_timeout
        p_limit = phrase_time_limit or settings.voice.phrase_time_limit

        # Calibrate once on initial use
        if not self._calibrated:
            self.calibrate(duration=0.3)

        self.is_listening = True
        try:
            with self.microphone as source:
                print(f"[STT] Listening... (Threshold: {int(self.recognizer.energy_threshold)})")
                audio = self.recognizer.listen(
                    source,
                    timeout=t_out,
                    phrase_time_limit=p_limit
                )

            print("[STT] Audio captured. Transcribing...")

            # 1. Whisper Engine if requested
            if self.engine_name == "whisper" and whisper is not None:
                self._load_whisper_if_needed()
                if self.whisper_model:
                    import numpy as np
                    raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
                    audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                    res = self.whisper_model.transcribe(audio_np, language="en", fp16=False)
                    text = res.get("text", "").strip()
                    return text

            # 2. Google Speech Recognition (Default)
            text = self.recognizer.recognize_google(audio).strip()
            return text

        except sr.WaitTimeoutError:
            # Silence timeout
            return ""
        except sr.UnknownValueError:
            print("[STT] Sound detected but could not discern words clearly.")
            return ""
        except sr.RequestError as e:
            print(f"[STT] Recognition service connection error: {e}")
            return ""
        except Exception as e:
            print(f"[STT] Listening error: {e}")
            return ""
        finally:
            self.is_listening = False

    def _load_whisper_if_needed(self):
        if self.whisper_model is None and whisper is not None:
            with self._lock:
                if self.whisper_model is None:
                    try:
                        self.whisper_model = whisper.load_model(self.whisper_model_name)
                    except Exception as e:
                        print(f"[STT] Whisper load failed: {e}")

    def test_microphone(self) -> bool:
        """Self-diagnostic test of microphone recording and recognition."""
        print("=" * 50)
        print("          ALICIA MICROPHONE DIAGNOSTIC")
        print("=" * 50)
        if not self.microphone:
            print("[FAIL] Microphone not detected!")
            return False

        print(f"Sample Rate     : {self.microphone.SAMPLE_RATE or 'Native'}")
        print(f"Sample Width    : {self.microphone.SAMPLE_WIDTH or 'Native'}")
        self.calibrate(duration=0.5)
        print(f"Energy Threshold: {self.recognizer.energy_threshold:.0f}")

        print("\nSay something into the microphone now (testing for 5 seconds)...")
        res = self.listen(timeout=5, phrase_time_limit=7)
        if res:
            print(f"[SUCCESS] Recognized: '{res}'")
            return True
        else:
            print("[NOTICE] No speech transcribed. If you spoke, please ensure your microphone volume is unmuted in system settings.")
            return False

    def stop_listening(self):
        self.is_listening = False


stt = SpeechToText()

def listen(timeout: int = 6, phrase_time_limit: int = 8) -> str:
    return stt.listen(timeout=timeout, phrase_time_limit=phrase_time_limit)


if __name__ == "__main__":
    stt.test_microphone()