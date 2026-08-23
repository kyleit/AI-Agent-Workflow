"""REST adapter (health/send/recv/list) over urllib."""
from __future__ import annotations

import json
import urllib.request
from urllib.parse import quote

from .config import ClientConfig

# A non-bot User-Agent: Cloudflare's bot-fight blocks "Python-urllib/*" with 403.
USER_AGENT = "msgbus-ws-client/1.0"


class RestClient:
    def __init__(self, config: ClientConfig) -> None:
        self._config = config

    def _request(self, method: str, path: str, data: bytes | None = None,
                 headers: dict | None = None, auth: bool = True) -> bytes:
        h = {"User-Agent": USER_AGENT}
        h.update(headers or {})
        if auth:
            h["X-Token"] = self._config.token
        req = urllib.request.Request(self._config.base_url + path, data=data, method=method, headers=h)
        with urllib.request.urlopen(req) as resp:
            return resp.read()

    def health(self) -> dict:
        return json.loads(self._request("GET", "/health", auth=False))

    def send(self, text: str, to: str | None = None) -> dict:
        # Header values must be latin-1; percent-encode so Vietnamese names survive.
        headers = {"X-From": quote(self._config.sender), "Content-Type": "text/plain; charset=utf-8"}
        if to:
            headers["X-To"] = quote(to)
        return json.loads(self._request("POST", "/send", data=text.encode("utf-8"), headers=headers))

    def recv(self, since: int = 0) -> list:
        return json.loads(self._request("GET", f"/recv?since={since}", headers={"X-From": quote(self._config.sender)}))

    def list_files(self) -> list:
        return json.loads(self._request("GET", "/list"))
