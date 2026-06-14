"""
run.py - Start the Video Lab server with .env loaded.

Usage: python run.py [--port PORT]
"""

import sys
import os

# Load .env before importing the app
from dotenv import load_dotenv
load_dotenv()

# Check for --port argument
port = 8000
if "--port" in sys.argv:
    idx = sys.argv.index("--port")
    if idx + 1 < len(sys.argv):
        port = int(sys.argv[idx + 1])

import uvicorn

print(f"Starting Video Lab on port {port}...")
print(f"MINIMAX_API_KEY set: {bool(os.environ.get('MINIMAX_API_KEY'))}")

uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)
