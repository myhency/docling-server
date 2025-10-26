#!/usr/bin/env python3
"""Simple HTTP server for serving static files."""
import os
import http.server
import socketserver
from pathlib import Path

# Configuration
PORT = int(os.getenv("WEB_PORT", "8002"))
DIRECTORY = Path(__file__).parent / "static"

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS support."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        """Add CORS headers to all responses."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[Web Server] {self.address_string()} - {format % args}")


def run_server():
    """Run the static file server."""
    # Ensure static directory exists
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    (DIRECTORY / "figures").mkdir(parents=True, exist_ok=True)

    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"Web server running on http://0.0.0.0:{PORT}")
        print(f"Serving files from: {DIRECTORY}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down web server...")
            httpd.shutdown()


if __name__ == "__main__":
    run_server()
