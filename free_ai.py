import requests
import json


def ask_deepseek(prompt):
    """Free DeepSeek Coder API - no limits"""
    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer sk-your-deepseek-key",  # Get free key from deepseek.com
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
            return f"Error: {response.status_code}"

    except Exception as e:
        return f"DeepSeek error: {str(e)}"


def ask_groq_free(prompt):
    """Free Groq API - 30 requests/minute"""
    try:
        from groq import Groq

        client = Groq(api_key="gsk_...")  # Free key from groq.com
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Groq error: {str(e)}"


# Update bella to use free APIs
def ask_free_ai(prompt, provider="deepseek"):
    """Switch between free AI providers"""
    if provider == "deepseek":
        return ask_deepseek(prompt)
    elif provider == "groq":
        return ask_groq_free(prompt)
    else:
        return "Provider not supported. Use 'deepseek' or 'groq'"
