from __future__ import annotations

import os


class VirtualFilesystemOverlay:
    """
    FEAT-098: Virtual Filesystem (VFS) Overlay
    RAM-backed memory overlay for virtual file modifications.
    """
    def __init__(self) -> None:
        self.overlay: dict[str, str] = {}

    def write_virtual(self, file_path: str, content: str) -> None:
        self.overlay[file_path] = content

    def read_virtual(self, file_path: str) -> str:
        if file_path in self.overlay:
            return self.overlay[file_path]
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        raise FileNotFoundError(f"File {file_path} not found in VFS or disk.")

    def commit_vfs(self) -> None:
        for file_path, content in list(self.overlay.items()):
            dir_name = os.path.dirname(file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        self.overlay.clear()


__all__ = ["VirtualFilesystemOverlay"]
