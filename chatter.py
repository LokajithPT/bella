import ollama
import time
import sys
import os
import signal
import json
import glob
import subprocess
import requests
import re
from typing import Optional, Union, List, Dict

from rich.console import Console  # New import for rich output
from rich.panel import Panel  # New import for rich panels
from rich.syntax import Syntax  # New import for rich code highlighting
from rich.text import Text  # New import for rich text styling
from rich.markdown import Markdown  # New import for markdown rendering
from prompt_toolkit import PromptSession  # New import for enhanced input
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.python import PythonLexer
from prompt_toolkit.key_binding import KeyBindings

# Define key bindings for Ctrl+Enter submission
kb = KeyBindings()


@kb.add("c-m")  # Enter
def _(event):
    # Standard enter adds a newline in multiline mode
    event.current_buffer.insert_text("\n")


@kb.add("c-j")  # Ctrl+J
def _(event):
    event.current_buffer.validate_and_handle()


# Initialize Rich Console
console = Console()

# Initialize Prompt Toolkit Session
session = PromptSession(lexer=PygmentsLexer(PythonLexer), key_bindings=kb)


# === CONFIG ===
import os
from dataclasses import dataclass


@dataclass
class Config:
    model: str = "mervinpraison/llama3.2-3B-instruct:8b"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(model=os.getenv("OLLAMA_MODEL", cls.model))


config = Config.from_env()
OLLAMA_MODEL = config.model

# === SYSTEM PROMPT ===
system_prompt_content = (
    "You are Chatter, a senior developer AI assistant. Be smart, fast, and helpful.\n\n"
    "Tool Usage:\n"
    "- Use tools only when necessary for the user's request\n"
    "- Prefer direct tool_calls over JSON blocks\n"
    '- If using JSON blocks, format: `{"function": {"name": "tool_name", "arguments": {...}}}`\n'
    "- Never explain tool usage, just execute\n"
    "- Provide real values, no placeholders\n\n"
    "Available tools: read_file_tool, write_file_tool, web_fetch_tool, web_search_tool, "
    "list_directory_tool, glob_tool, search_file_content_tool, run_shell_command_tool\n\n"
    "Respond directly and efficiently to user requests."
)

chat_history = [{"role": "system", "content": system_prompt_content}]

# === CLEAN TOOL CALL PARSING ===

import traceback


def _parse_tool_call_from_text(text: str) -> List[Dict]:
    """
    Parse tool calls from text. Supports multiple JSON formats.
    """
    parsed_calls = []

    # Extract JSON from code blocks
    json_blocks = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)

    # Try parsing entire text as JSON if no blocks found
    if not json_blocks:
        try:
            json.loads(text)
            json_blocks = [text]
        except json.JSONDecodeError:
            pass

    for json_str in json_blocks:
        try:
            data = json.loads(json_str)

            # Handle different JSON formats
            if "function" in data:
                # Already in correct format: {"function": {"name": ..., "arguments": ...}}
                parsed_calls.append(data)
            elif "name" in data and "parameters" in data:
                # Format: {"name": "...", "parameters": {...}}
                parsed_calls.append(
                    {
                        "function": {
                            "name": data["name"],
                            "arguments": data["parameters"],
                        }
                    }
                )
            elif "tool_call" in data:
                # Format: {"tool_call": {"tool_name": {...}}}
                for tool_name, args in data["tool_call"].items():
                    parsed_calls.append(
                        {"function": {"name": tool_name, "arguments": args}}
                    )
            elif "name" in data:
                # Simple format: {"name": "...", "arguments": {...}} or just {"name": "..."}
                parsed_calls.append(
                    {
                        "function": {
                            "name": data["name"],
                            "arguments": data.get("arguments", {}),
                        }
                    }
                )
        except json.JSONDecodeError:
            continue

    return parsed_calls


# === TOOL DEFINITIONS ===


def read_file_tool(file_path: Union[str, dict]) -> str:
    """Reads the content of a specified file."""
    try:
        if isinstance(file_path, dict):
            file_path = str(file_path.get("file_path", ""))
        with open(file_path, "r") as f:
            content = f.read()
        return f"File content of '{file_path}':\n```\n{content}\n```"
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except Exception as e:
        return f"Error reading file '{file_path}': {e}"


def write_file_tool(file_path: str, content: str) -> str:
    """Writes content to a specified file."""
    try:
        with open(file_path, "w") as f:
            f.write(content)
        return f"Successfully wrote to file '{file_path}'."
    except Exception as e:
        return f"Error writing to file '{file_path}': {e}"


def web_fetch_tool(url: str) -> str:
    """Fetches the content of a given URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return f"Content from {url}:\n```\n{response.text[:1000]}...\n``` (truncated to 1000 chars)"
    except requests.exceptions.RequestException as e:
        return f"Error fetching URL '{url}': {e}"
    except Exception as e:
        return f"An unexpected error occurred while fetching '{url}': {e}"


def web_search_tool(query: str) -> str:
    """Performs web search using DuckDuckGo's API (no API key required)."""
    try:
        # Use DuckDuckGo's instant answer API
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []

        # Get instant answer if available
        if data.get("AbstractText"):
            results.append(f"Answer: {data['AbstractText']}")

        # Get related topics
        for topic in data.get("RelatedTopics", [])[:5]:
            if "Text" in topic:
                results.append(f"• {topic['Text']}")

        if results:
            return f"Search results for '{query}':\n" + "\n".join(results)
        else:
            return f"No results found for '{query}'. Try a different search term."

    except Exception as e:
        return f"Web search failed for '{query}': {e}"


def list_directory_tool(dir_path: str = ".") -> str:
    """Lists the names of files and subdirectories directly within a specified directory path."""
    try:
        entries = os.listdir(dir_path)
        return f"Contents of directory '{dir_path}':\n" + "\n".join(entries)
    except FileNotFoundError:
        return f"Error: Directory '{dir_path}' not found."
    except Exception as e:
        return f"Error listing directory '{dir_path}': {e}"


def glob_tool(pattern: str, dir_path: str = ".") -> str:
    """Finds files matching a glob pattern within a specified directory. Defaults to current directory ('.') if dir_path is not specified."""
    try:
        # Change current working directory temporarily for glob to work relative to dir_path
        original_cwd = os.getcwd()
        os.chdir(dir_path)
        matching_files = glob.glob(pattern)
        os.chdir(original_cwd)  # Change back

        if matching_files:
            return f"Files matching pattern '{pattern}' in '{dir_path}':\n" + "\n".join(
                matching_files
            )
        else:
            return f"No files matching pattern '{pattern}' found in '{dir_path}'."
    except Exception as e:
        return f"Error globbing for pattern '{pattern}' in '{dir_path}': {e}"


def search_file_content_tool(pattern: str, file_path: str) -> str:
    """Searches for a pattern (case-sensitive) within the content of a specified file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        found_lines = [line for line in content.splitlines() if pattern in line]

        if found_lines:
            return (
                f"Pattern '{pattern}' found in '{file_path}':\n"
                + "\n".join(found_lines[:10])
                + (
                    f"\n...and {len(found_lines) - 10} more lines."
                    if len(found_lines) > 10
                    else ""
                )
            )
        else:
            return f"Pattern '{pattern}' not found in '{file_path}'."
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except Exception as e:
        return f"Error searching file '{file_path}': {e}"


def run_shell_command_tool(
    command: Union[str, List[str]],
) -> str:  # Modified command type hint
    """Executes a shell command and returns its stdout and stderr."""
    if isinstance(command, list):
        command_str = " ".join(command)
    else:
        command_str = command

    # Auto-correct common python commands
    if command_str.startswith("python "):
        if os.system("which python3 > /dev/null 2>&1") == 0:
            command_str = command_str.replace("python ", "python3 ", 1)
    try:
        # Using shell=True for simpler command execution, but be cautious with user input
        result = subprocess.run(
            command_str, shell=True, capture_output=True, text=True, check=True
        )
        return f"Command: {command_str}\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}"
    except subprocess.CalledProcessError as e:
        return f"Command '{e.cmd}' failed with exit code {e.returncode}:\nStdout:\n{e.stdout}\nStderr:\n{e.stderr}"
    except Exception as e:
        return f"Error executing command '{command_str}': {e}"


# Tool schemas for Ollama
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file_tool",
            "description": "Reads the content of a specified file.",
            "parameters": {
                "type": "object",
                "properties": {"file_path": {"type": "string"}},
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file_tool",
            "description": "Writes content to a specified file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to write.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file.",
                    },
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch_tool",
            "description": "Fetches the content of a given URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch."}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search_tool",
            "description": "Performs a web search using a dedicated search API (e.g., SerpAPI for Google Search) and returns relevant snippets. This tool requires integration with an external API for robust functionality.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory_tool",
            "description": "Lists the names of files and subdirectories directly within a specified directory path. Defaults to current directory if not specified.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "The path to the directory to list.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob_tool",
            "description": "Finds files matching a glob pattern within a specified directory. Defaults to current directory ('.') if dir_path is not specified.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The glob pattern to match against (e.g., '*.py', 'src/**/*.txt').",
                    },
                    "dir_path": {
                        "type": "string",
                        "description": "The path to the directory to search within.",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_file_content_tool",
            "description": "Searches for a pattern (case-sensitive) within the content of a specified file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The pattern to search for.",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to search within.",
                    },
                },
                "required": ["pattern", "file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell_command_tool",
            "description": "Executes a shell command and returns its stdout and stderr. Use with caution for commands that modify the system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": ["string", "array"],
                        "items": {"type": "string"},
                        "description": "The exact shell command to execute as a single string (e.g., 'ls -l') or as an array of strings (e.g., ['ls', '-l']).",
                    }
                },
                "required": ["command"],
            },
        },
    },
]

# Map tool names to actual functions
AVAILABLE_TOOLS = {
    "read_file_tool": read_file_tool,
    "write_file_tool": write_file_tool,
    "web_fetch_tool": web_fetch_tool,
    "web_search_tool": web_search_tool,
    "list_directory_tool": list_directory_tool,
    "glob_tool": glob_tool,
    "search_file_content_tool": search_file_content_tool,
    "run_shell_command_tool": run_shell_command_tool,
}


# === UTILS ===
def type_like_terminal(text, delay=0.005):  # Reduced delay for faster output
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def _handle_ollama_error(e: Exception, model: str) -> str:
    """Handle Ollama errors consistently"""
    if isinstance(e, requests.exceptions.ConnectionError):
        return f"Error: Could not connect to Ollama server. Is it running? ({e})"
    else:
        return f"Error with Ollama model '{model}': {e}"


def _execute_tool_call(tool_call_item, available_tools: dict) -> tuple:
    """Execute a single tool call and return (tool_call_id, output)"""
    function_name = None
    function_args = {}
    tool_call_id = None

    if isinstance(tool_call_item, dict) and "function" in tool_call_item:
        func_data = tool_call_item["function"]
        function_name = func_data.get("name")
        function_args = func_data.get("arguments", {})
        tool_call_id = "generated_from_text_" + str(time.time_ns())
    else:
        # Handle Ollama ToolCall objects
        tool_call_id = "generated_ollama_tool_id_" + str(time.time_ns())
        func_obj = getattr(tool_call_item, "function", None)
        if func_obj:
            function_name = getattr(func_obj, "name", None)
            function_args = dict(getattr(func_obj, "arguments", {}))

    if not function_name:
        return None, None

    console.print(
        Panel(
            f"Tool: [bold]{function_name}[/bold]\nArgs: {json.dumps(function_args, indent=2)}",
            title="Tool Call",
            style="cyan",
        )
    )

    if function_name in available_tools:
        try:
            tool_output = available_tools[function_name](**function_args)
            console.print(f"[dim]Output length: {len(str(tool_output))} chars[/dim]")
            return tool_call_id, str(tool_output)
        except Exception as e:
            error_msg = f"Error executing tool '{function_name}': {e}"
            console.print(f"[bold red]{error_msg}[/bold red]")
            return tool_call_id, error_msg
    else:
        error_msg = f"Unknown tool: {function_name}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        return tool_call_id, error_msg


def ask_ollama(prompt: str) -> str:
    chat_history.append({"role": "user", "content": prompt})

    try:
        response_generator = ollama.chat(
            model=OLLAMA_MODEL, messages=chat_history, stream=True, tools=TOOLS
        )
    except Exception as e:
        error_msg = _handle_ollama_error(e, OLLAMA_MODEL)
        console.print(f"[bold red]{error_msg}[/bold red]")
        chat_history.pop()
        return error_msg

    try:
        response_generator = ollama.chat(
            model=OLLAMA_MODEL, messages=chat_history, stream=True, tools=TOOLS
        )
    except Exception as e:
        error_msg = _handle_ollama_error(e, OLLAMA_MODEL)
        console.print(f"[bold red]{error_msg}[/bold red]")
        chat_history.pop()
        return error_msg

    full_response_content = ""
    tool_calls = []

    try:
        # Process the stream
        for chunk in response_generator:
            if "content" in chunk["message"] and chunk["message"]["content"]:
                content_chunk = chunk["message"]["content"]
                sys.stdout.write(content_chunk)
                sys.stdout.flush()
                full_response_content += content_chunk

            if "tool_calls" in chunk["message"] and chunk["message"]["tool_calls"]:
                for tool_call_item in chunk["message"]["tool_calls"]:
                    tool_calls.append(tool_call_item)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]AI response interrupted.[/bold yellow]")
        return ""

    print()  # Newline after streaming

    # If no structured tool calls were made, try parsing from text content
    if not tool_calls and full_response_content:
        parsed_from_text_tool_calls = _parse_tool_call_from_text(full_response_content)
        if parsed_from_text_tool_calls:
            tool_calls.extend(parsed_from_text_tool_calls)
        else:
            chat_history.append({"role": "assistant", "content": full_response_content})

    # Execute tool calls
    if tool_calls:
        for tool_call_item in tool_calls:
            tool_call_id, tool_output = _execute_tool_call(
                tool_call_item, AVAILABLE_TOOLS
            )
            if tool_call_id is None:
                continue

            chat_history.append(
                {
                    "role": "tool",
                    "content": tool_output,
                    "tool_call_id": tool_call_id,
                }
            )

        console.print("[bold purple]Processing tool output...[/bold purple]")
        try:
            second_response_generator = ollama.chat(
                model=OLLAMA_MODEL, messages=chat_history, stream=True, tools=TOOLS
            )
        except Exception as e:
            console.print(
                f"[bold red]Error with Ollama model '{OLLAMA_MODEL}' for second call: {e}.[/bold red]"
            )
            return str(e)

        final_ai_response = ""
        for chunk in second_response_generator:
            if "content" in chunk["message"] and chunk["message"]["content"]:
                content_chunk = chunk["message"]["content"]
                sys.stdout.write(content_chunk)
                sys.stdout.flush()
                final_ai_response += content_chunk
        print()
        chat_history.append({"role": "assistant", "content": final_ai_response})
        return final_ai_response
    else:
        # No tool calls
        return full_response_content


# === MAIN LOOP ===
def main():
    console.print(
        Panel(
            "[bold green]Welcome to Chatter, your Ollama-powered AI assistant![/bold green]",
            title="Chatter",
        )
    )
    console.print(f"[dim]Using Ollama model: {OLLAMA_MODEL}[/dim]")
    console.print("[dim]Type 'exit' to quit.[/dim]")
    console.print(
        "[dim]Use [bold]Enter[/bold] for new lines. Use [bold]Ctrl+J[/bold] (or Esc+Enter) to SUBMIT.[/dim]"
    )

    while True:
        try:
            console.print("\n[bold cyan]You:[/bold cyan]")
            user_input = session.prompt("➤ ", multiline=True).strip()

            if user_input.lower() == "exit":
                console.print("[bold red]Exiting Chatter. See ya![/bold red]")
                break
            elif user_input.lower() == "/clear":
                os.system("cls" if os.name == "nt" else "clear")
                continue

            if not user_input:
                continue

            console.print("\n[bold purple]Chatter is thinking...[/bold purple]")
            start_time = time.time()
            ask_ollama(user_input)
            end_time = time.time()
            response_time = end_time - start_time
            console.print(f"[dim]Response time: {response_time:.2f} seconds[/dim]")

        except KeyboardInterrupt:
            console.print("\n[bold red]Exiting Chatter. Goodbye![/bold red]")
            break
        except Exception as e:
            console.print(f"[bold red]An error occurred:[/bold red] {e}")
            traceback.print_exc()


# === ENTRY ===
if __name__ == "__main__":
    main()
