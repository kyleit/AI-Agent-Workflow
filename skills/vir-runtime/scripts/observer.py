"""Legacy wrapper script for observation captures."""

import os
import sys
import warnings
import asyncio
from typing import Dict, Any

# Ensure script directory is in sys.path for vir_runtime package imports
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from vir_runtime.varbc.infrastructure.cdp import AsyncCDPClient


def capture_observation(url: str, selector: str = "body") -> Dict[str, Any]:
    """Legacy function wrapper forwarding screenshot captures to AsyncCDPClient."""
    warnings.warn(
        "observer.py is deprecated; please use 'python var_dispatch.py run' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    cdp = AsyncCDPClient()

    async def _exec():
        await cdp.navigate(url)
        img = await cdp.capture_screenshot(selector)
        dom = await cdp.get_dom_snapshot()
        return {"url": url, "dom_snippet": dom[:100], "image_size": len(img)}

    return asyncio.run(_exec())
