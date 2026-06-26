import requests
import streamlit as st
from typing import Dict, Any, Tuple
from config import OLLAMA_MODEL, OLLAMA_HOST, OLLAMA_API_KEY

def check_ollama_server() -> Tuple[bool, str]:
    """Checks if the Ollama server is reachable (handles local and remote hosts)."""
    try:
        headers = {}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
        
        # Check endpoint
        url = OLLAMA_HOST.rstrip("/") + "/api/tags"
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code in [200, 404]:  # 404 is allowed for custom endpoints or gateways
            return True, "Ollama Cloud Connection Active" if OLLAMA_API_KEY else "Ollama server is running locally."
        return False, f"Server responded with status {response.status_code}"
    except Exception as e:
        if OLLAMA_API_KEY:
            return False, f"Ollama Cloud host is unreachable: {e}"
        return False, "Ollama server is NOT running. Please start it by opening the Ollama app."

def check_model_exists() -> Tuple[bool, str]:
    """Checks if the required model is ready (auto-passes for cloud models)."""
    if OLLAMA_API_KEY:
        return True, f"Model '{OLLAMA_MODEL}' is ready (Cloud-managed)."
        
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            for m in models:
                name = m.get('name', '') if isinstance(m, dict) else getattr(m, 'model', '')
                if OLLAMA_MODEL in name:
                    return True, f"Model '{OLLAMA_MODEL}' is ready."
            return False, f"Model '{OLLAMA_MODEL}' not found. Please run 'ollama pull {OLLAMA_MODEL}'."
        return False, f"Server responded with status {response.status_code}"
    except Exception as e:
        return False, f"Error checking models: {e}"

@st.cache_data(ttl=60)
def run_system_check() -> Dict[str, Any]:
    """Runs a full system diagnostic. Cached for 60 seconds to improve performance."""
    server_ok, server_msg = check_ollama_server()
    model_ok, model_msg = check_model_exists() if server_ok else (False, "Cannot check models without server.")
    
    return {
        "server": {"ok": server_ok, "message": server_msg},
        "model": {"ok": model_ok, "message": model_msg},
        "all_clear": server_ok and model_ok
    }
