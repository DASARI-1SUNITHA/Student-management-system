"""Vercel entry point: serves the FastAPI backend under /api on the same domain as the React app.
 
Vercel maps api/index.py to /api only, so vercel.json rewrites every /api/... request here and passes the
original sub-path in a "__path" query parameter. RestorePath puts it back before FastAPI routes the request.
"""
import os
import sys
from urllib.parse import parse_qsl, urlencode
 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
 
from fastapi import FastAPI  # noqa: E402
 
from app.main import app as backend  # noqa: E402
 
inner = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
inner.mount("/api", backend)  # /api/auth/login -> backend route /auth/login ; Swagger at /api/docs
 
 
class RestorePath:
    def __init__(self, asgi_app):
        self.app = asgi_app
 
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            pairs = parse_qsl(scope.get("query_string", b"").decode(), keep_blank_values=True)
            values = dict(pairs)
            if "__path" in values:
                rest = values["__path"].lstrip("/")
                scope = dict(scope)
                scope["path"] = "/api/" + rest
                scope["raw_path"] = scope["path"].encode()
                scope["query_string"] = urlencode([(k, v) for k, v in pairs if k != "__path"]).encode()
        await self.app(scope, receive, send)
 
 
app = RestorePath(inner)
