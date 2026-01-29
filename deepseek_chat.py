#!/usr/bin/env python3
"""
Simple script to talk to DeepSeek API directly
Your key: sk-e342aeb2fe7b4e23ab46e1208aed5df7
"""

import requests
import json

# Your DeepSeek key
DEEPSEEK_KEY = "sk-8e1d1e7eb4ad43a1bca7f55e8980f769"


def talk_to_deepseek(message):
    """Send message to DeepSeek and get response"""
    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
            },
            json={
                "model": "deepseek-coder",
                "messages": [{"role": "user", "content": message}],
                "temperature": 0.7,
            },
            timeout=30,
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"API Error: {response.status_code}"

    except Exception as e:
        return f"Connection Error: {str(e)}"


def main():
    print("🦙 DeepSeek Chat - Direct API Access")
    print("🔑 Key: sk-e342aeb...5df7")
    print("💬 Type 'quit' to exit")
    print("─" * 40)

    while True:
        try:
            message = input("You >> ").strip()

            if not message:
                continue

            if message.lower() in ["quit", "exit"]:
                print("👋 Goodbye!")
                break

            print("🤔 DeepSeek is thinking...")

            response = talk_to_deepseek(message)

            print(f"🦙 DeepSeek:")
            print("─" * 40)
            print(response)
            print("─" * 40)
            print()

        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
