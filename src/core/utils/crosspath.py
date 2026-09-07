"""
Cross-path Utility
Handles robust path resolution across Windows, Linux, and macOS.
"""

import sys
from pathlib import Path

# Compute project root (alicia/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def get_project_root() -> Path:
    return PROJECT_ROOT

def get_database_dir() -> Path:
    p = PROJECT_ROOT / "database"
    p.mkdir(parents=True, exist_ok=True)
    return p

def get_resources_dir() -> Path:
    return PROJECT_ROOT / "resources"

def get_resource_file(category: str, filename: str) -> Path:
    """Return path to a file inside resources/{category}/{filename}."""
    return PROJECT_ROOT / "resources" / category / filename

def get_style_file(filename: str = "main.qss") -> Path:
    return PROJECT_ROOT / "resources" / "style" / filename

def resolve_path(relative_or_absolute: str) -> Path:
    """Safely resolve relative paths to project root or preserve absolute paths."""
    p = Path(relative_or_absolute)
    if p.is_absolute():
        return p.resolve()
    return (PROJECT_ROOT / p).resolve()
