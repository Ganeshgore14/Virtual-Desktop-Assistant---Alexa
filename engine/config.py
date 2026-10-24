import os
from pathlib import Path

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
env_file = BASE_DIR / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

# User Credentials & Settings
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Alexa")
GENAI_API_KEY = os.getenv("GENAI_API_KEY", "")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
PORCUPINE_ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY", "")