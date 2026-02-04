"""
List saved webhook payloads from Vercel Blob (when BLOB_READ_WRITE_TOKEN is set).
GET /api/webhooks/list?limit=20
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs

try:
    import vercel_blob
    HAS_BLOB = True
except ImportError:
    HAS_BLOB = False


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        if not HAS_BLOB or not os.environ.get("BLOB_READ_WRITE_TOKEN"):
            out = {
                "ok": False,
                "message": "Vercel Blob not configured. Set BLOB_READ_WRITE_TOKEN to persist and list webhooks.",
                "blobs": [],
            }
            self.wfile.write(json.dumps(out, indent=2).encode("utf-8"))
            return

        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        limit = min(int(qs.get("limit", ["20"])[0]), 100)

        try:
            result = vercel_blob.list({"limit": str(limit)})
            blobs = result.get("blobs", [])
            # Filter to our webhook prefix if we got more than we need
            blobs = [b for b in blobs if (b.get("pathname") or "").startswith("webhooks/earnings/")][:limit]
            out = {
                "ok": True,
                "count": len(blobs),
                "blobs": [
                    {
                        "pathname": b.get("pathname"),
                        "url": b.get("url"),
                        "uploadedAt": b.get("uploadedAt"),
                        "size": b.get("size"),
                    }
                    for b in blobs
                ],
            }
        except Exception as e:
            out = {"ok": False, "error": str(e), "blobs": []}

        self.wfile.write(json.dumps(out, indent=2).encode("utf-8"))
