import io
import pytest
from datetime import datetime
from PIL import Image
from pydantic import ValidationError

from vir_runtime.varbc.domain import (
    VisualObservation,
    UIBaseline,
    VisualDiff,
    VARStatus,
    VARReport,
    ActionType,
    AgentAction,
    ActionPlan,
    AnomalySeverity,
    Anomaly,
    AnomalyRule,
    HypothesisStatus,
    Hypothesis,
    Investigation,
    BrowserNotAvailableError,
)
from vir_runtime.varbc.application.ports import (
    CDPClientPort,
    BaselineRepositoryPort,
    ReportRepositoryPort,
    MemoryManagerPort,
    LLMProviderPort,
)
from vir_runtime.varbc.application.service import VARService
from vir_runtime.varbc.infrastructure import FileBaselineRepo, FileReportRepo


# --- Test FR-01: 10 Domain Entities Immutability & Validation ---

def test_visual_observation_immutability():
    obs = VisualObservation(id="obs-1", url="http://example.com")
    assert obs.id == "obs-1"
    assert obs.url == "http://example.com"
    with pytest.raises(ValidationError):
        obs.url = "http://changed.com"  # Frozen check


def test_ui_baseline_immutability():
    base = UIBaseline(component_id="comp-1", baseline_image_path="path/to/img.png")
    assert base.component_id == "comp-1"
    with pytest.raises(ValidationError):
        base.component_id = "comp-2"


def test_visual_diff_immutability():
    diff = VisualDiff(baseline_id="base-1", observation_id="obs-1", diff_score=0.02)
    assert diff.diff_score == 0.02
    with pytest.raises(ValidationError):
        diff.diff_score = 0.5


def test_var_report_compute_status():
    report = VARReport(id="rep-1")
    assert report.status == VARStatus.NOT_AVAILABLE
    assert not report.passed

    # Pass case
    diff1 = VisualDiff(baseline_id="b1", observation_id="o1", diff_score=0.01)
    rep_pass = VARReport(id="rep-2", diffs=[diff1]).compute_status(threshold=0.05)
    assert rep_pass.status == VARStatus.PASS
    assert rep_pass.passed
    assert rep_pass.score == 99.0

    # Fail case
    diff2 = VisualDiff(baseline_id="b2", observation_id="o2", diff_score=0.10)
    rep_fail = VARReport(id="rep-3", diffs=[diff2]).compute_status(threshold=0.05)
    assert rep_fail.status == VARStatus.FAIL
    assert not rep_fail.passed
    assert rep_fail.score == 90.0


def test_action_entities():
    act = AgentAction(type=ActionType.CLICK, target="#button")
    plan = ActionPlan(actions=[act], rationale="Click button test", confidence=0.95)
    assert plan.actions[0].type == ActionType.CLICK
    with pytest.raises(ValidationError):
        plan.confidence = 1.0


def test_anomaly_entities():
    rule = AnomalyRule(rule_id="r-1", name="Layout Overlap", pattern=".header", threshold=0.2)
    anomaly = Anomaly(id="anom-1", description="Header clipping", severity=rule.severity)
    assert anomaly.severity == AnomalySeverity.MEDIUM
    with pytest.raises(ValidationError):
        anomaly.id = "anom-2"


def test_investigation_entities():
    hyp = Hypothesis(statement="CSS selector broken", status=HypothesisStatus.PENDING)
    inv = Investigation(id="inv-1", hypotheses=[hyp], completed=False)
    assert inv.hypotheses[0].statement == "CSS selector broken"
    with pytest.raises(ValidationError):
        inv.completed = True


# --- Test FR-02: ABC Ports Cannot Be Instantiated Directly ---

def test_abc_ports_cannot_be_instantiated():
    with pytest.raises(TypeError):
        CDPClientPort()
    with pytest.raises(TypeError):
        BaselineRepositoryPort()
    with pytest.raises(TypeError):
        ReportRepositoryPort()
    with pytest.raises(TypeError):
        MemoryManagerPort()
    with pytest.raises(TypeError):
        LLMProviderPort()


# --- Test FR-02: VARService Logic with Mocks ---

class MockCDPClient(CDPClientPort):
    def __init__(self):
        self.navigated_url = None

    async def navigate(self, url: str) -> None:
        self.navigated_url = url

    async def capture_screenshot(self, selector: str = "body") -> bytes:
        img = Image.new("RGB", (100, 100), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    async def get_dom_snapshot(self) -> str:
        return "<html><body>Mock</body></html>"

    async def get_console_errors(self) -> list[str]:
        return ["Mock error"]

    async def execute_action(self, action) -> None:
        pass

    async def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_var_service_capture_screenshot():
    cdp = MockCDPClient()
    repo_base = FileBaselineRepo(baselines_dir="/tmp/test_baselines_dir")
    repo_rep = FileReportRepo(reports_dir="/tmp/test_reports_dir", assets_dir="/tmp/test_assets_dir")

    service = VARService(cdp_client=cdp, baseline_repo=repo_base, report_repo=repo_rep)
    obs, img_bytes = await service.capture_screenshot("http://localhost:8000")

    assert cdp.navigated_url == "http://localhost:8000"
    assert obs.url == "http://localhost:8000"
    assert obs.dom_snapshot == "<html><body>Mock</body></html>"
    assert obs.console_errors == ["Mock error"]
    assert len(img_bytes) > 0


@pytest.mark.asyncio
async def test_var_service_browser_unavailable():
    repo_base = FileBaselineRepo(baselines_dir="/tmp/test_baselines_dir")
    repo_rep = FileReportRepo(reports_dir="/tmp/test_reports_dir", assets_dir="/tmp/test_assets_dir")

    service = VARService(cdp_client=None, baseline_repo=repo_base, report_repo=repo_rep)
    with pytest.raises(BrowserNotAvailableError):
        await service.capture_screenshot("http://localhost:8000")


@pytest.mark.asyncio
async def test_var_service_compare_baseline(tmp_path):
    base_dir = str(tmp_path / "baselines")
    rep_dir = str(tmp_path / "reports")
    asset_dir = str(tmp_path / "assets")

    repo_base = FileBaselineRepo(baselines_dir=base_dir)
    repo_rep = FileReportRepo(reports_dir=rep_dir, assets_dir=asset_dir)
    service = VARService(cdp_client=None, baseline_repo=repo_base, report_repo=repo_rep)

    # Create baseline image
    img = Image.new("RGB", (100, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    base_bytes = buf.getvalue()

    baseline = UIBaseline(component_id="comp-test", baseline_image_path=f"{base_dir}/comp-test.png")
    await repo_base.save_baseline(baseline, base_bytes)

    # Observation with identical image
    obs = VisualObservation(id="obs-test", url="http://example.com")
    diff = await service.compare_baseline(obs, "comp-test", base_bytes)

    assert diff.baseline_id == "comp-test"
    assert diff.observation_id == "obs-test"
    assert diff.diff_score == 0.0


# --- Test FR-06: File Repositories File Read/Write Operations ---

@pytest.mark.asyncio
async def test_file_baseline_repo_crud(tmp_path):
    repo_dir = str(tmp_path / "baselines")
    repo = FileBaselineRepo(baselines_dir=repo_dir)

    baseline = UIBaseline(component_id="btn-primary", baseline_image_path=f"{repo_dir}/btn-primary.png")
    image_bytes = b"fake_png_data"

    await repo.save_baseline(baseline, image_bytes)

    retrieved = await repo.get_baseline("btn-primary")
    assert retrieved is not None
    assert retrieved.component_id == "btn-primary"

    retrieved_bytes = await repo.get_baseline_image("btn-primary")
    assert retrieved_bytes == image_bytes

    non_existent = await repo.get_baseline("non-existent")
    assert non_existent is None


@pytest.mark.asyncio
async def test_file_report_repo_crud(tmp_path):
    reports_dir = str(tmp_path / "reports")
    assets_dir = str(tmp_path / "assets")
    repo = FileReportRepo(reports_dir=reports_dir, assets_dir=assets_dir)

    report = VARReport(id="rep-100", status=VARStatus.PASS, passed=True, score=98.5)
    await repo.save_report(report)

    retrieved = await repo.get_report("rep-100")
    assert retrieved is not None
    assert retrieved.id == "rep-100"
    assert retrieved.status == VARStatus.PASS
    assert retrieved.passed is True
    assert retrieved.score == 98.5


# --- Test NFR-01: Domain Layer Isolation ---

def test_domain_layer_isolation():
    import sys
    import vir_runtime.varbc.domain as domain_pkg

    # Check imported modules in domain package
    for module_name in sys.modules:
        if module_name.startswith("vir_runtime.varbc.domain."):
            mod = sys.modules[module_name]
            # Ensure domain modules do not import infrastructure or application
            mod_file = getattr(mod, "__file__", "") or ""
            if "varbc/domain" in mod_file:
                with open(mod_file, "r", encoding="utf-8") as f:
                    code = f.read()
                assert "infrastructure" not in code, f"Domain module {module_name} imports infrastructure layer!"
                assert "application" not in code, f"Domain module {module_name} imports application layer!"
