"""Configuration settings for the document converter service."""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
FIGURES_DIR = STATIC_DIR / "figures"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# File upload settings
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".pptx",
    ".html", ".htm", ".md", ".csv",
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"
}

# Server URL for generating figure URLs
SERVER_URL = os.getenv("SERVER_URL", f"http://localhost:{API_PORT}")
