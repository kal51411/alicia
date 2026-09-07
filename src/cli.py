"""
Alicia Modern Terminal CLI Interface
Rich-powered, beautiful command-line interface for the Alicia AI Assistant.
"""

import sys
import time
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich.layout import Layout
from rich.markdown import Markdown

from config.settings import settings
from database.manager import db
from src.core.cmd.system import system
from src.core.cmd.action import execute_command
from src.core.voice.tts import speak, stop_speaking, is_speaking
from src.core.voice.stt import stt
from src.core.voice.fuzz import matches_wake_word
from src.core.logic.summary import summarizer

console = Console()


class AliciaCLI:
    """Rich interactive terminal assistant."""

    def __init__(self):
        self.console = console
        self.voice_feedback = True
        self.user_name = db.get_user_name()

    def print_banner(self):
        """Render stylish cyberpunk terminal banner."""
        cpu = system.cpu_usage(interval=0.1)
        ram = system.ram_usage()
        uptime_str = system.uptime()

        header_text = Text()
        header_text.append("⚡ ALICIA AI DESKTOP ASSISTANT ⚡\n", style="bold cyan")
        header_text.append(f"Operator: {self.user_name}  |  Status: ONLINE  |  Voice: {'ON' if self.voice_feedback else 'OFF'}\n", style="dim white")
        header_text.append(f"CPU: {cpu}%  |  RAM: {ram.get('percent', 0)}%  |  Uptime: {uptime_str}", style="bold green")

        panel = Panel(
            header_text,
            subtitle="[dim]Type [bold cyan]'help'[/bold cyan] for commands, [bold cyan]'mic'[/bold cyan] to speak, or [bold cyan]'exit'[/bold cyan] to quit[/dim]",
            border_style="bright_blue",
            padding=(1, 2)
        )
        self.console.print(panel)

    def show_help(self):
        """Display table of available terminal commands."""
        table = Table(title="✨ Alicia Available Commands", border_style="cyan", title_style="bold magenta")
        table.add_column("Category", style="bold cyan", no_wrap=True)
        table.add_column("Example Commands", style="white")
        table.add_column("Description", style="dim")

        table.add_row("🎙️ Voice", "mic, listen", "Listen to microphone input")
        table.add_row("🔊 Audio", "voice on, voice off", "Toggle spoken voice replies")
        table.add_row("📝 Summarizer", "summarize <text>, summarize notes", "Pretrained text summarization")
        table.add_row("⚙️ System", "status, cpu, ram, battery, uptime", "Check hardware metrics")
        table.add_row("📌 Notes", "take note <text>, show notes", "Persistent notes management")
        table.add_row("🔍 Search", "search <query>, who is <person>", "Multi-engine web search")
        table.add_row("🚀 Apps", "open <app>, open youtube, open files", "Launch applications & links")
        table.add_row("🖥️ Control", "screenshot, lock screen", "Take screen captures or lock")
        table.add_row("🧹 Terminal", "clear, help, exit", "Manage CLI session")

        self.console.print(table)

    def show_status(self):
        """Display detailed system diagnostics."""
        cpu = system.cpu_usage(interval=0.2)
        ram = system.ram_usage()
        bat = system.get_battery()

        table = Table(title="📊 Alicia System Diagnostics", border_style="green")
        table.add_column("Metric", style="bold cyan")
        table.add_column("Value", style="bold white")

        table.add_row("OS Version", system.os_version())
        table.add_row("Host Name", system.computer_name())
        table.add_row("Uptime", system.uptime())
        table.add_row("CPU Usage", f"{cpu}%")
        table.add_row("RAM Usage", f"{ram.get('percent')}% ({ram.get('used_gb')} / {ram.get('total_gb')} GB)")

        if bat.get("present"):
            status = "Charging ⚡" if bat.get("charging") else "Battery"
            bat_pct = int(bat.get("percent", 100))
            table.add_row("Battery", f"{bat_pct}% ({status})")
        else:
            table.add_row("Battery", "AC Power / Not Detected")

        self.console.print(table)

    def listen_voice(self):
        """Listen from microphone and transcribe."""
        self.console.print("\n[bold cyan]🎙️ Listening...[/bold cyan] [green](Speak clearly into your microphone now)[/green]")
        phrase = stt.listen(timeout=6, phrase_time_limit=10)
        if phrase:
            self.console.print(f"[bold yellow]🎤 You (Voice):[/bold yellow] [bold white]{phrase}[/bold white]")
            matched, w = matches_wake_word(phrase)
            if matched:
                cmd = phrase.lower().replace(w, "").strip()
            else:
                cmd = phrase
            if cmd:
                self.process_command(cmd)
            else:
                self.console.print("[dim cyan]Alicia heard the wake word. What would you like to do?[/dim cyan]")
        else:
            self.console.print("[dim yellow]No speech detected or could not transcribe. Tip: speak clearly and check mic volume.[/dim yellow]")

    def process_command(self, command: str):
        """Execute command and render response."""
        cmd = command.strip()
        if not cmd:
            return

        clean = cmd.lower()

        # Built-in CLI commands
        if clean in ["help", "?", "commands"]:
            self.show_help()
            return

        if clean in ["test mic", "mic test", "test microphone"]:
            stt.test_microphone()
            return

        if clean in ["status", "sysinfo", "diagnostics"]:
            self.show_status()
            return

        if clean in ["clear", "cls"]:
            self.console.clear()
            self.print_banner()
            return

        if clean in ["mic", "listen", "speak"]:
            self.listen_voice()
            return

        if clean in ["voice off", "mute"]:
            self.voice_feedback = False
            self.console.print("[dim yellow]Spoken audio feedback turned OFF.[/dim yellow]")
            return

        if clean in ["voice on", "unmute"]:
            self.voice_feedback = True
            self.console.print("[dim green]Spoken audio feedback turned ON.[/dim green]")
            return

        # Action execution
        with self.console.status("[bold cyan]Alicia is thinking...[/bold cyan]", spinner="dots"):
            response = execute_command(cmd)

        # Print stylish response
        panel = Panel(
            Text(response, style="white"),
            title="[bold cyan]Alicia[/bold cyan]",
            border_style="cyan",
            padding=(0, 1)
        )
        self.console.print(panel)

        if self.voice_feedback and response:
            speak(response)

    def start(self):
        """Main CLI loop."""
        self.console.clear()
        self.print_banner()

        welcome_msg = f"Hello {self.user_name}! Alicia CLI is active and ready in your terminal."
        self.console.print(f"\n[bold green]●[/bold green] [dim]{welcome_msg}[/dim]\n")
        if self.voice_feedback:
            speak(welcome_msg)

        while True:
            try:
                user_input = Prompt.ask("[bold cyan]alicia[/bold cyan] [bright_blue]❯[/bright_blue]").strip()
                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit", "q", "bye"]:
                    farewell = "Goodbye! Session terminated."
                    self.console.print(f"\n[bold cyan]Alicia:[/bold cyan] {farewell}")
                    if self.voice_feedback:
                        speak(farewell)
                    break

                self.process_command(user_input)
                self.console.print()  # Spacer line

            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[dim cyan]Session interrupted. Goodbye![/dim cyan]")
                break
            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")


def run_cli():
    cli = AliciaCLI()
    cli.start()


if __name__ == "__main__":
    run_cli()
