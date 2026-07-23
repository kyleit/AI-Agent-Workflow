import io
import os
import uuid
from typing import Optional, Tuple
from PIL import Image
import numpy as np

from vir_runtime.varbc.domain.observation import VisualObservation
from vir_runtime.varbc.domain.baseline import UIBaseline
from vir_runtime.varbc.domain.diff import VisualDiff
from vir_runtime.varbc.domain.report import VARReport, VARStatus
from vir_runtime.varbc.domain.errors import BrowserNotAvailableError
from vir_runtime.varbc.application.ports import (
    CDPClientPort,
    BaselineRepositoryPort,
    ReportRepositoryPort,
)


class VARService:
    """Core application service orchestrating baseline, observation, and diff comparison logic."""

    def __init__(
        self,
        cdp_client: Optional[CDPClientPort],
        baseline_repo: BaselineRepositoryPort,
        report_repo: ReportRepositoryPort,
    ) -> None:
        """Constructs VARService with dependency-injected ports."""
        self._cdp_client = cdp_client
        self._baseline_repo = baseline_repo
        self._report_repo = report_repo

    async def capture_screenshot(
        self, url: str, selector: str = "body"
    ) -> Tuple[VisualObservation, bytes]:
        """Captures screenshot and DOM snapshot from Chrome DevTools Protocol.

        1. Check if self._cdp_client is present. If None, raise BrowserNotAvailableError.
        2. Call self._cdp_client.navigate(url)
        3. Call image_bytes = await self._cdp_client.capture_screenshot(selector)
        4. Call dom_snapshot = await self._cdp_client.get_dom_snapshot()
        5. Call console_errors = await self._cdp_client.get_console_errors()
        6. Construct VisualObservation instance with unique ID.
        7. Return (observation, image_bytes).
        """
        if self._cdp_client is None:
            raise BrowserNotAvailableError("CDP client unavailable")

        await self._cdp_client.navigate(url)
        image_bytes = await self._cdp_client.capture_screenshot(selector)
        dom_snapshot = await self._cdp_client.get_dom_snapshot()
        console_errors = await self._cdp_client.get_console_errors()

        obs_id = f"obs-{uuid.uuid4().hex[:8]}"
        observation = VisualObservation(
            id=obs_id,
            url=url,
            dom_snapshot=dom_snapshot,
            console_errors=console_errors,
        )
        return observation, image_bytes

    async def compare_baseline(
        self, observation: VisualObservation, component_id: str, current_image: bytes
    ) -> VisualDiff:
        """Compares a captured observation image against gold-standard UIBaseline.

        1. Fetch baseline from self._baseline_repo.get_baseline(component_id).
        2. Read baseline PNG bytes from self._baseline_repo.get_baseline_image(component_id).
        3. Compute pixel difference score using Pillow/NumPy matrix comparison.
        4. Generate diff heatmap image PNG bytes if diff_score > 0.0.
        5. Save diff heatmap using report asset store.
        6. Return VisualDiff domain object.
        """
        baseline = await self._baseline_repo.get_baseline(component_id)
        baseline_bytes = await self._baseline_repo.get_baseline_image(component_id)

        if not baseline or not baseline_bytes:
            return VisualDiff(
                baseline_id=component_id,
                observation_id=observation.id,
                diff_score=1.0,
                issues=[f"Baseline image not found for component '{component_id}'"],
            )

        # Pillow / NumPy image comparison
        img_baseline = Image.open(io.BytesIO(baseline_bytes)).convert("RGB")
        img_current = Image.open(io.BytesIO(current_image)).convert("RGB")

        # Resize current image to baseline size if dimensions differ
        if img_baseline.size != img_current.size:
            img_current = img_current.resize(img_baseline.size)

        arr_base = np.array(img_baseline, dtype=np.float32)
        arr_curr = np.array(img_current, dtype=np.float32)

        diff_arr = np.abs(arr_base - arr_curr)
        max_possible_diff = 255.0 * arr_base.size
        diff_score = (
            float(np.sum(diff_arr) / max_possible_diff)
            if max_possible_diff > 0
            else 0.0
        )
        diff_score = round(diff_score, 4)

        issues = []
        diff_image_path = ""

        if diff_score > 0.0:
            issues.append(
                f"Visual discrepancy detected with diff score {diff_score}"
            )
            diff_mask = np.uint8(np.clip(diff_arr * 2, 0, 255))
            diff_img = Image.fromarray(diff_mask, mode="RGB")

            assets_dir = "docs/reports/assets"
            os.makedirs(assets_dir, exist_ok=True)
            diff_filename = f"diff_{observation.id}_{component_id}.png"
            diff_image_path = os.path.join(assets_dir, diff_filename)
            diff_img.save(diff_image_path, format="PNG")

        return VisualDiff(
            baseline_id=component_id,
            observation_id=observation.id,
            diff_score=diff_score,
            diff_image_path=diff_image_path,
            issues=issues,
        )

    async def generate_report(
        self,
        observations: list[VisualObservation],
        diffs: list[VisualDiff],
        threshold: float = 0.05,
    ) -> VARReport:
        """Aggregates observations and visual diffs into a VARReport and persists it.

        1. Create VARReport instance with unique report ID.
        2. Call report.compute_status(threshold).
        3. Save report to disk via self._report_repo.save_report(report).
        4. Return saved VARReport.
        """
        report_id = uuid.uuid4().hex[:8]
        raw_report = VARReport(
            id=report_id,
            observations=observations,
            diffs=diffs,
        )
        report = raw_report.compute_status(threshold=threshold)
        await self._report_repo.save_report(report)
        return report
