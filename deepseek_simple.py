import requests
import json
import os

# Simple DeepSeek integration without heavy dependencies
DEEPSEEK_KEY = "sk-e342aeb2fe7b4e23ab46e1208aed5df7"


def ask_deepseek_simple(prompt):
    """Lightweight DeepSeek API call - no vLLM needed"""
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
                "max_tokens": 4000,
            },
            timeout=30,
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"DeepSeek API error: HTTP {response.status_code}"

    except Exception as e:
        return f"DeepSeek error: {str(e)}"


def test_deepseek():
    """Test the DeepSeek connection"""
    print("🔧 Testing DeepSeek API...")

    result = ask_deepseek_simple("Write a simple hello world function in Python")
    print(f"🦙 DeepSeek response: {result}")


if __name__ == "__main__":
    test_deepseek()
