import os
import pathlib
import pytest
from vir_runtime.varbc.infrastructure.cdp import AsyncCDPClient
from vir_runtime.varbc.infrastructure.gemini_provider import GeminiVisionProvider
from vir_runtime.varbc.infrastructure.report_repo import FileReportRepo
from vir_runtime.varbc.application.investigator import VARInvestigator
from vir_runtime.varbc.application.verifier import VARVerifier
from vir_runtime.varbc.application.agent import VARAgentLoop
from vir_runtime.varbc.domain.report import VARReport, VARStatus


@pytest.mark.asyncio
async def test_full_varbc_autonomous_loop_e2e(tmp_path: pathlib.Path) -> None:
    """Tests complete end-to-end execution of Python VAR agent loop.

    1. Initialize mock CDP client with dummy HTML and PNG.
    2. Initialize GeminiVisionProvider, FileReportRepo(reports_dir=str(tmp_path)).
    3. Initialize VARInvestigator and VARVerifier.
    4. Construct VARAgentLoop instance with max_steps=3.
    5. Call report = await loop.run(start_url="http://localhost:8080", goal="Verify login form").
    6. Assert isinstance(report, VARReport) is True.
    7. Assert report.status in (VARStatus.PASS, VARStatus.FAIL, VARStatus.NOT_AVAILABLE) is True.
    8. Assert report.generated_at is not None.
    9. Assert report saved on disk under tmp_path / f"VAR_REPORT_{report.id}.json".
    """
    cdp = AsyncCDPClient()
    llm = GeminiVisionProvider()
    repo = FileReportRepo(reports_dir=str(tmp_path))
    inv = VARInvestigator()
    ver = VARVerifier()
    agent = VARAgentLoop(cdp, llm, repo, inv, ver, max_steps=3)

    report = await agent.run("http://localhost:8080", "Verify login form")

    assert isinstance(report, VARReport)
    assert report.status in (VARStatus.PASS, VARStatus.FAIL, VARStatus.NOT_AVAILABLE)
    assert len(report.id) > 0
    assert report.generated_at is not None

    report_json_path = tmp_path / f"VAR_REPORT_{report.id}.json"
    assert os.path.exists(report_json_path)
