"""
workflow_runtime/infrastructure/browser/cdp_event_handler.py

Chrome DevTools Protocol event handler and tab locking visual effects.
"""
from __future__ import annotations

import os
from typing import Any

CHROME_BIN: str = os.environ.get("CHROME_BIN", "chrome")
_CDP_SCAN_PORTS: list[int] = [9222, 9223, 9224, 9229, 9230]
_HIGH_PORT_MIN: int = 49152
_HIGH_PORT_MAX: int = 65535


class CDPEventHandler:
    """CDP Event handler mixin for tab locking, element highlighting, and click tracing."""

    def _eval_js_safe(self, script: str) -> Any:
        eval_fn: Any = getattr(self, "eval_js", None)
        if callable(eval_fn):
            return eval_fn(script)
        return None

    def lock_tab(self, message: str = "Initializing…") -> None:
        lock_js = str(getattr(self, "_LOCK_JS", ""))
        self._eval_js_safe(lock_js)
        self.update_status(message)

    def unlock_tab(self) -> None:
        unlock_js = str(getattr(self, "_UNLOCK_JS", ""))
        self._eval_js_safe(unlock_js)

    def update_status(self, message: str, step: int | None = None, total: int | None = None) -> None:
        safe = message.replace("'", "\\'").replace("\n", " ")
        prefix = f"[{step}/{total}] " if step is not None and total is not None else ""
        js = f"""
(function(){{
  var el = document.getElementById('__ag_step__');
  if (!el) return;
  el.style.opacity = '0.4';
  el.style.transform = 'translateX(-4px)';
  el.style.transition = 'all .15s ease';
  setTimeout(function(){{
    el.textContent = '{prefix}{safe}';
    el.style.opacity = '1';
    el.style.transform = 'translateX(0)';
  }}, 150);
}})();
"""
        self._eval_js_safe(js)

    def highlight_element(self, selector: str, label: str = "") -> None:
        safe_sel = selector.replace("'", "\\'")
        safe_lbl = label.replace("'", "\\'")
        js = f"""
(function(){{
  var old = document.getElementById('__ag_hl__');
  if (old) old.remove();
  var el = document.querySelector('{safe_sel}');
  if (!el) return;
  var r = el.getBoundingClientRect();
  var hl = document.createElement('div');
  hl.id = '__ag_hl__';
  hl.style.cssText = [
    'position:fixed',
    'left:'+(r.left-3)+'px','top:'+(r.top-3)+'px',
    'width:'+(r.width+6)+'px','height:'+(r.height+6)+'px',
    'border:2px solid #38bdf8',
    'border-radius:6px',
    'box-shadow:0 0 0 4px rgba(56,189,248,0.18),0 0 16px rgba(56,189,248,0.25)',
    'pointer-events:none','z-index:2147483648',
    'transition:all .2s ease',
  ].join(';');
  if ('{safe_lbl}') {{
    var tag = document.createElement('div');
    tag.textContent = '{safe_lbl}';
    tag.style.cssText = [
      'position:absolute','top:-22px','left:0',
      'background:#0f172a','color:#38bdf8',
      'font-size:11px','font-family:system-ui,sans-serif',
      'padding:2px 8px','border-radius:4px',
      'border:1px solid rgba(56,189,248,0.35)',
      'white-space:nowrap',
    ].join(';');
    hl.appendChild(tag);
  }}
  document.body.appendChild(hl);
  setTimeout(function(){{ hl.style.opacity='0'; setTimeout(function(){{hl.remove();}},400); }}, 3000);
}})();
"""
        self._eval_js_safe(js)

    def agent_click_trace(self, x: float, y: float, label: str = "") -> None:
        safe_lbl = label.replace("'", "\\'")
        js = f"""
(function(){{
  var ring = document.createElement('div');
  ring.style.cssText = [
    'position:fixed',
    'left:{x-16}px','top:{y-16}px',
    'width:32px','height:32px','border-radius:50%',
    'border:2px solid #38bdf8',
    'background:rgba(56,189,248,0.15)',
    'pointer-events:none','z-index:2147483649',
    'animation:ag-ripple .6s ease-out forwards',
  ].join(';');
  document.body.appendChild(ring);
  if ('{safe_lbl}') {{
    var tip = document.createElement('div');
    tip.textContent = '👆 {safe_lbl}';
    tip.style.cssText = [
      'position:fixed',
      'left:{x+18}px','top:{y-10}px',
      'background:#0f172a','color:#38bdf8',
      'font-size:11px','font-family:system-ui,sans-serif',
      'padding:2px 8px','border-radius:4px',
      'border:1px solid rgba(56,189,248,0.3)',
      'pointer-events:none','z-index:2147483649',
      'animation:ag-highlight-fade 1.5s ease forwards',
    ].join(';');
    document.body.appendChild(tip);
    setTimeout(function(){{tip.remove();}},1600);
  }}
  setTimeout(function(){{ring.remove();}},700);
}})();
"""
        self._eval_js_safe(js)


__all__ = ["CDPEventHandler", "CHROME_BIN"]
