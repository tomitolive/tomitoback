import os
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
print(f"API Key present: {bool(API_KEY)}")
if API_KEY:
    print(f"API Key snippet: {API_KEY[:5]}...{API_KEY[-5:]}")

url = "https://api.groq.com/openai/v1/chat/completions"
payload = {
    "model": "llama-3.3-70b-versatile",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant. Respond with valid JSON."},
        {"role": "user", "content": "Tell me a story about a hero named Tomito. Return JSON like {'story': '...'}"}
    ],
    "temperature": 0.6,
    "response_format": {"type": "json_object"}
}
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

try:
    print("Calling Groq...")
    res = requests.post(url, headers=headers, json=payload, timeout=20)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
