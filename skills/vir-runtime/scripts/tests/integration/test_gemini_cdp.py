import pytest
from vir_runtime.varbc.domain.observation import VisualObservation
from vir_runtime.varbc.domain.action import ActionPlan
from vir_runtime.varbc.infrastructure.cdp import AsyncCDPClient
from vir_runtime.varbc.infrastructure.adapter_factory import create_browser_adapter
from vir_runtime.varbc.infrastructure.gemini_provider import GeminiVisionProvider


@pytest.mark.asyncio
async def test_async_cdp_client_fallback():
    client = AsyncCDPClient()
    await client.connect()
    await client.navigate("http://example.com")
    screenshot = await client.capture_screenshot()
    dom = await client.get_dom_snapshot()
    errors = await client.get_console_errors()
    await client.close()

    assert len(screenshot) > 0
    assert "<html>" in dom
    assert isinstance(errors, list)


def test_adapter_factory_selection():
    adapter = create_browser_adapter("async_cdp")
    assert isinstance(adapter, AsyncCDPClient)

    with pytest.raises(ValueError):
        create_browser_adapter("non_existent_adapter")


@pytest.mark.asyncio
async def test_gemini_vision_provider_fallback_without_api_key():
    provider = GeminiVisionProvider(api_key="")
    obs = VisualObservation(id="obs-test", url="http://example.com")

    plan = await provider.plan_action(obs, goal="Find search input")

    assert isinstance(plan, ActionPlan)
    assert plan.confidence == 0.0
    assert "missing" in plan.rationale.lower()
