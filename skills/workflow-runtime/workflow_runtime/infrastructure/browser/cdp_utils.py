from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, cast

import websocket  # websocket-client

CHROME_BIN: str = os.environ.get("CHROME_BIN", "chrome")
_CDP_SCAN_PORTS: list[int] = [9222, 9223, 9224, 9229, 9230]
_HIGH_PORT_MIN: int = 49152
_HIGH_PORT_MAX: int = 65535


def get_free_port() -> int:
    import random
    for _ in range(20):
        candidate = random.randint(_HIGH_PORT_MIN, _HIGH_PORT_MAX)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", candidate))
                return candidate
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(s.getsockname()[1])


def detect_cdp_port() -> int | None:
    for port in _CDP_SCAN_PORTS:
        try:
            urllib.request.urlopen(
                f"http://localhost:{port}/json/version", timeout=1
            )
            return port
        except Exception:
            continue
    return None


def is_cdp_ready(port: int) -> bool:
    try:
        urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=2)
        return True
    except Exception:
        return False


def is_chrome_windowed(port: int) -> bool:
    try:
        import json as _json
        with urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=2) as r:
            info = _json.loads(r.read())
        if isinstance(info, dict):
            info_dict = cast(dict[str, Any], info)
            ua = str(info_dict.get("User-Agent", ""))
            if "Headless" in ua:
                return False
        with urllib.request.urlopen(f"http://localhost:{port}/json/list", timeout=2) as r:
            tabs = _json.loads(r.read())
        raw_tabs = cast(list[Any], tabs) if isinstance(tabs, list) else []
        pages: list[dict[str, Any]] = []
        for t in raw_tabs:
            if isinstance(t, dict):
                t_dict = cast(dict[str, Any], t)
                if t_dict.get("type") == "page":
                    pages.append(t_dict)
        return len(pages) > 0
    except Exception:
        return False


def get_page_tab(port: int) -> dict[str, Any]:
    with urllib.request.urlopen(f"http://localhost:{port}/json/list", timeout=5) as r:
        tabs = json.loads(r.read())
    raw_tabs = cast(list[Any], tabs) if isinstance(tabs, list) else []
    pages: list[dict[str, Any]] = []
    for t in raw_tabs:
        if isinstance(t, dict):
            t_dict = cast(dict[str, Any], t)
            if t_dict.get("type") == "page":
                pages.append(t_dict)
    if not pages:
        raise RuntimeError("Không có page tab nào trong Chrome!")
    for t in pages:
        url = str(t.get("url", ""))
        if "localhost" in url or "127.0.0.1" in url:
            return t
    return pages[0]


def detect_base_url(tab: dict[str, Any]) -> str:
    from urllib.parse import urlparse
    tab_url = str(tab.get("url", "http://localhost:5173"))
    p = urlparse(tab_url)
    return f"{p.scheme}://{p.hostname}:{p.port}"


def _bring_chrome_to_front() -> None:
    import sys as _sys
    if _sys.platform == "win32":
        ps = r"""
$sig = @'
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
}
'@
Add-Type -TypeDefinition $sig -Language CSharp -ErrorAction SilentlyContinue
$procs = Get-Process chrome -ErrorAction SilentlyContinue |
         Where-Object { $_.MainWindowHandle -ne 0 } |
         Sort-Object StartTime -Descending
foreach ($p in $procs) {
    [Win32]::ShowWindow($p.MainWindowHandle, 9)
    [Win32]::BringWindowToTop($p.MainWindowHandle)
    [Win32]::SetForegroundWindow($p.MainWindowHandle)
    break
}
"""
        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
    elif _sys.platform == "darwin":
        script = 'tell application "Google Chrome" to activate'
        try:
            subprocess.Popen(
                ["osascript", "-e", script],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
    else:
        try:
            subprocess.Popen(
                ["wmctrl", "-a", "Google Chrome"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            try:
                subprocess.Popen(
                    ["xdotool", "search", "--class", "google-chrome",
                     "windowactivate", "--sync"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            except FileNotFoundError:
                pass


def launch_chrome(app_url: str, profile_dir: Path, port: int | None = None) -> tuple[subprocess.Popen[Any], int]:
    actual_port = port if port is not None else get_free_port()
    profile_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        CHROME_BIN,
        f"--remote-debugging-port={actual_port}",
        f"--user-data-dir={profile_dir}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-popup-blocking",
        "--disable-extensions",
        "--start-maximized",
        "--new-window",
        app_url,
    ]
    print(f"[CDP] 🚀 Khởi động Chrome trên port {actual_port}...")

    if sys.platform == "win32":
        proc = subprocess.Popen(
            ["cmd", "/c", "start", "", *cmd],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    else:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for i in range(20):
        time.sleep(1.0)
        if is_cdp_ready(actual_port):
            print(f"[CDP] ✅ Chrome + CDP sẵn sàng sau {i+1}s (port {actual_port})")
            time.sleep(1.5)
            _bring_chrome_to_front()
            return proc, actual_port
        print(f"[CDP] ⏳ Đợi Chrome... ({i+1}/20)")
    raise RuntimeError(f"Chrome khởi động thất bại trên port {actual_port}!")


def ensure_chrome(
    app_url: str,
    profile_dir: Path,
) -> tuple[subprocess.Popen[Any] | None, int]:
    for candidate_port in _CDP_SCAN_PORTS:
        if not is_cdp_ready(candidate_port):
            continue
        if not is_chrome_windowed(candidate_port):
            print(f"[CDP] ⏭️  Port {candidate_port}: headless/IDE process — bỏ qua")
            continue
        try:
            tab = get_page_tab(candidate_port)
            ws_url = str(tab.get("webSocketDebuggerUrl", ""))
            ws_create: Any = getattr(websocket, "create_connection", None)
            if callable(ws_create):
                test_ws: Any = ws_create(ws_url, timeout=3)
                if hasattr(test_ws, "close"):
                    test_ws.close()
            print(f"[CDP] ✅ Chrome windowed ở port {candidate_port} — reuse")
            return None, candidate_port
        except Exception as e:
            print(f"[CDP] ⚠️  WS không kết nối được (port {candidate_port}): {e} — bỏ qua")
            continue

    print("[CDP] 🚀 Không tìm thấy Chrome windowed phù hợp — mở Chrome mới...")
    return launch_chrome(app_url, profile_dir, port=None)


__all__ = [
    "CHROME_BIN",
    "get_free_port",
    "detect_cdp_port",
    "is_cdp_ready",
    "is_chrome_windowed",
    "get_page_tab",
    "detect_base_url",
    "launch_chrome",
    "ensure_chrome",
]
