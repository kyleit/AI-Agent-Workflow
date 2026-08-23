from __future__ import annotations

import asyncio
from typing import Any, Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from workflow_runtime.domain.interfaces.watcher import IFileWatcher


class _DebouncedHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str], None], debounce_seconds: float = 0.05) -> None:
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self._timer: asyncio.TimerHandle | None = None

    def on_modified(self, event: Any) -> None:
        src_path = str(getattr(event, "src_path", ""))
        is_dir = bool(getattr(event, "is_directory", False))
        if not is_dir and (src_path.endswith(".vir.yaml") or src_path.endswith(".vir.json")):
            if self._timer:
                self._timer.cancel()
            try:
                loop = asyncio.get_running_loop()
                self._timer = loop.call_later(self.debounce_seconds, self.callback, src_path)
            except RuntimeError:
                pass


class WatchdogFileWatcher(IFileWatcher):
    def __init__(self) -> None:
        self.observer = Observer()

    def watch(self, path: str, callback: Callable[[str], None]) -> None:
        handler = _DebouncedHandler(callback)
        self.observer.schedule(handler, path, recursive=True)
        self.observer.start()

    def stop(self) -> None:
        self.observer.stop()
        self.observer.join()


__all__ = [
    "WatchdogFileWatcher",
]
