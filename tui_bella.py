import asyncio
import time
from typing import Optional, List
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.text import Text
from rich.status import Status
from rich.prompt import Prompt
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule
import threading


class BellaTUI:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self._setup_layout()
        self.messages = []
        self.current_status = "Ready"

    def _setup_layout(self):
        """Create the main layout structure"""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="status", size=3),
        )

        self.layout["main"].split_row(
            Layout(name="chat", ratio=3),
            Layout(name="sidebar", size=30),
        )

    def _render_header(self) -> Panel:
        """Render the header section"""
        header_text = Text()
        header_text.append("🦙 ", style="bold blue")
        header_text.append("BELLA", style="bold blue")
        header_text.append(" • AI Assistant", style="dim")

        return Panel(Align.center(header_text), style="blue", border_style="blue")

    def _render_chat(self) -> Panel:
        """Render the chat area with messages"""
        if not self.messages:
            chat_content = Text("Start a conversation...\n\n", style="dim")
            chat_content.append("💡 Tips:\n", style="yellow")
            chat_content.append("• Use Ctrl+C to exit\n", style="cyan")
            chat_content.append("• Try 'help' for commands\n", style="cyan")
            chat_content.append("• Tools: file ops, web, shell\n", style="cyan")
        else:
            chat_content = Text()
            for msg in self.messages[-10:]:  # Show last 10 messages
                if msg["role"] == "user":
                    chat_content.append("👤 You: ", style="bold green")
                    chat_content.append(msg["content"] + "\n\n")
                else:
                    chat_content.append("🦙 Bella: ", style="bold blue")
                    chat_content.append(msg["content"] + "\n\n")

        return Panel(chat_content, title="Chat", border_style="green", padding=(1, 2))

    def _render_sidebar(self) -> Panel:
        """Render the sidebar with status and tools"""
        # Status section
        status_table = Table(show_header=False, box=None)
        status_table.add_column("Key", style="cyan")
        status_table.add_column("Value", style="white")

        status_table.add_row("Status", self.current_status)
        status_table.add_row("Model", "Llama 3.2")
        status_table.add_row("Messages", str(len(self.messages)))

        # Tools section
        tools_table = Table(title="Tools", show_header=True, box=None)
        tools_table.add_column("Tool", style="yellow")
        tools_table.add_column("Status", style="green")

        tools = [
            "read_file",
            "write_file",
            "web_fetch",
            "web_search",
            "shell_cmd",
            "list_dir",
        ]
        for tool in tools:
            tools_table.add_row(f"• {tool}", "✓")

        sidebar_content = Columns(
            [
                Panel(status_table, title="Status", border_style="cyan"),
                Panel(tools_table, title="Tools", border_style="yellow"),
            ]
        )

        return Panel(sidebar_content, title="Info", border_style="blue")

    def _render_status_bar(self) -> Panel:
        """Render the status bar"""
        status_text = Text()
        status_text.append(f"📊 {self.current_status} | ", style="green")
        status_text.append(f"🕐 {time.strftime('%H:%M:%S')} | ", style="cyan")
        status_text.append("Press 'q' to quit | 'c' to clear", style="dim")

        return Panel(Align.center(status_text), style="dim", border_style="dim")

    def _render_full_layout(self):
        """Render the complete layout"""
        self.layout["header"].update(self._render_header())
        self.layout["chat"].update(self._render_chat())
        self.layout["sidebar"].update(self._render_sidebar())
        self.layout["status"].update(self._render_status_bar())

        return self.layout

    def add_message(self, role: str, content: str):
        """Add a message to the chat"""
        self.messages.append({"role": role, "content": content})

    def set_status(self, status: str):
        """Update the current status"""
        self.current_status = status

    def show_loading(self, message: str = "Thinking..."):
        """Show a loading spinner"""
        with self.console.status(
            f"[bold blue]{message}[/bold blue]", spinner="dots"
        ) as status:
            yield status

    def show_progress(self, task_name: str, steps: List[str]):
        """Show progress bar for multi-step operations"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task(task_name, total=len(steps))
            for step in steps:
                progress.update(task, description=step)
                time.sleep(0.5)
                progress.advance(task)

    def get_user_input(self) -> str:
        """Get user input with prompt"""
        return Prompt.ask("\n[bold green]👤 You[/bold green]", default="")

    def run_interactive(self):
        """Run the interactive TUI"""
        self.console.clear()

        try:
            while True:
                # Render the UI
                with Live(
                    self._render_full_layout(), refresh_per_second=4, screen=True
                ) as live:
                    # Get user input (this is a simplified version)
                    user_input = self.get_user_input()

                    if user_input.lower() == "q":
                        self.console.print("[bold red]Goodbye! 👋[/bold red]")
                        break
                    elif user_input.lower() == "c":
                        self.messages.clear()
                        self.console.print("[bold yellow]Chat cleared![/bold yellow]")
                        continue
                    elif user_input.lower() == "help":
                        self._show_help()
                        continue

                    if not user_input.strip():
                        continue

                    # Add user message
                    self.add_message("user", user_input)

                    # Simulate AI response (in real version, this would call the AI)
                    self.set_status("Processing...")
                    self.add_message(
                        "assistant", f"I understand you said: '{user_input}'"
                    )
                    self.set_status("Ready")

        except KeyboardInterrupt:
            self.console.print("\n[bold red]Interrupted. Goodbye! 👋[/bold red]")

    def _show_help(self):
        """Show help information"""
        help_text = Text()
        help_text.append("🦙 BELLA HELP\n\n", style="bold blue")
        help_text.append("Commands:\n", style="yellow")
        help_text.append("• help - Show this help\n", style="cyan")
        help_text.append("• clear/c - Clear chat history\n", style="cyan")
        help_text.append("• quit/q - Exit the application\n\n", style="cyan")
        help_text.append("Tools Available:\n", style="yellow")
        help_text.append("• File operations (read, write, list)\n", style="cyan")
        help_text.append("• Web operations (fetch, search)\n", style="cyan")
        help_text.append("• Shell commands (run any command)\n", style="cyan")

        self.console.print(Panel(help_text, title="Help", border_style="yellow"))


if __name__ == "__main__":
    tui = BellaTUI()
    tui.run_interactive()
