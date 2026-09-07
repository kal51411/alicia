"""
Alicia Vision & Multimodal Logic
Analyzes screen captures and images using Gemini Multimodal Vision.
"""

from pathlib import Path
from typing import Optional, Union
from PIL import Image

from src.core.cmd.system import system
from src.core.logic.model import gemini_model


class VisionAnalyzer:
    """Provides computer vision and screen understanding capabilities."""

    def __init__(self, model_instance=None):
        self.model = model_instance or gemini_model

    def analyze_image(
        self,
        image_path_or_obj: Union[str, Path, Image.Image],
        prompt: str = "Describe what you see in this image concisely."
    ) -> str:
        """Analyze a given image path or PIL Image using Gemini."""
        if not self.model.is_available() or not self.model.client:
            return "Vision analysis requires Gemini API key. Please configure GEMINI_API_KEY."

        try:
            if isinstance(image_path_or_obj, (str, Path)):
                path = Path(image_path_or_obj)
                if not path.exists():
                    return f"Image not found at {path}"
                img = Image.open(path)
            elif isinstance(image_path_or_obj, Image.Image):
                img = image_path_or_obj
            else:
                return "Invalid image format provided."

            response = self.model.client.models.generate_content(
                model=self.model.model_name,
                contents=[img, prompt]
            )

            if response and response.text:
                return response.text.strip()
            return "No description generated for this image."

        except Exception as e:
            print(f"[Vision] Image analysis error: {e}")
            return f"Failed to analyze image: {e}"

    def inspect_screen(self, query: str = "What is currently visible on my screen? Explain briefly.") -> str:
        """Capture the current screen and ask Gemini to explain it."""
        shot_path = system.take_screenshot()
        if not shot_path or not shot_path.exists():
            return "Failed to take screen capture."

        return self.analyze_image(shot_path, prompt=query)


vision_analyzer = VisionAnalyzer()

def inspect_screen(query: str = "What is on my screen?") -> str:
    return vision_analyzer.inspect_screen(query)
