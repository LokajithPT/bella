#!/usr/bin/env python3
"""
BELLA - AI Assistant Launcher
Choose your interface: Classic CLI or Modern TUI
"""

import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.align import Align

console = Console()


def show_logo():
    """Show BELLA logo"""
    logo_text = Text()
    logo_text.append("🦙 BELLA", style="bold blue")
    logo_text.append(" • AI Assistant", style="green")

    console.print(Panel(Align.center(logo_text), title="Welcome", border_style="blue"))


def choose_interface():
    """Choose between CLI and TUI"""
    console.print("\n[bold cyan]Choose your interface:[/bold cyan]")
    console.print("1. [green]Classic CLI[/green] - Simple terminal interface")
    console.print("2. [blue]Modern TUI[/blue] - Rich visual interface")
    console.print("3. [dim]Exit[/dim]")

    choice = Prompt.ask(
        "\n[yellow]Select option (1-3)[/yellow]", choices=["1", "2", "3"], default="2"
    )

    return choice


def run_cli():
    """Run the classic CLI interface"""
    console.print("[bold green]🚀 Starting Classic CLI...[/bold green]")
    try:
        from chatter import main as cli_main

        cli_main()
    except ImportError:
        console.print("[bold red]Error: chatter.py not found![/bold red]")
        sys.exit(1)


def run_tui():
    """Run the modern TUI interface"""
    console.print("[bold blue]🚀 Starting Modern TUI...[/bold blue]")
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("bella_tui", "bella_tui.py")
        if spec is None:
            raise ImportError("Could not load bella_tui.py")
        bella_tui = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise ImportError("Could not load bella_tui.py loader")
        spec.loader.exec_module(bella_tui)
        tui = bella_tui.BellaTUI()
        tui.run_interactive()
    except Exception as e:
        console.print(f"[bold red]Error loading TUI: {e}![/bold red]")
        sys.exit(1)


def main():
    """Main launcher"""
    show_logo()

    while True:
        choice = choose_interface()

        if choice == "1":
            run_cli()
            break
        elif choice == "2":
            run_tui()
            break
        elif choice == "3":
            console.print("[bold red]👋 Goodbye![/bold red]")
            sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]👋 Goodbye![/bold red]")
        sys.exit(0)
