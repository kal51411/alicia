"""
Alicia Configuration Settings
Handles application settings, API keys, voice preferences, and paths.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

# Base project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

@dataclass
class VoiceSettings:
    wake_words: List[str] = field(default_factory=lambda: ["alicia", "hey alicia", "elicia", "alisa"])
    speech_rate: int = 170
    volume: float = 1.0
    voice_gender: str = "female"
    stt_model: str = "google"  # "google" (fast/online) or "whisper" (offline)
    whisper_model: str = "base"
    sample_rate: int = 16000
    listen_timeout: int = 5
    phrase_time_limit: int = 8
    ambient_noise_duration: float = 0.5

@dataclass
class AISettings:
    model_name: str = "gemini-2.5-flash"
    gemini_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    hf_token: Optional[str] = None
    hf_summarizer_model: str = "facebook/bart-large-cnn"
    max_tokens: int = 1024
    temperature: float = 0.7
    system_instruction: str = (
        "You are Alicia, an intelligent, charming, and highly capable desktop AI assistant. "
        "Your responses should be concise, natural, and friendly when spoken out loud. "
        "Keep answers brief (1-3 sentences) unless the user explicitly requests a detailed explanation."
    )

@dataclass
class UISettings:
    app_name: str = "Alicia AI Assistant"
    window_title: str = "Alicia"
    window_width: int = 420
    window_height: int = 680
    theme: str = "dark_neon"
    always_on_top: bool = False
    start_minimized: bool = False

@dataclass
class Settings:
    voice: VoiceSettings = field(default_factory=VoiceSettings)
    ai: AISettings = field(default_factory=AISettings)
    ui: UISettings = field(default_factory=UISettings)
    root_dir: Path = PROJECT_ROOT
    database_dir: Path = PROJECT_ROOT / "database"
    resources_dir: Path = PROJECT_ROOT / "resources"
    
    def __post_init__(self):
        # Load API keys from environment if available
        self.ai.gemini_api_key = os.getenv("GEMINI_API_KEY") or self._read_key_file("gemini_key.txt")
        self.ai.tavily_api_key = os.getenv("TAVILY_API_KEY") or "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"
        self.ai.hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN") or self._read_key_file("hf_token.txt")

    def _read_key_file(self, filename: str) -> Optional[str]:
        path = self.database_dir / filename
        if path.exists():
            try:
                return path.read_text(encoding="utf-8").strip()
            except Exception:
                return None
        return None

# Global settings instance
settings = Settings()
