
import requests
from ..config import LLM_BASE_URL, LLM_MODEL

def generate(messages, temperature=0.2, max_tokens=512):
    url = f"{LLM_BASE_URL}/api/chat"
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens}
    }
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data.get("message", {}).get("content", "")
