"""Vercel entry point: serves the FastAPI backend under /api on the same domain as the React app."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi import FastAPI  # noqa: E402

from app.main import app as backend  # noqa: E402

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/api", backend)  # /api/auth/login -> backend route /auth/login; docs at /api/docs
