"""HTTP remote control server for MiniPC.

Runs a lightweight HTTP server that serves a mobile-friendly remote control
web page and accepts navigation commands via a simple REST API.
Designed to work on very old browsers (Android 2.3 Kindle Fire Silk).
"""

from __future__ import annotations

import json
import socket
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from PySide6.QtCore import QObject, Signal


# Path to the remote control HTML files
REMOTE_DIR = Path(__file__).resolve().parent.parent / "remote"

# Available commands
VALID_COMMANDS = {
    "up", "down", "left", "right",
    "select", "back", "home",
    "volume_up", "volume_down",
    "play_pause", "mute",
}


class RemoteCommandDispatcher(QObject):
    """Bridges HTTP remote commands to Qt signals.

    Emits command_received(str) with the command name.
    Safe to connect across threads — Qt handles queued delivery.
    """
    command_received = Signal(str)

    def dispatch(self, command: str) -> bool:
        """Dispatch a command. Returns True if valid."""
        if command in VALID_COMMANDS:
            self.command_received.emit(command)
            return True
        return False


class _RemoteHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the remote control server."""

    # Suppress default logging to stdout
    def log_message(self, format, *args):
        pass

    def do_GET(self) -> None:
        path = self.path.rstrip("/")

        # API endpoint: /api/command/<cmd>
        if path.startswith("/api/command/"):
            cmd = path.split("/api/command/", 1)[1]
            dispatcher: RemoteCommandDispatcher = self.server.dispatcher
            if dispatcher.dispatch(cmd):
                self._json_response(200, {"ok": True, "command": cmd})
            else:
                self._json_response(400, {"ok": False, "error": "Unknown command"})
            return

        # API endpoint: /api/status
        if path == "/api/status":
            self._json_response(200, {"ok": True, "app": "MiniPC", "version": "1.0.0"})
            return

        # Serve static files from remote/ directory
        if path == "" or path == "/":
            path = "/index.html"

        file_path = REMOTE_DIR / path.lstrip("/")

        # Security: prevent directory traversal
        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(REMOTE_DIR.resolve())):
                self._text_response(403, "Forbidden")
                return
        except (ValueError, OSError):
            self._text_response(403, "Forbidden")
            return

        if file_path.is_file():
            content_type = self._guess_type(file_path.suffix)
            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)
        else:
            self._text_response(404, "Not Found")

    def _json_response(self, code: int, data: dict) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _text_response(self, code: int, text: str) -> None:
        body = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _guess_type(suffix: str) -> str:
        return {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
        }.get(suffix.lower(), "application/octet-stream")


def get_local_ip() -> str:
    """Get the local network IP address of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class RemoteServer:
    """Manages the HTTP remote control server in a background thread."""

    def __init__(self, dispatcher: RemoteCommandDispatcher, port: int = 8080) -> None:
        self.dispatcher = dispatcher
        self.port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> str:
        """Start the server. Returns the URL to access it."""
        self._server = ThreadingHTTPServer(("0.0.0.0", self.port), _RemoteHandler)
        self._server.dispatcher = self.dispatcher  # type: ignore

        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

        ip = get_local_ip()
        url = f"http://{ip}:{self.port}"
        print(f"[MiniPC] Remote control available at: {url}")
        return url

    def stop(self) -> None:
        """Stop the server."""
        if self._server:
            self._server.shutdown()
            self._server = None

    @property
    def url(self) -> str:
        return f"http://{get_local_ip()}:{self.port}"
