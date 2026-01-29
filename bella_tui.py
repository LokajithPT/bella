import asyncio
import time
import threading
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
from rich.markdown import Markdown

# Import existing functionality
from chatter import (
    ask_ollama,
    chat_history,
    OLLAMA_MODEL,
    AVAILABLE_TOOLS,
    _execute_tool_call,
)


class BellaTUI:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self._setup_layout()
        self.messages = []
        self.current_status = "Ready"
        self.is_processing = False

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
        if not self.messages and not chat_history[1:]:  # Skip system prompt
            chat_content = Text("Start a conversation...\n\n", style="dim")
            chat_content.append("💡 Tips:\n", style="yellow")
            chat_content.append("• Use Ctrl+C to exit\n", style="cyan")
            chat_content.append("• Try 'help' for commands\n", style="cyan")
            chat_content.append("• Tools: file ops, web, shell\n", style="cyan")
        else:
            chat_content = Text()

            # Show recent messages from chat_history
            recent_history = chat_history[-15:]  # Show last 15 messages
            for msg in recent_history:
                if msg["role"] == "user":
                    chat_content.append("👤 You: ", style="bold green")
                    chat_content.append(msg["content"] + "\n\n")
                elif msg["role"] == "assistant":
                    # Show assistant response with better formatting
                    content = msg["content"]
                    if len(content) > 300:
                        content = content[:300] + "..."
                    chat_content.append("🦙 Bella: ", style="bold blue")
                    chat_content.append(content + "\n\n")
                elif msg["role"] == "tool":
                    chat_content.append("🔧 Tool: ", style="bold yellow")
                    chat_content.append(
                        f"{msg['tool_call_id']} - {len(str(msg['content']))} chars\n\n"
                    )

        return Panel(chat_content, title="Chat", border_style="green", padding=(1, 2))

    def _render_sidebar(self) -> Panel:
        """Render the sidebar with status and tools"""
        # Status section
        status_table = Table(show_header=False, box=None)
        status_table.add_column("Key", style="cyan")
        status_table.add_column("Value", style="white")

        status_table.add_row("Status", self.current_status)
        status_table.add_row(
            "Model",
            OLLAMA_MODEL.split("/")[-1] if "/" in OLLAMA_MODEL else OLLAMA_MODEL,
        )
        status_table.add_row(
            "Messages",
            str(len([m for m in chat_history if m["role"] in ["user", "assistant"]])),
        )

        # Tools section
        tools_table = Table(title="Tools", show_header=True, box=None)
        tools_table.add_column("Tool", style="yellow")
        tools_table.add_column("Status", style="green")

        tool_names = list(AVAILABLE_TOOLS.keys())
        for i, tool in enumerate(tool_names[:6]):  # Show first 6 tools
            tools_table.add_row(f"• {tool.replace('_tool', '')}", "✓")

        if len(tool_names) > 6:
            tools_table.add_row(f"... +{len(tool_names) - 6} more", "✓")

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
        status_text.append("Ctrl+C to exit | Type 'help'", style="dim")

        if self.is_processing:
            status_text.append(" | ", style="dim")
            status_text.append("⚡ Processing...", style="yellow animate")

        return Panel(Align.center(status_text), style="dim", border_style="dim")

    def _render_full_layout(self):
        """Render the complete layout"""
        self.layout["header"].update(self._render_header())
        self.layout["chat"].update(self._render_chat())
        self.layout["sidebar"].update(self._render_sidebar())
        self.layout["status"].update(self._render_status_bar())

        return self.layout

    def add_message(self, role: str, content: str):
        """Add a message to the chat (for demo purposes)"""
        self.messages.append({"role": role, "content": content})

    def set_status(self, status: str):
        """Update the current status"""
        self.current_status = status

    def show_progress(self, task_name: str, steps: List[str]):
        """Show progress bar for multi-step operations"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:
            task = progress.add_task(task_name, total=len(steps))
            for step in steps:
                progress.update(task, description=step)
                time.sleep(0.3)
                progress.advance(task)

    def show_processing_spinner(self, message: str = "Thinking..."):
        """Show a processing spinner"""
        return Status(
            f"[bold blue]{message}[/bold blue]", spinner="dots12", console=self.console
        )

    def process_user_input(self, user_input: str) -> str:
        """Process user input through the AI pipeline"""
        if self.is_processing:
            return "Already processing..."

        self.is_processing = True
        self.set_status("Processing...")

        try:
            # Show progress for AI thinking
            with self.show_processing_spinner("Bella is thinking..."):
                start_time = time.time()
                response = ask_ollama(user_input)
                end_time = time.time()
                response_time = end_time - start_time

            self.set_status(f"Ready ({response_time:.2f}s)")
            return response

        except Exception as e:
            self.set_status("Error")
            return f"Error: {e}"
        finally:
            self.is_processing = False

    def get_user_input_non_blocking(self) -> Optional[str]:
        """Get user input in a non-blocking way (simplified)"""
        try:
            user_input = Prompt.ask(
                "\n[bold green]👤 You[/bold green]",
                default="",
                show_default=False,
                console=self.console,
            )
            return user_input
        except (KeyboardInterrupt, EOFError):
            return None

    def _show_help(self):
        """Show help information"""
        help_text = Text()
        help_text.append("🦙 BELLA HELP\n\n", style="bold blue")
        help_text.append("Commands:\n", style="yellow")
        help_text.append("• help - Show this help\n", style="cyan")
        help_text.append("• clear - Clear chat history\n", style="cyan")
        help_text.append("• Ctrl+C - Exit the application\n\n", style="cyan")
        help_text.append("Available Tools:\n", style="yellow")
        help_text.append("• File: read, write, list, search\n", style="cyan")
        help_text.append("• Web: fetch URLs, search web\n", style="cyan")
        help_text.append("• Shell: run any command\n", style="cyan")
        help_text.append("• Git operations, npm, python, etc.\n", style="cyan")

        self.console.print(Panel(help_text, title="Help", border_style="yellow"))

    def run_interactive(self):
        """Run the interactive TUI"""
        self.console.clear()

        # Welcome message
        welcome_text = Text()
        welcome_text.append("🦙 Welcome to BELLA!", style="bold blue")
        welcome_text.append(" • Your AI-powered assistant\n", style="green")
        welcome_text.append("Connected to: ", style="dim")
        welcome_text.append(OLLAMA_MODEL, style="cyan")

        self.console.print(
            Panel(
                Align.center(welcome_text), title="🚀 Starting...", border_style="green"
            )
        )

        time.sleep(2)

        try:
            while True:
                try:
                    # Get user input
                    user_input = self.get_user_input_non_blocking()

                    if user_input is None:  # Ctrl+C
                        break

                    user_input = user_input.strip()

                    if not user_input:
                        continue

                    if user_input.lower() == "help":
                        self._show_help()
                        input("\nPress Enter to continue...")
                        continue
                    elif user_input.lower() == "clear":
                        # Clear chat history except system prompt
                        global chat_history
                        chat_history = [chat_history[0]]  # Keep system prompt
                        self.console.print("[bold yellow]Chat cleared![/bold yellow]")
                        time.sleep(1)
                        continue
                    elif user_input.lower() in ["quit", "exit"]:
                        break

                    # Process the input
                    response = self.process_user_input(user_input)

                except KeyboardInterrupt:
                    break

        except KeyboardInterrupt:
            pass

        self.console.print("\n[bold red]👋 Goodbye! Thanks for using BELLA![/bold red]")


if __name__ == "__main__":
    tui = BellaTUI()
    tui.run_interactive()
