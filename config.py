import os

# Ollama Configuration
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "22b32e28fd9b48a1811e66f93f23aeac.ox5sIPqap6G1_UH5c3UIclke")
# If API key is present, default to remote Ollama Cloud host; otherwise default to local
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "https://ollama.com" if OLLAMA_API_KEY else "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b-cloud")
OLLAMA_TIMEOUT = 120  # Seconds

def get_ollama_client():
    """Instantiates and returns an authenticated Ollama Client."""
    from ollama import Client
    headers = {}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
    return Client(host=OLLAMA_HOST, headers=headers, timeout=OLLAMA_TIMEOUT)


# File Processing
SUPPORTED_EXTENSIONS = [".pdf", ".docx"]
MAX_TEXT_LENGTH = 6000  # Limit resume text to stay within LLM context window

# Industry Categories
INDUSTRY_DOMAINS = [
    "IT & Software",
    "Digital Marketing",
    "Design & Creative",
    "Finance",
    "Healthcare",
    "HR",
    "Sales",
    "Other"
]

# Experience Level Thresholds (Years)
EXPERIENCE_LEVELS = {
    "Fresher": (0, 1),
    "Junior": (1, 3),
    "Mid-Level": (3, 6),
    "Senior": (6, 100)
}

# Output Configuration
OUTPUT_FOLDER = "outputs"
EXCEL_FILENAME = "categorized_resumes.xlsx"

# Ensure output directory exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
