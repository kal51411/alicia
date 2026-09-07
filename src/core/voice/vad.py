"""
Alicia Voice Activity Detector (VAD)
Detects human speech and silence in audio frames to optimize recording and listening windows.
"""

import math
import numpy as np
from typing import Union


class VoiceActivityDetector:
    """Detects voice activity using energy (RMS) thresholding and dynamic noise floor calibration."""

    def __init__(
        self,
        energy_threshold: float = 0.015,
        sample_rate: int = 16000,
        silence_limit_sec: float = 1.2
    ):
        self.energy_threshold = energy_threshold
        self.sample_rate = sample_rate
        self.silence_limit_sec = silence_limit_sec
        self.noise_floor = 0.005

    def calculate_rms(self, audio_data: Union[np.ndarray, bytes]) -> float:
        """Calculate Root Mean Square energy of audio frame."""
        try:
            if isinstance(audio_data, bytes):
                data = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            elif isinstance(audio_data, np.ndarray):
                data = audio_data.flatten()
                if data.dtype != np.float32:
                    data = data.astype(np.float32)
            else:
                return 0.0

            if len(data) == 0:
                return 0.0

            rms = float(np.sqrt(np.mean(data**2)))
            return rms
        except Exception:
            return 0.0

    def is_speech(self, audio_frame: Union[np.ndarray, bytes]) -> bool:
        """Return True if current frame contains voice energy above threshold."""
        rms = self.calculate_rms(audio_frame)
        # Adaptively track noise floor
        if rms < self.energy_threshold:
            self.noise_floor = 0.95 * self.noise_floor + 0.05 * rms
        return rms > max(self.energy_threshold, self.noise_floor * 2.5)

    def calibrate(self, ambient_audio: np.ndarray):
        """Calibrate noise floor based on ambient sample."""
        rms = self.calculate_rms(ambient_audio)
        self.noise_floor = rms
        self.energy_threshold = max(0.01, rms * 1.8)
        print(f"[VAD] Calibrated threshold: {self.energy_threshold:.4f}, noise floor: {self.noise_floor:.4f}")


vad = VoiceActivityDetector()
