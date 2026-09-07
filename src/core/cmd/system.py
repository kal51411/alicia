"""
Alicia System Commands
Provides hardware monitoring, process control, system power controls, and OS interactions.
"""

import datetime
import os
import platform
import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
from PIL import ImageGrab

from src.core.utils import crossplatform
from src.core.utils.crosspath import get_project_root


class SystemManager:
    """Manages system metrics, process management, and OS execution."""

    @staticmethod
    def get_time() -> str:
        return datetime.datetime.now().strftime("%I:%M %p")

    @staticmethod
    def get_date() -> str:
        return datetime.datetime.now().strftime("%A, %B %d, %Y")

    @staticmethod
    def get_datetime_full() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def os_version() -> str:
        return f"{platform.system()} {platform.release()} ({platform.machine()})"

    @staticmethod
    def computer_name() -> str:
        return socket.gethostname()

    @staticmethod
    def uptime() -> str:
        try:
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            delta = datetime.datetime.now() - boot_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours} hours, {minutes} minutes"
        except Exception:
            return "Uptime unavailable"

    @staticmethod
    def cpu_usage(interval: float = 0.5) -> float:
        try:
            return psutil.cpu_percent(interval=interval)
        except Exception:
            return 0.0

    @staticmethod
    def ram_usage() -> Dict[str, Any]:
        try:
            ram = psutil.virtual_memory()
            return {
                "total_gb": round(ram.total / (1024**3), 2),
                "used_gb": round(ram.used / (1024**3), 2),
                "available_gb": round(ram.available / (1024**3), 2),
                "percent": ram.percent
            }
        except Exception as e:
            return {"error": str(e), "percent": 0.0}

    @staticmethod
    def get_battery() -> Dict[str, Any]:
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return {"present": False, "percent": 100, "charging": True}
            return {
                "present": True,
                "percent": battery.percent,
                "charging": battery.power_plugged,
                "seconds_left": battery.secsleft
            }
        except Exception as e:
            return {"present": False, "error": str(e)}

    @staticmethod
    def get_temperatures() -> Dict[str, Any]:
        try:
            if hasattr(psutil, "sensors_temperatures"):
                return psutil.sensors_temperatures()
            return {}
        except Exception:
            return {}

    @staticmethod
    def get_processes(limit: int = 15) -> List[Dict[str, Any]]:
        processes = []
        try:
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            # Sort by memory percent descending
            processes.sort(key=lambda p: p.get("memory_percent") or 0.0, reverse=True)
            return processes[:limit]
        except Exception:
            return []

    @staticmethod
    def is_running(application_name: str) -> bool:
        app_name_lower = application_name.lower()
        for process in psutil.process_iter(["name"]):
            try:
                pname = (process.info.get("name") or "").lower()
                if app_name_lower in pname:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    @staticmethod
    def kill_process(name_or_pid: str) -> str:
        killed = 0
        try:
            if name_or_pid.isdigit():
                pid = int(name_or_pid)
                p = psutil.Process(pid)
                p.terminate()
                return f"Terminated process {pid} ({p.name()})."
            
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    if name_or_pid.lower() in (proc.info.get("name") or "").lower():
                        proc.terminate()
                        killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            if killed > 0:
                return f"Closed {killed} instance(s) of '{name_or_pid}'."
            return f"No process matching '{name_or_pid}' found."
        except Exception as e:
            return f"Failed to terminate process: {e}"

    @staticmethod
    def open_application(application: str) -> str:
        return (
            f"Opened {application}"
            if crossplatform.launch_application(application)
            else f"Could not launch {application}"
        )

    @staticmethod
    def lock_screen() -> str:
        return "Screen locked." if crossplatform.lock_workstation() else "Failed to lock screen."

    @staticmethod
    def shutdown() -> str:
        if crossplatform.is_windows():
            subprocess.Popen(["shutdown", "/s", "/t", "1"])
        else:
            subprocess.Popen(["shutdown", "-h", "now"])
        return "Shutting down the computer."

    @staticmethod
    def restart() -> str:
        if crossplatform.is_windows():
            subprocess.Popen(["shutdown", "/r", "/t", "1"])
        else:
            subprocess.Popen(["reboot"])
        return "Restarting the system."

    @staticmethod
    def take_screenshot(filename: Optional[str] = None) -> Optional[Path]:
        try:
            shots_dir = get_project_root() / "resources" / "pictures"
            shots_dir.mkdir(parents=True, exist_ok=True)
            if not filename:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            target_path = shots_dir / filename
            image = ImageGrab.grab()
            image.save(target_path)
            return target_path
        except Exception as e:
            print(f"[System] Screenshot capture failed: {e}")
            return None


# Module-level helper functions matching user's original intentions
system = SystemManager()

def get_time():
    return system.get_time()

def get_date():
    return system.get_date()

def uptime():
    return system.uptime()

def cpu_usage():
    return system.cpu_usage()

def ram_usage():
    return system.ram_usage()

def get_battery():
    return system.get_battery()

def is_running(application):
    return system.is_running(application)

def open_application(application):
    return system.open_application(application)
