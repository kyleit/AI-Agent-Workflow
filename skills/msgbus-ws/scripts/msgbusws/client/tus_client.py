"""Resumable file transfer: tus 1.0.0 uploader + HTTP Range downloader."""
from __future__ import annotations

import base64
import os
import urllib.error
import urllib.request
from pathlib import Path

from .config import ClientConfig
from .rest_client import USER_AGENT

CHUNK = 1024 * 1024  # 1 MiB


class TusUploader:
    def __init__(self, config: ClientConfig) -> None:
        self._config = config

    def _headers(self, extra: dict | None = None) -> dict:
        headers = {"User-Agent": USER_AGENT, "X-Token": self._config.token, "Tus-Resumable": "1.0.0"}
        headers.update(extra or {})
        return headers

    def _head_offset(self, upload_url: str) -> int:
        req = urllib.request.Request(upload_url, method="HEAD", headers=self._headers())
        with urllib.request.urlopen(req) as resp:
            return int(resp.headers.get("Upload-Offset", "0"))

    def upload(self, path: str, to: str | None = None) -> dict:
        source = Path(path)
        size = source.stat().st_size
        meta = [
            f"filename {base64.b64encode(source.name.encode()).decode()}",
            f"from {base64.b64encode(self._config.sender.encode()).decode()}",
        ]
        if to:
            meta.append(f"to {base64.b64encode(to.encode()).decode()}")
        create = urllib.request.Request(
            self._config.base_url + "/files", method="POST",
            headers=self._headers({"Upload-Length": str(size), "Upload-Metadata": ",".join(meta),
                                   "Content-Length": "0"}),
        )
        with urllib.request.urlopen(create) as resp:
            location = resp.headers.get("Location", "")
        upload_url = self._config.base_url + location if location.startswith("/") else location

        offset = 0
        with source.open("rb") as f:
            while offset < size:
                f.seek(offset)
                chunk = f.read(CHUNK)
                patch = urllib.request.Request(
                    upload_url, data=chunk, method="PATCH",
                    headers=self._headers({"Content-Type": "application/offset+octet-stream",
                                           "Upload-Offset": str(offset)}),
                )
                try:
                    with urllib.request.urlopen(patch) as resp:
                        offset = int(resp.headers.get("Upload-Offset", offset + len(chunk)))
                except urllib.error.HTTPError as exc:
                    if exc.code == 409:  # offset conflict -> resync and retry
                        offset = self._head_offset(upload_url)
                        continue
                    raise
        return {"name": source.name, "size": size, "location": location}


class RangeDownloader:
    def __init__(self, config: ClientConfig) -> None:
        self._config = config

    def download(self, name: str, out: str | None = None) -> dict:
        out_path = Path(out or name)
        part = out_path.with_suffix(out_path.suffix + ".part")
        start = part.stat().st_size if part.exists() else 0
        headers = {"User-Agent": USER_AGENT, "X-Token": self._config.token}
        if start:
            headers["Range"] = f"bytes={start}-"
        req = urllib.request.Request(self._config.base_url + f"/download?name={name}", headers=headers)
        with urllib.request.urlopen(req) as resp:
            resumed = resp.status == 206
            mode = "ab" if (start and resumed) else "wb"
            with part.open(mode) as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
        os.replace(part, out_path)
        return {"name": name, "out": str(out_path), "size": out_path.stat().st_size}
