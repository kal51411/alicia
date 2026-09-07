"""
Cross-platform System Utility
Provides operating system abstractions for application launching, system controls, and desktop actions.
"""

import os
import platform
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional, List

OS_SYSTEM = platform.system().lower()  # 'linux', 'windows', 'darwin'

def get_os_name() -> str:
    return OS_SYSTEM

def is_linux() -> bool:
    return OS_SYSTEM == "linux"

def is_windows() -> bool:
    return OS_SYSTEM == "windows"

def is_macos() -> bool:
    return OS_SYSTEM == "darwin"

def open_url(url: str) -> bool:
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"[Platform] Failed to open URL {url}: {e}")
        return False

def open_file_explorer(target_path: Optional[str] = None) -> bool:
    path = target_path or str(Path.home())
    try:
        if is_windows():
            os.startfile(path)
        elif is_macos():
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception as e:
        print(f"[Platform] Failed to open file explorer: {e}")
        return False

def open_terminal() -> bool:
    try:
        if is_windows():
            subprocess.Popen(["start", "cmd"], shell=True)
        elif is_macos():
            subprocess.Popen(["open", "-a", "Terminal"])
        else:
            terminals = ["x-terminal-emulator", "gnome-terminal", "konsole", "xfce4-terminal", "alacritty", "kitty", "xterm"]
            for term in terminals:
                if shutil.which(term):
                    subprocess.Popen([term])
                    return True
            subprocess.Popen(["xterm"])
        return True
    except Exception as e:
        print(f"[Platform] Failed to open terminal: {e}")
        return False

def open_text_editor(filepath: Optional[str] = None) -> bool:
    try:
        if is_windows():
            cmd = ["notepad.exe"]
            if filepath:
                cmd.append(filepath)
            subprocess.Popen(cmd)
        elif is_macos():
            cmd = ["open", "-a", "TextEdit"]
            if filepath:
                cmd.append(filepath)
            subprocess.Popen(cmd)
        else:
            editors = ["gedit", "kate", "mousepad", "kwrite", "nano", "vi"]
            for ed in editors:
                if shutil.which(ed):
                    cmd = [ed]
                    if filepath:
                        cmd.append(filepath)
                    subprocess.Popen(cmd)
                    return True
            if filepath:
                subprocess.Popen(["xdg-open", filepath])
            else:
                subprocess.Popen(["x-terminal-emulator", "-e", "nano"])
        return True
    except Exception as e:
        print(f"[Platform] Failed to open text editor: {e}")
        return False

def launch_application(app_cmd: str) -> bool:
    """Launch an application or system command asynchronously."""
    try:
        subprocess.Popen(app_cmd, shell=True)
        return True
    except Exception as e:
        print(f"[Platform] Failed to launch application '{app_cmd}': {e}")
        return False

def lock_workstation() -> bool:
    try:
        if is_windows():
            subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
        elif is_macos():
            subprocess.run("pmset displaysleepnow", shell=True)
        else:
            lockers = ["loginctl lock-session", "xdg-screensaver lock", "gnome-screensaver-command -l"]
            for cmd in lockers:
                res = subprocess.run(cmd, shell=True, capture_output=True)
                if res.returncode == 0:
                    return True
        return True
    except Exception as e:
        print(f"[Platform] Lock workstation failed: {e}")
        return False
