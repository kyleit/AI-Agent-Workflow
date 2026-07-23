"""Legacy wrapper script for VARAgentLoop."""

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
from vir_runtime.varbc.infrastructure.gemini_provider import GeminiVisionProvider
from vir_runtime.varbc.infrastructure.report_repo import FileReportRepo
from vir_runtime.varbc.application.investigator import VARInvestigator
from vir_runtime.varbc.application.verifier import VARVerifier
from vir_runtime.varbc.application.agent import VARAgentLoop


def run_legacy_loop(url: str, goal: str, max_steps: int = 10) -> Dict[str, Any]:
    """Legacy function wrapper forwarding calls to VARAgentLoop."""
    warnings.warn(
        "loop.py is deprecated; please use 'python var_dispatch.py agent' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    cdp = AsyncCDPClient()
    llm = GeminiVisionProvider()
    repo = FileReportRepo()
    inv = VARInvestigator()
    ver = VARVerifier()
    agent = VARAgentLoop(cdp, llm, repo, inv, ver, max_steps=max_steps)
    report = asyncio.run(agent.run(url, goal))
    return report.model_dump()
