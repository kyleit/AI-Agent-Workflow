import os
from typing import Dict, Type, Optional
from vir_runtime.varbc.application.ports import CDPClientPort
from vir_runtime.varbc.infrastructure.cdp import AsyncCDPClient
from vir_runtime.varbc.infrastructure.drission_adapter import DrissionAdapter
from vir_runtime.varbc.infrastructure.playwright_adapter import PlaywrightAdapter

ADAPTER_REGISTRY: Dict[str, Type[CDPClientPort]] = {
    "async_cdp": AsyncCDPClient,  # DEFAULT
    "drission": DrissionAdapter,
    "playwright": PlaywrightAdapter,
}


def create_browser_adapter(config: Optional[str] = None) -> CDPClientPort:
    """Config-driven factory instantiating CDPClientPort adapter.

    Step-by-step Algorithm:
    1. Determine target adapter key: use `config` parameter if provided, otherwise read env var `VAR_BROWSER_ADAPTER`, falling back to 'async_cdp'.
    2. Lookup key in ADAPTER_REGISTRY (case-insensitive strip).
    3. If key found, instantiate and return adapter instance.
    4. Otherwise raise ValueError(f"Unknown browser adapter '{adapter_key}'. Valid choices are: {list(ADAPTER_REGISTRY.keys())}").
    """
    adapter_key = (config or os.getenv("VAR_BROWSER_ADAPTER", "async_cdp")).strip().lower()
    adapter_cls = ADAPTER_REGISTRY.get(adapter_key)
    if not adapter_cls:
        raise ValueError(
            f"Unknown browser adapter '{adapter_key}'. Valid choices are: {list(ADAPTER_REGISTRY.keys())}"
        )
    return adapter_cls()
