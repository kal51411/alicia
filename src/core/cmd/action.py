"""
Alicia Action Router & Dispatcher
Parses user intent from text/speech and executes appropriate system, web, memory, or AI actions.
"""

import re
from typing import Dict, Any, Tuple, Optional

from database.manager import db
from src.core.cmd.system import system
from src.core.cmd.search import search_engine
from src.core.utils import crossplatform
from src.core.logic.model import gemini_model
from src.core.logic.vision import vision_analyzer
from src.core.logic.summary import summarizer


class ActionDispatcher:
    """Intelligently routes commands to appropriate modules."""

    def __init__(self, ai_model=None):
        self.ai_model = ai_model or gemini_model


    def set_ai_model(self, model):
        self.ai_model = model

    def execute(self, text: str) -> str:
        """Process user command string and return assistant response."""
        command = text.strip()
        if not command:
            return ""

        clean_cmd = command.lower()
        response = ""
        success = True

        try:
            # 1. TIME & DATE
            if any(k in clean_cmd for k in ["what time is it", "current time", "tell me the time"]) or clean_cmd == "time":
                response = f"It is currently {system.get_time()}."

            elif any(k in clean_cmd for k in ["what date is it", "current date", "what is today's date", "what day is it"]):
                response = f"Today is {system.get_date()}."

            # 2. HARDWARE & SYSTEM STATUS
            elif "battery" in clean_cmd:
                bat = system.get_battery()
                if bat.get("present"):
                    status = "charging" if bat.get("charging") else "discharging"
                    response = f"Battery is at {bat.get('percent')}%, and is currently {status}."
                else:
                    response = "Battery sensor is not available on this device."

            elif any(k in clean_cmd for k in ["cpu usage", "system usage", "cpu status", "system stats", "hardware status"]):
                cpu = system.cpu_usage(interval=0.2)
                ram = system.ram_usage()
                response = f"CPU usage is {cpu}%, and RAM usage is {ram.get('percent')}% ({ram.get('used_gb')} GB used out of {ram.get('total_gb')} GB)."

            elif "ram usage" in clean_cmd or "memory usage" in clean_cmd:
                ram = system.ram_usage()
                response = f"RAM usage is {ram.get('percent')}%. Using {ram.get('used_gb')} GB out of {ram.get('total_gb')} GB."

            elif "uptime" in clean_cmd:
                response = f"System uptime is {system.uptime()}."

            # 3. SCREENSHOT, VISION & LOCK
            elif any(k in clean_cmd for k in ["what is on my screen", "what's on my screen", "look at my screen", "inspect screen"]):
                response = vision_analyzer.inspect_screen(command)

            elif any(k in clean_cmd for k in ["take screenshot", "capture screen", "screenshot"]):
                shot_path = system.take_screenshot()
                if shot_path:
                    response = f"Screenshot saved successfully at {shot_path.name}."
                else:
                    response = "Could not capture screenshot."

            elif any(k in clean_cmd for k in ["lock screen", "lock computer", "lock pc"]):
                system.lock_screen()
                response = "Computer locked."

            # 4. NOTES & REMINDERS
            elif clean_cmd.startswith("take note") or clean_cmd.startswith("write note") or clean_cmd.startswith("save note"):
                note_text = re.sub(r"^(take|write|save)\s+note\s*(that|about|to|:)?\s*", "", command, flags=re.IGNORECASE).strip()
                if note_text:
                    res = db.add_note(note_text)
                    response = f"Got it. {res}"
                else:
                    response = "What note would you like me to write?"

            elif any(k in clean_cmd for k in ["show notes", "read notes", "list notes", "my notes"]):
                notes = db.list_notes()
                if not notes:
                    response = "You don't have any notes saved yet."
                else:
                    last_notes = notes[-3:]
                    summary_list = [f"Note {n['id']}: {n['content']}" for n in last_notes]
                    response = f"Here are your latest notes: {'; '.join(summary_list)}"

            elif any(k in clean_cmd for k in ["summarize notes", "summarize note", "summary of notes"]):
                notes = db.list_notes()
                if not notes:
                    response = "You don't have any notes to summarize."
                else:
                    all_text = " ".join([n["content"] for n in notes])
                    summary = summarizer.summarize(all_text, max_sentences=2)
                    response = f"Summary of your notes: {summary}"

            elif clean_cmd.startswith("summarize ") or clean_cmd.startswith("summary of "):
                text_to_summarize = re.sub(r"^(summarize|summary\s+of)\s*", "", command, flags=re.IGNORECASE).strip()
                summary = summarizer.summarize(text_to_summarize, max_sentences=2)
                response = f"Summary: {summary}"

            # 5. WEBSITES & APP LAUNCHING
            elif "open youtube" in clean_cmd:
                crossplatform.open_url("https://www.youtube.com")
                response = "Opening YouTube."

            elif "open google" in clean_cmd:
                crossplatform.open_url("https://www.google.com")
                response = "Opening Google."

            elif "open github" in clean_cmd:
                crossplatform.open_url("https://www.github.com")
                response = "Opening GitHub."

            elif clean_cmd.startswith("open website ") or clean_cmd.startswith("open url "):
                target_url = command.split(" ", 2)[-1].strip()
                if not target_url.startswith("http"):
                    target_url = "https://" + target_url
                crossplatform.open_url(target_url)
                response = f"Opening {target_url}."

            elif "open notepad" in clean_cmd or "open text editor" in clean_cmd:
                crossplatform.open_text_editor()
                response = "Opening text editor."

            elif "open terminal" in clean_cmd or "open command prompt" in clean_cmd:
                crossplatform.open_terminal()
                response = "Opening terminal."

            elif "open file" in clean_cmd or "open files" in clean_cmd or "open explorer" in clean_cmd:
                crossplatform.open_file_explorer()
                response = "Opening file manager."

            elif clean_cmd.startswith("open "):
                app_target = clean_cmd.replace("open ", "").strip()
                crossplatform.launch_application(app_target)
                response = f"Attempting to launch {app_target}."

            elif clean_cmd.startswith("close ") or clean_cmd.startswith("kill "):
                target = clean_cmd.split(" ", 1)[-1].strip()
                response = system.kill_process(target)

            # 6. WEB SEARCH DIRECT COMMAND
            elif clean_cmd.startswith("search for ") or clean_cmd.startswith("search "):
                query = re.sub(r"^search\s*(for)?\s*", "", command, flags=re.IGNORECASE).strip()
                response = search_engine.search(query)

            # 7. AI & CONVERSATION
            elif self.ai_model and self.ai_model.is_available():
                response = self.ai_model.ask(command)

            # Fallback when AI is unavailable
            elif any(clean_cmd.startswith(w) for w in ["who is", "what is", "where is", "how to"]):
                response = search_engine.search(command)

            elif any(g in clean_cmd for g in ["hello", "hi alicia", "hey alicia", "good morning", "good evening"]):
                user_name = db.get_user_name()
                response = f"Hello {user_name}! How can I assist you today?"

            elif "who are you" in clean_cmd:
                response = "I am Alicia, your personal AI desktop companion."

            else:
                response = "I heard you, but I'm not sure how to handle that command yet. Ask me for system info, notes, web search, or applications."

        except Exception as e:
            response = f"An error occurred while executing that command: {e}"
            success = False

        # Log command execution
        db.log_command(command, success=success)
        return response


action_dispatcher = ActionDispatcher()

def execute_command(command: str) -> str:
    return action_dispatcher.execute(command)
