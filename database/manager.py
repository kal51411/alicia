"""
Alicia Database Manager
Thread-safe persistent storage manager for memory, application paths, and tracking.
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import settings

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._init_manager()
            return cls._instance

    def _init_manager(self):
        self.db_dir = settings.database_dir
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.memory_path = self.db_dir / "memory.json"
        self.path_config_path = self.db_dir / "path.json"
        self.tracking_path = self.db_dir / "tracking.json"
        self.file_lock = threading.RLock()

    def _read_json(self, path: Path, default: Dict) -> Dict:
        with self.file_lock:
            if not path.exists():
                self._write_json(path, default)
                return default
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[DB] Error reading {path.name}: {e}")
                return default

    def _write_json(self, path: Path, data: Any) -> bool:
        with self.file_lock:
            try:
                tmp_path = path.with_suffix(".tmp")
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                tmp_path.replace(path)
                return True
            except Exception as e:
                print(f"[DB] Error writing {path.name}: {e}")
                return False

    # -------------------------------------------------------------
    # MEMORY & NOTES
    # -------------------------------------------------------------
    def get_memory(self) -> Dict:
        default = {"user_profile": {"name": "Kalpesh"}, "facts": {}, "notes": []}
        return self._read_json(self.memory_path, default)

    def save_memory(self, memory_data: Dict) -> bool:
        return self._write_json(self.memory_path, memory_data)

    def add_note(self, content: str) -> str:
        with self.file_lock:
            data = self.get_memory()
            notes = data.setdefault("notes", [])
            note = {
                "id": len(notes) + 1,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "content": content
            }
            notes.append(note)
            self.save_memory(data)
            return f"Note #{note['id']} saved."

    def list_notes(self) -> List[Dict]:
        return self.get_memory().get("notes", [])

    def get_user_name(self) -> str:
        memory = self.get_memory()
        return memory.get("user_profile", {}).get("name", "Kalpesh")

    # -------------------------------------------------------------
    # PATHS
    # -------------------------------------------------------------
    def get_paths(self) -> Dict:
        return self._read_json(self.path_config_path, {})

    # -------------------------------------------------------------
    # TRACKING & TELEMETRY
    # -------------------------------------------------------------
    def log_command(self, command: str, success: bool = True):
        with self.file_lock:
            data = self._read_json(self.tracking_path, {"total_commands": 0, "command_history": []})
            data["total_commands"] = data.get("total_commands", 0) + 1
            data["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history = data.setdefault("command_history", [])
            history.append({
                "command": command,
                "timestamp": data["last_active"],
                "success": success
            })
            if len(history) > 100:
                history.pop(0)
            self._write_json(self.tracking_path, data)

db = DatabaseManager()
