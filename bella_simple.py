import time
import sys


def simple_tui():
    print("╔══════════════════════════════════════════════════════╗")
    print("║           BELLA • AI Assistant                      ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()

    messages = []

    try:
        while True:
            # Show recent messages
            print(
                "╭──────────────────────────────────────────────────────────────────────╮"
            )
            for msg in messages[-5:]:
                if msg["role"] == "user":
                    print(f"│ You: {msg['content']:<50} │")
                else:
                    print(f"│ Bella: {msg['content']:<47} │")
            print(
                "╰──────────────────────────────────────────────────────────────────────╯"
            )

            if not messages:
                print("💬 Ready to chat!")
                print("  Enter = Send | help | clear | quit")

            print()

            # Get multi-line input
            print("You >> ", end="", flush=True)
            lines = []

            while True:
                try:
                    line = input()
                    if line.strip() == ";;":
                        # Send with ;; (semicolon semicolon)
                        break
                    elif line.strip() == "help":
                        print("Commands:")
                        print("  ;; - Send message")
                        print("  help - Show commands")
                        print("  clear - Clear chat")
                        print("  quit - Exit")
                        print("  Examples: npm init -y, read file.txt")
                        input("Press Enter...")
                        lines = []  # Reset
                        continue
                    elif line.strip() == "clear":
                        messages.clear()
                        print("Chat cleared!")
                        lines = []  # Reset
                        continue
                    elif line.strip() in ["quit", "exit"]:
                        print("Goodbye!")
                        return
                    else:
                        lines.append(line)
                except (EOFError, KeyboardInterrupt):
                    return

            user_input = "\n".join(lines).strip()

            if not user_input:
                continue

            # Add user message
            messages.append({"role": "user", "content": user_input})

            # AI thinking
            print("🔸 Bella is thinking...")
            time.sleep(1)

            # Real AI integration
            try:
                import os

                sys.path.append(os.path.dirname(__file__))
                from chatter import ask_ollama

                response = ask_ollama(user_input)
            except Exception as e:
                response = f"Error: {str(e)}"

            messages.append({"role": "assistant", "content": response})

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    simple_tui()
