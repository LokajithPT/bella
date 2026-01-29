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
from rich.box import ROUNDED, DOUBLE
from rich.rule import Rule

# Import existing functionality
from chatter import ask_ollama, chat_history, OLLAMA_MODEL, AVAILABLE_TOOLS


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
            Layout(name="footer", size=3),
        )

        self.layout["main"].split_row(
            Layout(name="chat", ratio=3),
            Layout(name="sidebar", size=35),
        )

    def render_header(self) -> Panel:
        """Render the clean header"""
        header_text = Text()
        header_text.append("BELLA", style="bold #0087FF")
        header_text.append(" • AI Assistant", style="dim")

        return Panel(
            Align.center(header_text),
            box=ROUNDED,
            border_style="#0087FF",
            padding=(1, 2),
        )

    def render_chat(self) -> Panel:
        """Render the chat area"""
        if not self.messages:
            chat_content = Text()
            chat_content.append("Ready for conversation...\n\n", style="dim")
            chat_content.append("• Ctrl+C to exit\n", style="#505050")
            chat_content.append("• Type 'help' for commands\n", style="#505050")
            chat_content.append("• Full tool integration available\n", style="#505050")
        else:
            chat_content = Text()
            for msg in self.messages[-10:]:  # Show last 10 messages
                if msg["role"] == "user":
                    chat_content.append("You: ", style="bold #00D084")
                    chat_content.append(msg["content"] + "\n\n")
                elif msg["role"] == "assistant":
                    chat_content.append("Bella: ", style="bold #0087FF")
                    content = msg["content"]
                    if len(content) > 400:
                        content = content[:400] + "..."
                    chat_content.append(content + "\n\n")

        return Panel(
            chat_content,
            title="Chat",
            box=ROUNDED,
            border_style="#00D084",
            padding=(1, 2),
        )

    def render_sidebar(self) -> Panel:
        """Render the sidebar with info"""
        # Status table
        status_table = Table(show_header=False, box=None, padding=0)
        status_table.add_column("", style="#0087FF", width=8)
        status_table.add_column("", style="white", width=15)

        status_table.add_row("Status", self.current_status)
        status_table.add_row(
            "Model",
            OLLAMA_MODEL.split("/")[-1] if "/" in OLLAMA_MODEL else OLLAMA_MODEL,
        )
        status_table.add_row(
            "Messages",
            str(len([m for m in chat_history if m["role"] in ["user", "assistant"]])),
        )

        # Tools table
        tools_table = Table(title="Tools", show_header=True, box=None, padding=0)
        tools_table.add_column("", style="#FF9500", width=20)
        tools_table.add_column("", style="#00D084", width=8)

        tools = [
            ("read/write", "Active"),
            ("web fetch", "Active"),
            ("web search", "Active"),
            ("shell", "Active"),
            ("directory", "Active"),
        ]
        for tool_name, status in tools:
            tools_table.add_row(f"• {tool_name}", status)

        sidebar_content = Table.grid(padding=1)
        sidebar_content.add_row(
            Panel(
                status_table,
                title="System",
                box=ROUNDED,
                border_style="#0087FF",
                padding=(1, 1),
            ),
            Panel(
                tools_table,
                title="Tools",
                box=ROUNDED,
                border_style="#FF9500",
                padding=(1, 1),
            ),
        )

        return Panel(
            sidebar_content,
            title="Info",
            box=ROUNDED,
            border_style="#505050",
            padding=(1, 1),
        )

    def render_footer(self) -> Panel:
        """Render the footer status bar"""
        status_text = Text()
        status_text.append(f"[{self.current_status}] ", style="#00D084")
        status_text.append(f"{time.strftime('%H:%M:%S')} ", style="#505050")

        if self.is_processing:
            status_text.append("● Processing", style="#FF9500 animate")

        help_text = "Ctrl+C: Exit | help: Commands | clear: Reset"

        footer_content = Table.grid(padding=1)
        footer_content.add_column()
        footer_content.add_column(justify="right")
        footer_content.add_row(status_text, help_text)

        return Panel(footer_content, box=ROUNDED, style="#1E1E1E", padding=(0, 2))

    def get_full_layout(self) -> Layout:
        """Build and return the complete layout"""
        self.layout["header"].update(self.render_header())
        self.layout["chat"].update(self.render_chat())
        self.layout["sidebar"].update(self.render_sidebar())
        self.layout["footer"].update(self.render_footer())

        return self.layout

    def add_message(self, role: str, content: str):
        """Add message to chat"""
        self.messages.append({"role": role, "content": content})

    def set_status(self, status: str):
        """Update current status"""
        self.current_status = status

    def process_input(self, user_input: str) -> str:
        """Process user input through AI"""
        if self.is_processing:
            return "Processing in progress..."

        self.is_processing = True
        self.set_status("Processing...")

        try:
            start_time = time.time()
            response = ask_ollama(user_input)
            end_time = time.time()

            self.set_status(f"Ready ({end_time - start_time:.1f}s)")
            return response

        except Exception as e:
            self.set_status("Error")
            return f"Error: {str(e)}"
        finally:
            self.is_processing = False

    def get_user_input(self) -> Optional[str]:
        """Get user input"""
        try:
            return Prompt.ask(
                "[#00D084]You[/#00D084] >> ",
                default="",
                console=self.console,
                show_default=False,
            )
        except (KeyboardInterrupt, EOFError):
            return None

    def show_help(self):
        """Display help information"""
        help_content = Table(show_header=False, box=None, padding=1)
        help_content.add_column("", style="#0087FF", width=15)
        help_content.add_column("", style="white")

        help_content.add_row("Commands", "")
        help_content.add_row("help", "Show this help")
        help_content.add_row("clear", "Clear chat history")
        help_content.add_row("Ctrl+C", "Exit application")
        help_content.add_row("", "")
        help_content.add_row("Tools Available", "")
        help_content.add_row("Files", "read, write, list, search")
        help_content.add_row("Web", "fetch URLs, search web")
        help_content.add_row("System", "run any command")
        help_content.add_row("Examples", "")
        help_content.add_row("npm init -y", "Create Node project")
        help_content.add_row("read file.txt", "Read file content")
        help_content.add_row("search web query", "Search online")

        self.console.print(
            Panel(
                help_content,
                title="Help",
                box=ROUNDED,
                border_style="#0087FF",
                padding=(1, 2),
            )
        )

    def run(self):
        """Main TUI loop"""
        self.console.clear()

        # Welcome
        welcome_text = Text()
        welcome_text.append("BELLA", style="bold #0087FF")
        welcome_text.append(" • AI Assistant", style="#00D084")
        welcome_text.append("\n\nReady to assist you.", style="white")

        self.console.print(
            Panel(
                Align.center(welcome_text),
                title="Starting",
                box=DOUBLE,
                border_style="#00D084",
                padding=(1, 3),
            )
        )

        time.sleep(2)

        try:
            while True:
                # Display static UI, then get input
                self.console.clear()
                self.console.print(self.get_full_layout())

                user_input = self.get_user_input()

                if user_input is None:
                    break

                user_input = user_input.strip()

                if not user_input:
                    continue

                if user_input.lower() == "help":
                    self.show_help()
                    input("\nPress Enter to continue...")
                    continue
                elif user_input.lower() == "clear":
                    # Reset chat
                    global chat_history
                    chat_history = [chat_history[0]]  # Keep system prompt
                    self.messages.clear()
                    self.console.print("[#FF9500]Chat cleared![/#FF9500]")
                    time.sleep(1)
                    continue
                elif user_input.lower() in ["quit", "exit"]:
                    break

                # Add user message and get response
                self.add_message("user", user_input)
                response = self.process_input(user_input)
                self.add_message("assistant", response)

        except KeyboardInterrupt:
            pass

        self.console.print("\n[#FF9500]Goodbye! Thanks for using BELLA.[/#FF9500]")


if __name__ == "__main__":
    tui = BellaTUI()
    tui.run()
