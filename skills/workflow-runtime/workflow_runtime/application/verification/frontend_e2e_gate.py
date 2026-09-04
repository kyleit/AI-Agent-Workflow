"""Evidence contract and real-browser runner for frontend completion gates."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

REQUIRED_VIEWPORT_ORDER = ("mobile", "desktop", "tablet")
REQUIRED_WIDTHS = {
    "mobile": (375, 390),
    "desktop": (1440, 1920),
    "tablet": (768, 820),
}
_MOCK_ADAPTERS = {"mock", "fake", "stub", "async_cdp"}
_REQUIRED_SEQUENCE = ("automation", "screenshot", "validate")


@dataclass(frozen=True)
class FrontendGateResult:
    ok: bool
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def blocked(cls, reason: str, **details: Any) -> "FrontendGateResult":
        return cls(False, reason, details)

    @classmethod
    def pass_result(cls, **details: Any) -> "FrontendGateResult":
        return cls(True, "frontend_visual_pass", details)


class CompletionGateBlocked(RuntimeError):
    """Raised when a frontend workflow tries to complete without valid evidence."""

    def __init__(self, code: str, reason: str) -> None:
        super().__init__(f"{code}: {reason}")
        self.code = code
        self.reason = reason


def _screenshot_keys(records: Any) -> set[tuple[str, int]]:
    if not isinstance(records, list):
        return set()
    keys: set[tuple[str, int]] = set()
    for record in records:
        if not isinstance(record, Mapping):
            continue
        family = record.get("family")
        width = record.get("width")
        digest = record.get("sha256")
        if isinstance(family, str) and isinstance(width, int) and isinstance(digest, str) and len(digest) == 64:
            keys.add((family, width))
    return keys


def _assertion_keys(records: Any) -> set[tuple[str, int]]:
    if not isinstance(records, list):
        return set()
    return {
        (record["family"], record["width"])
        for record in records
        if isinstance(record, Mapping)
        and isinstance(record.get("family"), str)
        and isinstance(record.get("width"), int)
        and record.get("passed") is True
    }


def validate_frontend_evidence(manifest: Mapping[str, Any]) -> FrontendGateResult:
    """Validate the machine-readable evidence required for frontend completion."""
    if not bool(manifest.get("browser_evidence")):
        return FrontendGateResult.blocked("frontend_browser_evidence_missing")

    adapter = str(manifest.get("adapter", "")).strip().lower()
    if not adapter or adapter in _MOCK_ADAPTERS:
        return FrontendGateResult.blocked("frontend_mock_evidence_forbidden")
    if tuple(manifest.get("viewport_order", ())) != REQUIRED_VIEWPORT_ORDER:
        return FrontendGateResult.blocked("frontend_viewport_order_invalid")

    viewports = manifest.get("viewports")
    if not isinstance(viewports, Mapping):
        return FrontendGateResult.blocked("frontend_viewports_missing")
    for family, widths in REQUIRED_WIDTHS.items():
        observed = tuple(viewports.get(family, ()))
        if observed != widths:
            return FrontendGateResult.blocked(f"frontend_viewport_missing:{family}")

    iterations = manifest.get("iterations")
    if not isinstance(iterations, list) or not iterations:
        return FrontendGateResult.blocked("frontend_iterations_missing")
    final_iteration = iterations[-1]
    if not isinstance(final_iteration, Mapping):
        return FrontendGateResult.blocked("frontend_final_iteration_invalid")
    sequence = tuple(final_iteration.get("sequence", ()))
    if sequence[: len(_REQUIRED_SEQUENCE)] != _REQUIRED_SEQUENCE:
        return FrontendGateResult.blocked("frontend_automation_sequence_invalid")
    prior_findings = any(
        isinstance(item, Mapping) and bool(item.get("findings")) for item in iterations[:-1]
    )
    if prior_findings and not {"fix", "rerun"}.issubset(sequence):
        return FrontendGateResult.blocked("frontend_rerun_after_fix_missing")
    if prior_findings and final_iteration.get("source_changed_since_previous") is not True:
        return FrontendGateResult.blocked("frontend_source_fix_missing")

    required_keys = {(family, width) for family, widths in REQUIRED_WIDTHS.items() for width in widths}
    observed_keys = _screenshot_keys(final_iteration.get("screenshot_hashes"))
    if not required_keys.issubset(observed_keys):
        return FrontendGateResult.blocked("frontend_screenshot_evidence_incomplete")
    if not required_keys.issubset(_assertion_keys(final_iteration.get("layout_assertions"))):
        return FrontendGateResult.blocked("frontend_layout_evidence_incomplete")
    if not isinstance(final_iteration.get("interactions"), list) or not final_iteration.get("interactions"):
        return FrontendGateResult.blocked("frontend_interaction_evidence_missing")

    for field_name, reason in (
        ("unresolved_findings", "frontend_visual_findings_unresolved"),
        ("failed_assertions", "frontend_visual_assertions_failed"),
        ("console_errors", "frontend_runtime_errors_present"),
        ("network_errors", "frontend_runtime_errors_present"),
    ):
        if manifest.get(field_name):
            return FrontendGateResult.blocked(reason)
    if manifest.get("decision") != "PASS":
        return FrontendGateResult.blocked("frontend_visual_pass_missing")
    return FrontendGateResult.pass_result(viewport_count=len(observed_keys), iterations=len(iterations))


def load_visual_manifest(feature_id: str, workspace_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(workspace_root or os.getcwd()).resolve()
    safe_id = Path(str(feature_id)).name
    if safe_id != str(feature_id) or not safe_id:
        return {}
    path = root / "docs" / "aiwf-runs" / safe_id / "08-visual" / "frontend-e2e.json"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return dict(loaded) if isinstance(loaded, dict) else {}


def load_project_profile(workspace_root: str | Path | None = None) -> dict[str, Any]:
    path = Path(workspace_root or os.getcwd()) / ".agents" / "project-profile.json"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return dict(loaded) if isinstance(loaded, dict) else {}


def _source_revision(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except OSError:
        pass
    return "working-tree"


def _source_fingerprint(root: Path) -> str:
    """Fingerprint the working tree enough to prove a fix changed source state."""
    try:
        diff = subprocess.run(
            [
                "git", "diff", "--no-ext-diff", "--binary", "HEAD", "--", ".",
                ":(exclude)docs/aiwf-runs", ":(exclude).agents",
            ],
            cwd=root,
            capture_output=True,
            check=False,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain=v1"], cwd=root, capture_output=True, check=False
        )
        status_lines = [
            line for line in status.stdout.splitlines()
            if b"docs/aiwf-runs" not in line and b".agents/" not in line
        ]
        payload = diff.stdout + b"\n" + b"\n".join(status_lines)
        if payload:
            return hashlib.sha256(payload).hexdigest()
    except OSError:
        pass
    return "working-tree"


async def _run_browser(url: str, screenshot_dir: Path, iteration_number: int) -> dict[str, Any]:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"browser_evidence": False, "adapter": "unavailable", "error": "playwright_not_installed"}

    screenshot_dir.mkdir(parents=True, exist_ok=True)
    console_errors: list[str] = []
    network_errors: list[str] = []
    screenshot_hashes: list[dict[str, Any]] = []
    layout_assertions: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    endpoint = os.getenv("AIWF_BROWSER_CDP_ENDPOINT")
    try:
        async with async_playwright() as playwright:
            browser = (
                await playwright.chromium.connect_over_cdp(endpoint)
                if endpoint
                else await playwright.chromium.launch(headless=True)
            )
            context = await browser.new_context(viewport={"width": 375, "height": 900})
            page = await context.new_page()
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: console_errors.append(str(error)))
            page.on("requestfailed", lambda request: network_errors.append(str(request.url)))
            for family in REQUIRED_VIEWPORT_ORDER:
                for width in REQUIRED_WIDTHS[family]:
                    await page.set_viewport_size({"width": width, "height": 900})
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await page.keyboard.press("Tab")
                    layout = await page.evaluate(
                        """() => {
                          const body = document.body;
                          const controls = [...document.querySelectorAll(
                            'button,a,input,select,textarea,[role="button"]'
                          )].filter((node) => {
                            const rect = node.getBoundingClientRect();
                            return rect.width > 0 && rect.height > 0;
                          });
                          return {
                            horizontalOverflow: body ? body.scrollWidth > body.clientWidth + 1 : false,
                            smallControls: controls.filter((node) => {
                              const rect = node.getBoundingClientRect();
                              return rect.width < 44 || rect.height < 44;
                            }).length,
                          };
                        }"""
                    )
                    if layout.get("horizontalOverflow"):
                        findings.append({"family": family, "width": width, "kind": "horizontal_overflow"})
                    if layout.get("smallControls"):
                        findings.append({"family": family, "width": width, "kind": "touch_target"})
                    layout_assertions.append(
                        {
                            "family": family,
                            "width": width,
                            "horizontal_overflow": bool(layout.get("horizontalOverflow")),
                            "small_controls": int(layout.get("smallControls", 0)),
                            "passed": not layout.get("horizontalOverflow") and not layout.get("smallControls"),
                        }
                    )
                    path = screenshot_dir / f"{family}-{width}-iteration-{iteration_number}.png"
                    data = await page.screenshot(path=str(path), full_page=True)
                    screenshot_hashes.append(
                        {"family": family, "width": width, "path": str(path), "sha256": hashlib.sha256(data).hexdigest()}
                    )
            await context.close()
            await browser.close()
    except Exception as exc:  # Browser startup/navigation failures are evidence failures, never PASS.
        return {
            "browser_evidence": False,
            "adapter": "playwright",
            "error": f"{type(exc).__name__}: {exc}",
            "console_errors": console_errors,
            "network_errors": network_errors,
        }
    return {
        "browser_evidence": True,
        "adapter": "playwright",
        "screenshot_hashes": screenshot_hashes,
        "layout_assertions": layout_assertions,
        "interactions": [{"action": "navigate"}, {"action": "keyboard", "key": "Tab"}],
        "findings": findings,
        "console_errors": console_errors,
        "network_errors": network_errors,
    }


def _run_async(coroutine: Any) -> Any:
    """Run browser work from both synchronous CLIs and IDE event-loop hosts."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)
    result: list[Any] = []
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            result.append(asyncio.run(coroutine))
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=worker, name="aiwf-frontend-e2e", daemon=True)
    thread.start()
    thread.join()
    if errors:
        raise errors[0]
    return result[0] if result else {}


def run_frontend_e2e(
    url: str,
    feature_id: str,
    route: str = "/",
    workspace_root: str | Path | None = None,
    max_iterations: int = 8,
) -> dict[str, Any]:
    """Run one real-browser pass and append it to the feature evidence manifest."""
    root = Path(workspace_root or os.getcwd()).resolve()
    previous = load_visual_manifest(feature_id, root)
    iterations = list(previous.get("iterations", [])) if isinstance(previous.get("iterations"), list) else []
    if len(iterations) >= max_iterations:
        result = {"status": "BLOCKED", "reason": "frontend_max_iterations_exceeded", "next_action": "review_evidence"}
        return result
    number = len(iterations) + 1
    fingerprint = _source_fingerprint(root)
    browser_result = _run_async(
        _run_browser(url.rstrip("/") + "/" + route.lstrip("/"), root / "docs" / "aiwf-runs" / feature_id / "08-visual" / "screenshots", number)
    )
    prior_findings = any(isinstance(item, Mapping) and bool(item.get("findings")) for item in iterations)
    current_findings = browser_result.get("findings", [])
    sequence = [*(_REQUIRED_SEQUENCE), "fix", "rerun"] if prior_findings else list(_REQUIRED_SEQUENCE)
    iteration = {
        "number": number,
        "sequence": sequence,
        "screenshot_hashes": browser_result.get("screenshot_hashes", []),
        "layout_assertions": browser_result.get("layout_assertions", []),
        "interactions": browser_result.get("interactions", []),
        "findings": current_findings,
        "automation": {"route": route, "url": url},
        "source_fingerprint": fingerprint,
        "source_changed_since_previous": bool(
            not iterations or fingerprint != iterations[-1].get("source_fingerprint")
        ),
    }
    iterations.append(iteration)
    manifest: dict[str, Any] = {
        "feature_id": feature_id,
        "source_revision": _source_revision(root),
        "route": route,
        "server": url,
        "adapter": browser_result.get("adapter", "unavailable"),
        "browser_evidence": bool(browser_result.get("browser_evidence")),
        "viewport_order": list(REQUIRED_VIEWPORT_ORDER),
        "viewports": {family: list(widths) for family, widths in REQUIRED_WIDTHS.items()},
        "iterations": iterations,
        "unresolved_findings": current_findings,
        "failed_assertions": [],
        "console_errors": browser_result.get("console_errors", []),
        "network_errors": browser_result.get("network_errors", []),
        "interactions": iteration["interactions"],
        "decision": "PASS" if browser_result.get("browser_evidence") and not current_findings else "BLOCKED",
    }
    if browser_result.get("error"):
        manifest["unresolved_findings"] = [{"kind": "browser", "message": browser_result["error"]}]
    path = root / "docs" / "aiwf-runs" / feature_id / "08-visual" / "frontend-e2e.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    for record in manifest["iterations"][-1].get("screenshot_hashes", []):
        if isinstance(record, dict) and isinstance(record.get("path"), str):
            try:
                record["path"] = Path(record["path"]).resolve().relative_to(root).as_posix()
            except ValueError:
                record["path"] = Path(record["path"]).name
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    gate = validate_frontend_evidence(manifest)
    return {
        "status": "PASS" if gate.ok else "BLOCKED",
        "reason": gate.reason,
        "next_action": "complete" if gate.ok else "fix_source_and_rerun",
        "manifest": path.relative_to(root).as_posix(),
        "iteration": number,
    }


__all__ = [
    "CompletionGateBlocked",
    "FrontendGateResult",
    "REQUIRED_VIEWPORT_ORDER",
    "REQUIRED_WIDTHS",
    "load_project_profile",
    "load_visual_manifest",
    "run_frontend_e2e",
    "validate_frontend_evidence",
]
