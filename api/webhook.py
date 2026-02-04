"""
Webhook endpoint for earnings call.biz (or any sender).
Receives POST/GET, captures full request (headers, body), saves to Vercel Blob if configured,
and always returns the captured payload so you can see the exact format.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Optional: Vercel Blob for persistent storage (set BLOB_READ_WRITE_TOKEN in Vercel)
try:
    import vercel_blob
    HAS_BLOB = True
except ImportError:
    HAS_BLOB = False


def _read_body(handler):
    """Read request body. Handles chunked or Content-Length."""
    content_length = handler.headers.get("Content-Length")
    if content_length:
        return handler.rfile.read(int(content_length))
    # No Content-Length: read until EOF (some clients send chunked)
    chunks = []
    while True:
        try:
            chunk = handler.rfile.read(8192)
            if not chunk:
                break
            chunks.append(chunk)
        except (ConnectionResetError, BrokenPipeError):
            break
    return b"".join(chunks)


def _headers_dict(handler):
    """Convert request headers to a plain dict (JSON-serializable)."""
    return {k: v for k, v in handler.headers.items()}


def _capture_payload(handler):
    """Capture everything from the request."""
    body_raw = _read_body(handler)
    body_text = body_raw.decode("utf-8", errors="replace") if body_raw else ""
    body_parsed = None
    if body_text.strip():
        try:
            body_parsed = json.loads(body_text)
        except json.JSONDecodeError:
            pass

    parsed = urlparse(handler.path)
    payload = {
        "received_at": datetime.utcnow().isoformat() + "Z",
        "method": handler.command,
        "path": handler.path,
        "query": parse_qs(parsed.query) if parsed.query else {},
        "headers": _headers_dict(handler),
        "body_raw": body_text,
        "body_parsed": body_parsed,
    }
    return payload


def _save_to_blob(payload):
    """Save payload to Vercel Blob if token is set. Returns blob path or None."""
    if not HAS_BLOB or not os.environ.get("BLOB_READ_WRITE_TOKEN"):
        return None
    try:
        prefix = "webhooks/earnings"
        name = f"{prefix}/{payload['received_at'].replace(':', '-').replace('.', '-')}.json"
        data = json.dumps(payload, indent=2).encode("utf-8")
        vercel_blob.put(name, data)
        return name
    except Exception:
        return None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check and instructions."""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        info = {
            "status": "ok",
            "webhook": "Send POST requests to this URL to capture payloads.",
            "usage": "Configure this URL as your webhook in earnings call.biz. Each POST will be captured and returned in the response.",
            "saved": "Set BLOB_READ_WRITE_TOKEN in Vercel to persist payloads; then GET /api/webhooks/list to see them.",
        }
        self.wfile.write(json.dumps(info, indent=2).encode("utf-8"))

    def do_POST(self):
        """Capture webhook payload and optionally save to Blob."""
        payload = _capture_payload(self)
        blob_path = _save_to_blob(payload)

        response = {
            "ok": True,
            "message": "Webhook received and captured.",
            "captured": payload,
        }
        if blob_path:
            response["saved_to"] = blob_path

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))

    def do_PUT(self):
        """Treat like POST for flexibility."""
        self.do_POST()

    def log_message(self, format, *args):
        """Suppress default request logging to avoid noise (optional)."""
        pass
