"""
Alicia AI Assistant - Main Entry Point
Supports both Desktop GUI and CLI Voice Assistant modes.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from database.manager import db
from src.core.voice.tts import tts, speak
from src.core.voice.stt import stt
from src.core.voice.fuzz import matches_wake_word
from src.core.cmd.action import execute_command


def run_cli_mode():
    """Interactive CLI and voice assistant loop."""
    print("=" * 55)
    print("           ALICIA AI DESKTOP ASSISTANT")
    print("=" * 55)
    print("Status   : Online")
    print(f"Wake words: {', '.join(settings.voice.wake_words)}")
    print("Commands : Type a command, press ENTER to speak, or 'exit' to quit.")
    print("-" * 55)

    user_name = db.get_user_name()
    greeting = f"Hello {user_name}! Alicia is online and ready."
    print(f"[Alicia]: {greeting}")
    speak(greeting)

    while True:
        try:
            print("\nOptions: [1] Speak  [2] Type  [3] Exit")
            choice = input("Enter choice (default=2, or type command directly): ").strip()

            if not choice:
                choice = "2"

            if choice.lower() in ["exit", "quit", "q", "stop"]:
                farewell = "Goodbye! Call me whenever you need."
                print(f"[Alicia]: {farewell}")
                speak(farewell)
                break

            command = ""
            if choice == "1":
                print("\n[Listening...] Speak now into your microphone...")
                phrase = stt.listen(timeout=5, phrase_time_limit=8)
                if phrase:
                    print(f"[User Voice]: {phrase}")
                    # Remove wake word if present at start
                    matched, w = matches_wake_word(phrase)
                    if matched:
                        command = phrase.lower().replace(w, "").strip()
                    else:
                        command = phrase
                else:
                    print("[STT]: No speech detected.")
                    continue
            elif choice == "2":
                command = input("\nYou: ").strip()
            else:
                # User typed their command directly into the choice prompt
                command = choice

            if not command:
                continue

            if command.lower() in ["exit", "quit", "stop", "bye"]:
                farewell = "Goodbye! Have a great day."
                print(f"[Alicia]: {farewell}")
                speak(farewell)
                break

            response = execute_command(command)
            print(f"[Alicia]: {response}")
            speak(response)

        except (KeyboardInterrupt, EOFError):
            print("\n[Alicia]: Exiting session. Goodbye!")
            break
        except Exception as e:
            print(f"[Error]: {e}")


def main():
    parser = argparse.ArgumentParser(description="Alicia AI Desktop Assistant")
    parser.add_argument("--gui", action="store_true", help="Run in graphical desktop mode")
    parser.add_argument("--cli", action="store_true", help="Run in terminal CLI mode (default)")
    args = parser.parse_args()

    if args.gui:
        try:
            from src.gui.mainwindow import run_gui
            run_gui()
        except Exception as e:
            print(f"[GUI Notice]: Could not start GUI ({e}). Launching in CLI mode...")
            from src.cli import run_cli
            run_cli()
    else:
        # Default mode: Beautiful rich terminal CLI
        from src.cli import run_cli
        run_cli()


if __name__ == "__main__":
    main()