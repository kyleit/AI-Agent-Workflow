"""Integration test suite for var_dispatch.py CLI bridge and legacy script wrappers."""

import os
import sys
import pytest
import warnings
from unittest.mock import AsyncMock, patch

# Ensure skills/vir-runtime/scripts is in sys.path
script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from var_dispatch import create_parser, main_async
from loop import run_legacy_loop
from observer import capture_observation
from evaluator import evaluate_quality


def test_cli_parser_help():
    """Verify var_dispatch parser constructs valid arguments."""
    parser = create_parser()
    args = parser.parse_args(["run", "--url", "http://localhost:8080", "--selector", "div.main"])
    assert args.subcommand == "run"
    assert args.url == "http://localhost:8080"
    assert args.selector == "div.main"


@pytest.mark.asyncio
async def test_cli_dispatch_run_subcommand():
    """Verify var_dispatch run subcommand executes and outputs observation."""
    parser = create_parser()
    args = parser.parse_args(["run", "--url", "http://localhost:8080"])
    
    with patch("var_dispatch.VARService.capture_screenshot", new_callable=AsyncMock) as mock_capture:
        from vir_runtime.varbc.domain.observation import VisualObservation
        mock_obs = VisualObservation(
            id="obs-123",
            url="http://localhost:8080",
            screenshot_path="docs/reports/assets/obs-123.png",
            dom_snapshot="<html></html>",
        )
        mock_capture.return_value = (mock_obs, "docs/reports/assets/obs-123.png")
        
        exit_code = await main_async(args)
        assert exit_code == 0
        mock_capture.assert_called_once_with("http://localhost:8080", "body")


def test_legacy_evaluator_wrapper():
    """Verify evaluator.py emits DeprecationWarning and returns quality score dict."""
    with pytest.warns(DeprecationWarning, match="evaluator.py is deprecated"):
        res = evaluate_quality(90.0, 90.0, 100.0)
        assert "weighted_score" in res
        assert "passed" in res
        assert res["passed"] is True


def test_legacy_observer_wrapper():
    """Verify observer.py emits DeprecationWarning and returns observation metadata."""
    with pytest.warns(DeprecationWarning, match="observer.py is deprecated"):
        with patch("vir_runtime.varbc.infrastructure.cdp.AsyncCDPClient.navigate", new_callable=AsyncMock), \
             patch("vir_runtime.varbc.infrastructure.cdp.AsyncCDPClient.capture_screenshot", new_callable=AsyncMock) as mock_ss, \
             patch("vir_runtime.varbc.infrastructure.cdp.AsyncCDPClient.get_dom_snapshot", new_callable=AsyncMock) as mock_dom:
            mock_ss.return_value = b"fake-png"
            mock_dom.return_value = "<html><body>Test</body></html>"
            
            res = capture_observation("http://localhost:8080")
            assert res["url"] == "http://localhost:8080"
            assert "dom_snippet" in res
            assert res["image_size"] == len(b"fake-png")


def test_legacy_loop_wrapper():
    """Verify loop.py emits DeprecationWarning and executes agent loop."""
    with pytest.warns(DeprecationWarning, match="loop.py is deprecated"):
        with patch("vir_runtime.varbc.application.agent.VARAgentLoop.run", new_callable=AsyncMock) as mock_run:
            from vir_runtime.varbc.domain.report import VARReport, VARStatus
            mock_report = VARReport(
                id="rep-999",
                status=VARStatus.PASS,
                passed=True,
                score=95.0,
            )
            mock_run.return_value = mock_report
            
            res = run_legacy_loop("http://localhost:8080", "Test goal")
            assert res["id"] == "rep-999"
            assert res["passed"] is True
