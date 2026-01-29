import time
import sys
import requests
import os

# Configuration for different modes
AI_MODE = "ollama"  # Default mode: "ollama" or "deepseek"
DEEPSEEK_KEY = os.getenv("DEEPSEEK_KEY", "YOUR_DEEPSEEK_KEY")

# Load saved key if exists
try:
    if os.path.exists(".deepseek_key"):
        with open(".deepseek_key", "r") as f:
            DEEPSEEK_KEY = f.read().strip()
except:
    pass


def ask_deepseek_free(prompt):
    """Completely free DeepSeek Coder API"""
    try:
        # Check if we have a valid key
        if DEEPSEEK_KEY.startswith("sk-"):
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DEEPSEEK_KEY}",
                },
                json={
                    "model": "deepseek-coder",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 4000,
                },
                timeout=30,
            )

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 401:
                return "DeepSeek: Invalid API key. Check your key."
            elif response.status_code == 402:
                return "DeepSeek: API rate limit or billing issue. Try later."
            else:
                return f"DeepSeek API error: HTTP {response.status_code}"
        else:
            return (
                "DeepSeek: No valid API key. Run in DeepSeek mode and enter your key."
            )

    except Exception as e:
        return f"DeepSeek connection error: {str(e)}"


def ask_ai_mode(prompt, mode):
    """Route to appropriate AI based on mode"""
    if mode == "deepseek":
        return ask_deepseek_free(prompt)
    else:  # Default to ollama
        try:
            import sys

            sys.path.append(os.path.dirname(__file__))
            from chatter import ask_ollama

            return ask_ollama(prompt)
        except Exception as e:
            return f"Ollama error: {str(e)}"


def switch_mode():
    """Switch between AI modes"""
    global AI_MODE, DEEPSEEK_KEY

    print("\n🔧 AI MODE SELECTION")
    print("1. Ollama (Local)")
    print("2. DeepSeek Coder (Free Cloud)")

    choice = input("Select mode (1-2): ").strip()

    if choice == "1":
        AI_MODE = "ollama"
        print("✅ Switched to Ollama mode")
    elif choice == "2":
        if DEEPSEEK_KEY == "YOUR_DEEPSEEK_KEY":
            new_key = input("Enter DeepSeek API key: ").strip()
            if new_key:
                # Save key to environment and file
                DEEPSEEK_KEY = new_key
                os.environ["DEEPSEEK_KEY"] = new_key
                AI_MODE = "deepseek"

                # Save key to file for persistence
                try:
                    with open(".deepseek_key", "w") as f:
                        f.write(new_key)
                    print("✅ Key saved for future sessions")
                except:
                    pass  # Silent fail if can't save

                print("✅ Switched to DeepSeek mode")
            else:
                print("❌ Invalid key, staying in current mode")
        else:
            AI_MODE = "deepseek"
            print("✅ Switched to DeepSeek mode")
    else:
        print("❌ Invalid choice")

    input("Press Enter to continue...")


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
                print(f"  Current mode: {AI_MODE.upper()}")
                print("  Enter = Send | mode = Switch | help | clear | quit")

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
                    elif line.strip() == "mode":
                        switch_mode()
                        lines = []  # Reset input
                        continue
                    elif line.strip() == "help":
                        print("Commands:")
                        print("  ;; - Send message")
                        print("  mode - Switch AI provider")
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

            # AI integration based on mode
            try:
                response = ask_ai_mode(user_input, AI_MODE)
            except Exception as e:
                response = f"Error: {str(e)}"

            messages.append({"role": "assistant", "content": response})

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    simple_tui()
