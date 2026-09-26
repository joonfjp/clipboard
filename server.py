#!/usr/bin/env python3
"""local clipboard — a tiny shared clipboard you can reach from any device on your network."""

import argparse
import json
import os
import socket
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAX_BODY = 1_000_000
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/logo.svg": ("logo.svg", "image/svg+xml"),
    "/favicon.ico": ("logo.svg", "image/svg+xml"),
}


class Store:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.clips = json.loads(path.read_text()) if path.exists() else []

    def _save(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.clips))
        os.replace(tmp, self.path)

    def all(self):
        with self.lock:
            return list(self.clips)

    def add(self, text):
        clip = {"id": uuid.uuid4().hex[:12], "text": text, "at": int(time.time() * 1000)}
        with self.lock:
            self.clips.insert(0, clip)
            self._save()
        return clip

    def clear(self):
        with self.lock:
            self.clips = []
            self._save()

    def remove(self, clip_id):
        with self.lock:
            self.clips = [c for c in self.clips if c["id"] != clip_id]
            self._save()


class Handler(BaseHTTPRequestHandler):
    store: Store

    def log_message(self, *args):
        pass

    def _send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, data):
        self._send(code, json.dumps(data).encode())

    def do_GET(self):
        if self.path == "/api/clips":
            return self._json(200, self.store.all())
        if self.path in STATIC:
            name, ctype = STATIC[self.path]
            return self._send(200, (ROOT / name).read_bytes(), ctype)
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/clips":
            return self._json(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_BODY:
            return self._json(413, {"error": "too large"})
        try:
            text = json.loads(self.rfile.read(length))["text"]
        except (ValueError, KeyError, TypeError):
            return self._json(400, {"error": "bad request"})
        if not isinstance(text, str) or not text.strip():
            return self._json(400, {"error": "empty"})
        self._json(201, self.store.add(text))

    def do_DELETE(self):
        if self.path == "/api/clips":
            self.store.clear()
            return self._send(204)
        if not self.path.startswith("/api/clips/"):
            return self._json(404, {"error": "not found"})
        self.store.remove(self.path.rsplit("/", 1)[-1])
        self._send(204)


def lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main():
    p = argparse.ArgumentParser(description="local clipboard server")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--data", default=str(ROOT / "clips.json"), help="where clips are stored")
    args = p.parse_args()

    Handler.store = Store(Path(args.data))
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"local clipboard → http://localhost:{args.port}  ·  http://{lan_ip()}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
