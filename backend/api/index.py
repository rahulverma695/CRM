import sys
import os

# Ensure the backend root is on sys.path so `app.*` imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: F401  — Vercel picks up this `app` ASGI callable
