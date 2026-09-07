"""
Alicia Gemini AI Logic Model
Wraps Google GenAI SDK for conversational intelligence, instruction following, and chat memory.
"""

import os
from typing import Optional, Dict, Any

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from config.settings import settings


class GeminiModel:
    """Provides LLM conversational capability using Google Gemini."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        system_instruction: Optional[str] = None
    ):
        self.model_name = model_name or settings.ai.model_name
        self.api_key = api_key or settings.ai.gemini_api_key
        self.system_instruction = system_instruction or settings.ai.system_instruction

        self.client: Optional[genai.Client] = None
        self.chat = None

        self._initialize_client()

    def _initialize_client(self):
        if not genai or not self.api_key:
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            config = types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=settings.ai.temperature,
                max_output_tokens=settings.ai.max_tokens
            )
            self.chat = self.client.chats.create(
                model=self.model_name,
                config=config
            )
            print(f"[Model] Gemini initialized with {self.model_name}")
        except Exception as e:
            print(f"[Model] Gemini initialization failed: {e}")
            self.client = None
            self.chat = None

    def is_available(self) -> bool:
        return self.client is not None and self.chat is not None

    def ask(self, message: str) -> str:
        """Send message to Gemini and return concise conversational response."""
        if not message:
            return ""

        clean_message = str(message).strip()
        if not clean_message:
            return ""

        if not self.is_available():
            # Try to reinitialize in case key was updated
            if settings.ai.gemini_api_key and not self.api_key:
                self.api_key = settings.ai.gemini_api_key
                self._initialize_client()

            if not self.is_available():
                return "Gemini API key is not configured. Please set GEMINI_API_KEY to enable conversational AI."

        try:
            response = self.chat.send_message(clean_message)
            if response and response.text:
                return response.text.strip()
            return "I didn't receive a response from the model."
        except Exception as e:
            print(f"[Model] Gemini query error: {e}")
            return f"I ran into an issue connecting with Gemini: {e}"

    def reset(self):
        """Reset conversation session."""
        if self.client:
            try:
                config = types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=settings.ai.temperature
                )
                self.chat = self.client.chats.create(
                    model=self.model_name,
                    config=config
                )
                print("[Model] Conversation history reset.")
            except Exception as e:
                print(f"[Model] Reset error: {e}")

    def info(self) -> Dict[str, Any]:
        return {
            "provider": "Google Gemini",
            "model": self.model_name,
            "available": self.is_available()
        }


# Global instance
gemini_model = GeminiModel()