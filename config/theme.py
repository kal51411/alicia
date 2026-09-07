"""
Alicia Theme Configuration
Defines colors, styling tokens, and stylesheet utilities for the GUI.
"""

from pathlib import Path
from typing import Dict

THEMES: Dict[str, Dict[str, str]] = {
    "dark_neon": {
        "bg_primary": "#0e131f",
        "bg_secondary": "#161e2e",
        "bg_card": "#1d283c",
        "bg_input": "#131a29",
        "accent_cyan": "#00f0ff",
        "accent_magenta": "#e040fb",
        "accent_purple": "#7c4dff",
        "accent_green": "#00e676",
        "accent_amber": "#ffab00",
        "accent_red": "#ff5252",
        "text_primary": "#f0f4f8",
        "text_secondary": "#94a3b8",
        "text_dim": "#64748b",
        "border_color": "#283548",
        "border_glow": "#00f0ff88",
    },
    "midnight": {
        "bg_primary": "#090d16",
        "bg_secondary": "#101726",
        "bg_card": "#182236",
        "bg_input": "#0d1424",
        "accent_cyan": "#38bdf8",
        "accent_magenta": "#f43f5e",
        "accent_purple": "#818cf8",
        "accent_green": "#34d399",
        "accent_amber": "#fbbf24",
        "accent_red": "#f87171",
        "text_primary": "#f8fafc",
        "text_secondary": "#cbd5e1",
        "text_dim": "#64748b",
        "border_color": "#1e293b",
        "border_glow": "#38bdf888",
    }
}

def get_theme(name: str = "dark_neon") -> Dict[str, str]:
    return THEMES.get(name, THEMES["dark_neon"])

def load_stylesheet(style_path: Path, theme_name: str = "dark_neon") -> str:
    """Load QSS file and substitute theme variables."""
    if not style_path.exists():
        return ""
    
    content = style_path.read_text(encoding="utf-8")
    theme = get_theme(theme_name)
    for key, val in theme.items():
        content = content.replace(f"@{{{key}}}", val)
        content = content.replace(f"${key}", val)
    return content
