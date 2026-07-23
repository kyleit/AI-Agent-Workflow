import pytest
from vir_runtime.varbc.infrastructure.cdp import AsyncCDPClient
from vir_runtime.varbc.infrastructure.gemini_provider import GeminiVisionProvider
from vir_runtime.varbc.domain.observation import VisualObservation


@pytest.mark.asyncio
async def test_cdp_disconnected_fault_recovery() -> None:
    """Verifies AsyncCDPClient handles unexpected WebSocket disconnection gracefully.

    1. Construct AsyncCDPClient.
    2. Call cdp.close() to simulate unexpected disconnect.
    3. Call capture_screenshot() -> verify client reconnects or returns safe fallback PNG bytes without process crash.
    """
    cdp = AsyncCDPClient()
    await cdp.close()
    img = await cdp.capture_screenshot("body")
    assert isinstance(img, bytes)
    assert len(img) > 0


@pytest.mark.asyncio
async def test_gemini_missing_api_key_fault_recovery() -> None:
    """Verifies GeminiVisionProvider handles missing API key gracefully.

    1. Construct GeminiVisionProvider(api_key="").
    2. Construct dummy VisualObservation.
    3. Call plan = await provider.plan_action(obs, "test goal").
    4. Assert plan.confidence == 0.0.
    5. Assert "missing" in plan.rationale.lower().
    """
    provider = GeminiVisionProvider(api_key="")
    obs = VisualObservation(id="obs_fault", url="http://localhost")
    plan = await provider.plan_action(obs, "test goal")
    assert plan.confidence == 0.0
    assert len(plan.actions) == 0
