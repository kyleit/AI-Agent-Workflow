"""Composition root: the only place concrete adapters are constructed (DI wiring)."""
from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path

from ..application.bus_service import BusService
from ..infrastructure.file_system_store import FileSystemStore
from ..infrastructure.jsonl_message_store import JsonlMessageStore
from ..infrastructure.memory_registry import MemoryRegistry
from ..infrastructure.system_clock import SystemClock
from ..infrastructure.tus_upload_store import TusUploadStore
from .http_handler import make_handler


def build_service(store: Path) -> tuple[BusService, TusUploadStore]:
    store = Path(store)
    files = FileSystemStore(store / "files")
    uploads = TusUploadStore(store / "uploads")
    messages = JsonlMessageStore(store / "messages.jsonl")
    service = BusService(messages, files, MemoryRegistry(), SystemClock())
    return service, uploads


def create_server(bind: str, port: int, store: Path, token: str) -> ThreadingHTTPServer:
    service, uploads = build_service(store)
    httpd = ThreadingHTTPServer((bind, port), make_handler(service, uploads, token))
    httpd.daemon_threads = True
    return httpd
