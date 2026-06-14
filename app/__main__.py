"""
app/__main__.py - Entry point for: python -m app

Loads .env before starting uvicorn.
"""

from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()

# Now start uvicorn
import uvicorn

uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
