import time
import sys
import requests
import os

# Configuration
AI_MODE = "ollama"  # Default mode
DEEPSEEK_KEY = "YOUR_DEEPSEEK_KEY"  # Will be loaded properly


def load_deepseek_key():
    """Load DeepSeek key from file"""
    global DEEPSEEK_KEY
    try:
        if os.path.exists(".deepseek-key"):
            with open(".deepseek-key", "r") as f:
                loaded_key = f.read().strip()
                if loaded_key.startswith("sk-"):
                    DEEPSEEK_KEY = loaded_key
    except:
        pass


# Load saved key if exists
try:
    if os.path.exists(".deepseek-key"):
        with open(".deepseek-key", "r") as f:
            loaded_key = f.read().strip()
            if loaded_key.startswith("sk-"):
                DEEPSEEK_KEY = loaded_key
except:
    pass


def ask_deepseek(prompt):
    """DeepSeek API call"""
    if not DEEPSEEK_KEY.startswith("sk-"):
        return "DeepSeek: No valid API key. Use 'mode' to set key."

    try:
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
            },
            timeout=30,
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"DeepSeek error: HTTP {response.status_code}"

    except Exception as e:
        return f"DeepSeek connection error: {str(e)}"


def ask_ollama_fallback(prompt):
    """Fallback to Ollama"""
    try:
        sys.path.append(os.path.dirname(__file__))
        from chatter import ask_ollama

        return ask_ollama(prompt)
    except:
        return "Ollama not available. Install ollama."


def switch_mode():
    """Switch AI mode"""
    global AI_MODE, DEEPSEEK_KEY

    print("\n🔧 AI MODE SELECTION")
    print("1. Ollama (Local)")
    print("2. DeepSeek Coder (Free Cloud)")

    choice = input("Select mode (1-2): ").strip()

    if choice == "1":
        AI_MODE = "ollama"
        print("\n🔧 SWITCHED TO OLLAMA MODE")
        print("🟢 Status: Local AI processing")
        print("🔒 Privacy: All requests stay on your device")
        print("⚡ Speed: Instant response, no API delays")
        print("📁 Model: Your local Ollama models")
        print("💾 Cost: 100% FREE")
        print("\n✨ Ready to assist with local power!")

    elif choice == "2":
        AI_MODE = "deepseek"
        if not DEEPSEEK_KEY.startswith("sk-"):
            new_key = input("Enter DeepSeek API key: ").strip()
            if new_key and new_key.startswith("sk-"):
                DEEPSEEK_KEY = new_key
                os.environ["DEEPSEEK_KEY"] = new_key
                try:
                    with open(".deepseek-key", "w") as f:
                        f.write(new_key)
                    print("✅ Key saved to .deepseek-key")
                except:
                    pass
                print("\n🔧 SWITCHED TO DEEPSEEK MODE")
                print("🟢 Status: Cloud AI processing")
                print("🌐 Network: Internet-connected responses")
                print("⚡ Speed: Fast cloud API responses")
                print("💎 Quality: Code-specialized model")
                print("💰 Cost: Free tier with good limits")
                print("🔑 Key:", DEEPSEEK_KEY[:20] + "..." + DEEPSEEK_KEY[-4:])
                print("\n✨ Ready to assist with DeepSeek Coder!")
            else:
                print("❌ Invalid key format")
        else:
            print("\n🔧 SWITCHED TO DEEPSEEK MODE")
            print("🟢 Status: Cloud AI processing")
            print("🌐 Network: Internet-connected responses")
            print("⚡ Speed: Fast cloud API responses")
            print("💎 Quality: Code-specialized model")
            print("💰 Cost: Free tier with good limits")
            print("🔑 Key:", DEEPSEEK_KEY[:20] + "..." + DEEPSEEK_KEY[-4:])
            print("\n✨ Ready to assist with DeepSeek Coder!")
    else:
        print("❌ Invalid choice")


def ask_ai(prompt):
    """Route to appropriate AI"""
    if AI_MODE == "deepseek":
        return ask_deepseek(prompt)
    else:
        return ask_ollama_fallback(prompt)


def simple_tui():
    """Main TUI loop"""
    messages = []

    while True:
        print("\n╔═════════════════════════════════════════════════╗")
        print("║           BELLA • AI Assistant                      ║")
        print("╚════════════════════════════════════════════════════╝")

        print("\n╭──────────────────────────────────────────────────────────────╮")
        for msg in messages[-5:]:
            if msg["role"] == "user":
                print(f"│ You: {msg['content']:<50} │")
            else:
                print(f"│ Bella: {msg['content']:<47} │")
        print("╰──────────────────────────────────────────────────────────────╯")

        if not messages:
            print(f"💬 Ready! Mode: {AI_MODE.upper()} | help | clear | quit")
        else:
            print(f"💬 Mode: {AI_MODE.upper()} | help | clear | quit")

        print("\nYou >> ", end="", flush=True)

        # Get multi-line input
        lines = []
        try:
            while True:
                line = input()
                if line.strip() == ";;":
                    break  # Send message
                elif line.strip() == "help":
                    print("\nCommands:")
                    print("  ;; - Send message")
                    print("  mode - Switch AI provider")
                    print("  clear - Clear chat")
                    print("  quit - Exit")
                    print("Examples: npm init -y, read file.txt")
                    lines = []  # Reset input
                    continue
                elif line.strip() == "clear":
                    messages.clear()
                    print("Chat cleared!")
                    lines = []
                    continue
                elif line.strip() in ["quit", "exit"]:
                    return
                elif line.strip() == "mode":
                    switch_mode()
                    lines = []
                    continue
                else:
                    lines.append(line)
        except (EOFError, KeyboardInterrupt):
            return

        user_input = "\n".join(lines).strip()

        if not user_input:
            continue

        # Add user message
        messages.append({"role": "user", "content": user_input})

        # Get AI response
        print(f"\n🔸 Bella ({AI_MODE.upper()}) is thinking...")
        time.sleep(1)

        response = ask_ai(user_input)
        messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    print("🦙 BELLA • AI Assistant")
    print("🔗 GitHub: github.com/LokajithPT/bella")
    print("\nStarting with", AI_MODE.upper(), "mode...")
    time.sleep(1)

    simple_tui()
    print("\n👋 Goodbye!")
