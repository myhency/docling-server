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
API_PORT = int(os.getenv("API_PORT", "8001"))

# Web server settings (for static files) - DEPRECATED
WEB_SERVER_URL = os.getenv("WEB_SERVER_URL", "http://localhost:8002")

# API server URL (for authenticated image access)
API_SERVER_URL = os.getenv("API_SERVER_URL", "http://localhost:8001")

# File upload settings
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".pptx",
    ".html", ".htm", ".md", ".csv",
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"
}

# Server URL for generating figure URLs (now points to authenticated API endpoint)
SERVER_URL = API_SERVER_URL

# IP-based Access Control
# Only requests from these IPs will be allowed to access protected endpoints
# Supports individual IPs and CIDR notation
# Default includes: localhost (127.0.0.1, ::1) and Docker networks (172.16.0.0/12, 192.168.0.0/16)
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "127.0.0.1,::1,172.16.0.0/12,192.168.0.0/16,10.0.0.0/8").split(",")

# You can also allow entire subnets:
# Example: "127.0.0.1,::1,192.168.1.0/24,10.0.0.0/8"

# If you want to allow all IPs (not recommended for production), set:
# ALLOWED_IPS = ["0.0.0.0/0", "::/0"]
