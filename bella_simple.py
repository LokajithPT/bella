import time
import sys


def simple_tui():
    print("╔════════════════════════════════════════════════════════╗")
    print("║           BELLA • AI Assistant                      ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()

    messages = []

    try:
        while True:
            # Show recent messages
            for msg in messages[-5:]:
                if msg["role"] == "user":
                    print(f"🔹 You: {msg['content']}")
                else:
                    print(f"🔸 Bella: {msg['content']}")

            if not messages:
                print("💬 Ready to chat! (type 'help', 'clear', 'quit')")

            print()

            # Get input
            try:
                user_input = input("You >> ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input:
                continue

            if user_input.lower() == "help":
                print("Commands: help, clear, quit")
                print("Examples:")
                print("  npm init -y")
                print("  read file.txt")
                print("  make new folder")
                input("Press Enter...")
                continue
            elif user_input.lower() == "clear":
                messages.clear()
                continue
            elif user_input.lower() in ["quit", "exit"]:
                break

            # Add user message
            messages.append({"role": "user", "content": user_input})

            # Simulate AI thinking
            print("🔸 Bella is thinking...")
            time.sleep(1)

            # Integrate with real AI
            try:
                # Import here to avoid circular import issues
                import sys
                import os

                sys.path.append(os.path.dirname(__file__))
                from chatter import ask_ollama

                response = ask_ollama(user_input)
            except Exception as e:
                response = f"AI Error: {str(e)}"
            messages.append({"role": "assistant", "content": response})

    except KeyboardInterrupt:
        pass

    print("👋 Goodbye!")


if __name__ == "__main__":
    simple_tui()
