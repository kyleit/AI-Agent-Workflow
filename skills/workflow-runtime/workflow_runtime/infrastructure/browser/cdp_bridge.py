"""
workflow_runtime.infrastructure.browser.cdp_bridge
===================================================
CDP WebSocket bridge sử dụng websocket-client.
Cung cấp giao diện đồng bộ để điều khiển Chrome qua CDP.
"""
from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

import websocket

CHROME_BIN: str = os.environ.get("CHROME_BIN", "chrome")
_CDP_SCAN_PORTS: list[int] = [9222, 9223, 9224, 9229, 9230]
_HIGH_PORT_MIN: int = 49152
_HIGH_PORT_MAX: int = 65535

from workflow_runtime.infrastructure.browser.cdp_event_handler import (
    CDPEventHandler)


class CDPBridge(CDPEventHandler):
    """Giao tiếp đồng bộ với Chrome qua CDP WebSocket."""

    def __init__(self, ws_url: str, timeout: float = 10.0) -> None:
        self.ws_url = ws_url
        self.timeout = timeout
        self._id = 0
        self._ws: websocket.WebSocket | None = None

    def connect(self) -> CDPBridge:
        parsed = urlparse(self.ws_url)
        origin = f"http://{parsed.hostname}:{parsed.port}" if parsed.port else f"http://{parsed.hostname}"
        create_fn: Any = getattr(websocket, "create_connection", None)
        if callable(create_fn):
            self._ws = cast(websocket.WebSocket, create_fn(
                self.ws_url,
                timeout=self.timeout,
                origin=origin,
            ))
        return self

    def close(self) -> None:
        if self._ws is not None:
            try:
                self._ws.close()
            except Exception:
                pass

    def __enter__(self) -> CDPBridge:
        return self.connect()

    def __exit__(self, *_: Any) -> None:
        self.close()

    def send(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Gửi lệnh CDP và chờ response tương ứng (theo id)."""
        if self._ws is None:
            return {}

        self._id += 1
        msg_id = self._id
        payload = json.dumps({"id": msg_id, "method": method, "params": params or {}})
        self._ws.send(payload)

        deadline = time.time() + self.timeout
        while time.time() < deadline:
            try:
                self._ws.settimeout(max(0.5, deadline - time.time()))
                raw = self._ws.recv()
                msg = cast(dict[str, Any], json.loads(raw)) if isinstance(raw, str) else {}
                if msg.get("id") == msg_id:
                    res = msg.get("result", {})
                    return cast(dict[str, Any], res) if isinstance(res, dict) else {}
            except websocket.WebSocketTimeoutException:
                break
            except Exception:
                break
        return {}

    def navigate(self, url: str, wait: float = 2.5) -> None:
        self.send("Page.navigate", {"url": url})
        time.sleep(wait)

    def eval_js(self, js: str) -> str:
        res = self.send("Runtime.evaluate", {"expression": js, "returnByValue": True})
        raw_val = res.get("result")
        val_dict: dict[str, Any] = cast(dict[str, Any], raw_val) if isinstance(raw_val, dict) else {}
        return str(val_dict.get("value", ""))

    def evaluate(self, js: str) -> str:
        return self.eval_js(js)

    def screenshot(self, out_path: str) -> bool:
        """Chụp ảnh màn hình PNG. Trả về True nếu thành công."""
        res = self.send("Page.captureScreenshot", {"format": "png"})
        data = str(res.get("data", ""))
        if data:
            img = base64.b64decode(data)
            Path(out_path).write_bytes(img)
            return True
        return False

    def find_element(self, selector: str) -> dict[str, Any] | None:
        """
        Tìm element bằng CSS selector, trả về center (x, y) + rect.
        Dùng để biết toạ độ trước khi click/type.
        """
        js = f"""
(function(){{
    var el = document.querySelector({repr(selector)});
    if (!el) return null;
    var r = el.getBoundingClientRect();
    return JSON.stringify({{
        x: Math.round(r.left + r.width/2),
        y: Math.round(r.top  + r.height/2),
        width: Math.round(r.width),
        height: Math.round(r.height),
        tag: el.tagName,
        text: (el.innerText || el.value || '').substring(0, 80)
    }});
}})()
"""
        raw = self.eval_js(js)
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            return cast(dict[str, Any], parsed) if isinstance(parsed, dict) else None
        except Exception:
            return None

    def real_click(self, x: int, y: int) -> None:
        """CDP mouse click thật tại toạ độ (x, y) — giống người dùng click."""
        for etype in ("mousePressed", "mouseReleased"):
            self.send("Input.dispatchMouseEvent", {
                "type": etype, "x": x, "y": y,
                "button": "left", "clickCount": 1,
                "modifiers": 0,
            })
        time.sleep(0.05)

    def real_type(self, text: str, delay: float = 0.04) -> None:
        """Gõ từng ký tự bằng CDP KeyEvent thật — giống người gõ bàn phím."""
        for ch in text:
            self.send("Input.dispatchKeyEvent", {
                "type": "keyDown", "text": ch,
                "unmodifiedText": ch, "key": ch,
            })
            self.send("Input.dispatchKeyEvent", {
                "type": "keyUp", "text": ch,
                "unmodifiedText": ch, "key": ch,
            })
            time.sleep(delay)

    def click_element(self, selector: str, label: str = "") -> bool:
        """
        Tìm element, click thật vào center — kết hợp mắt (find) + tay (click).
        Trả về True nếu click thành công.
        """
        el = self.find_element(selector)
        if not el:
            print(f"  [eyes] Không tìm thấy: {label or selector}")
            return False
        x = int(cast(int, el["x"]))
        y = int(cast(int, el["y"]))
        text_str = str(el.get("text", ""))[:40]
        print(f"  [hand] Click {label or selector} tại ({x}, {y}) — {text_str!r}")
        self.real_click(x, y)
        return True

    def type_into(self, selector: str, text: str, label: str = "", clear: bool = True) -> bool:
        """
        Tìm input, click vào đó, xoá nếu cần, gõ text thật bằng bàn phím.
        Kết hợp mắt (find) + tay (click) + mũi (type).
        """
        el = self.find_element(selector)
        if not el:
            print(f"  [eyes] Input không thấy: {label or selector}")
            return False
        x = int(cast(int, el["x"]))
        y = int(cast(int, el["y"]))
        print(f"  [hand] Click input '{label or selector}' tại ({x}, {y})")
        self.real_click(x, y)
        time.sleep(0.1)
        if clear:
            self.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "modifiers": 2})
            self.send("Input.dispatchKeyEvent", {"type": "keyUp",   "key": "a", "modifiers": 2})
            self.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Delete"})
            self.send("Input.dispatchKeyEvent", {"type": "keyUp",   "key": "Delete"})
            time.sleep(0.05)
        print(f"  [nose] Type: {text!r}")
        self.real_type(text)
        return True

    def dom_issues(self) -> str:
        """Phân tích DOM tìm overflow/zero-height. Trả về 'OK' nếu không có lỗi."""
        js = r"""
(function(){
  var issues=[];
  var bw=(document.body||{}).offsetWidth||1280;
  var els=document.querySelectorAll('*');
  for(var i=0;i<Math.min(els.length,300);i++){
    var el=els[i],r=el.getBoundingClientRect&&el.getBoundingClientRect();
    if(r&&r.width>bw+10&&['SCRIPT','STYLE','HEAD','META','LINK'].indexOf(el.tagName)<0){
      var cn=typeof el.className==='string'?el.className.trim().split(' ')[0]:'';
      issues.push('OVF:'+el.tagName+(cn?'.'+cn:''));
    }
  }
  document.querySelectorAll('main,section,.card,.panel,.container').forEach(function(el){
    if(el.offsetHeight===0) issues.push('ZERO:'+el.className.trim().split(' ')[0]);
  });
  return issues.length?issues.slice(0,6).join(' | '):'OK';
})()
"""
        return self.eval_js(js) or "?"


__all__ = ["CHROME_BIN", "CDPBridge"]
