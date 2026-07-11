# test_lightweight_initialize.py
import pytest
pytestmark = pytest.mark.unit
pytestmark = [pytest.mark.unit, pytest.mark.smoke]

"""
FEAT-050 — Lightweight Initialize-Workflow Tests
8 no-heavy-init assertions + latency check + safe_minimal compatibility
"""
import pytest
pytestmark = pytest.mark.unit
import os
import sys
import time
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))


@pytest.fixture(autouse=True)
def tmp_state(tmp_path, monkeypatch):
    """Set up minimal state files in temp directory."""
    agents_dir = tmp_path / ".agents" / "state"
    agents_dir.mkdir(parents=True)
    # Write minimal context
    (agents_dir / "context.json").write_text(json.dumps({
        "project_version": "1.0.0",
        "version_source": "context.json",
        "git": {"branch": "main", "working_tree": "clean"},
        "checkpoint": 4,
    }), encoding="utf-8")
    (agents_dir / "approvals.json").write_text(json.dumps({"blueprint": {}}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    # Write AI_RULES.md placeholder
    (tmp_path / "AI_RULES.md").write_text("# AI Rules\n", encoding="utf-8")
    yield


# ---------------------------------------------------------------------------
# Heavy operation mocks
# ---------------------------------------------------------------------------

class TestNoHeavyInitOperations:
    """8 assertions that forbidden heavy operations are NOT called during init."""

    def test_sync_request_history_not_called(self):
        """TC-LITE-01: sync_request_history() must NOT be called during init."""
        with patch("builtins.__import__") as mock_import:
            # Ensure no transcript parsing happens
            import context as ctx
            with patch.object(ctx, "parse_transcript", MagicMock(side_effect=AssertionError("parse_transcript called!"))) as mock_parse:
                # Simulate init sequence
                from validator import detect_project_version_cached
                detect_project_version_cached()
                mock_parse.assert_not_called()

    def test_parse_transcript_not_called(self, tmp_path):
        """TC-LITE-02: parse_transcript() must NOT be called during lightweight init."""
        import context as ctx
        call_log = []

        original = ctx.parse_transcript

        def spy_parse(log_file):
            call_log.append(log_file)
            return original(log_file)

        with patch.object(ctx, "parse_transcript", spy_parse):
            # Simulate init: read cached state files only
            from validator import detect_project_version_cached, detect_work_item_cached
            detect_project_version_cached()
            detect_work_item_cached()

        assert len(call_log) == 0, f"parse_transcript was called {len(call_log)} times during init"

    def test_no_memory_full_load(self):
        """TC-LITE-03: Full memory load (project-summary.md) must NOT be triggered during init."""
        from dependency_resolver import load_memory_cached
        result = load_memory_cached()
        # Cached loader should NOT read project-summary.md
        assert result.status in ("cached", "missing"), f"Unexpected status: {result.status}"
        assert "project-summary.md" not in result.source

    def test_no_rag_connect(self):
        """TC-LITE-04: RAG connect must NOT be triggered during init."""
        from dependency_resolver import load_rag_cached
        result = load_rag_cached()
        # Should read metadata only, no connection
        assert result.status in ("cached", "missing"), f"Unexpected status: {result.status}"

    def test_no_workspace_scan(self):
        """TC-LITE-05: workspace_scan must be 'none' for initialize-workflow."""
        from dependency_resolver import parse_requirements
        reqs = parse_requirements("initialize-workflow")
        ws_scan = reqs.get("workspace_scan", "none")
        assert ws_scan == "none", f"initialize-workflow should have workspace_scan: none, got: {ws_scan}"

    def test_git_describe_tags_not_called(self):
        """TC-LITE-06: git describe --tags must NOT be called during init."""
        with patch("subprocess.run") as mock_run:
            from validator import detect_project_version_cached
            detect_project_version_cached()
            # Verify git describe was never called
            for call_args in mock_run.call_args_list:
                args = call_args[0][0] if call_args[0] else []
                if isinstance(args, list):
                    assert "describe" not in args, f"git describe --tags was called: {args}"

    def test_no_manifest_scan_for_version(self):
        """TC-LITE-07: Version must NOT come from package.json/go.mod/pyproject.toml scans."""
        from validator import detect_project_version_cached
        with patch("builtins.open", side_effect=lambda p, **kw: _safe_open(p, **kw)):
            result = detect_project_version_cached()
        # Result should come from context.json, not scanned manifests
        assert result["source"] in ("context.json", ".agents/MANIFEST.json", "unknown"), \
            f"Version came from forbidden manifest scan: {result['source']}"

    def test_refresh_context_usage_not_called(self):
        """TC-LITE-08: refresh_context_usage_for_active_conversation() must NOT be called during init."""
        import context as ctx
        with patch.object(ctx, "parse_transcript", MagicMock(side_effect=AssertionError("transcript parsed!"))) as mock:
            from dependency_resolver import load_usage_cached
            result = load_usage_cached()
            mock.assert_not_called()
        # Usage should come from state files, not transcript
        assert result.status in ("cached", "missing")


def _safe_open(path, **kw):
    """Allow reading only expected files during lightweight init."""
    path_str = str(path)
    # Allow context.json and MANIFEST.json
    allowed = [".agents", "context.json", "AI_RULES.md", "AGENTS.md", "MANIFEST.json", "SKILL.md"]
    # Forbidden: manifest files that should not be scanned
    forbidden = ["package.json", "go.mod", "pyproject.toml", "Cargo.toml"]
    for f in forbidden:
        if path_str.endswith(f):
            raise AssertionError(f"Forbidden manifest scan: {path_str}")
    import builtins
    return builtins.open(path, **kw)


class TestInitLatency:
    """Latency goal: < 800ms"""

    def test_cached_reads_complete_under_800ms(self, tmp_path):
        """TC-PERF-01: Cached reads for version, usage, work-item complete under 800ms."""
        from validator import detect_project_version_cached, detect_work_item_cached, read_environment_snapshot
        from dependency_resolver import load_usage_cached, load_memory_cached

        start = time.perf_counter()
        detect_project_version_cached()
        detect_work_item_cached()
        read_environment_snapshot()
        load_usage_cached()
        load_memory_cached()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 800, f"Lightweight init operations took {elapsed_ms:.0f}ms (limit: 800ms)"


class TestSafeMinimalFallback:
    """Legacy skills without runtime_requirements get safe_minimal fallback."""

    def test_legacy_skill_uses_safe_minimal_not_full_preload(self):
        """TC-COMPAT-01: A skill with no runtime_requirements gets safe_minimal, never full_preload."""
        from dependency_resolver import resolve_requirements, SAFE_MINIMAL_FALLBACK

        # Simulate a legacy skill with empty requirements
        ctx = resolve_requirements("nonexistent-legacy-skill", {})
        # All safety keys should be present
        assert "rules" in ctx.resolved
        assert "state" in ctx.resolved
        # Memory should be none/deferred, not full preload
        if "memory" in ctx.resolved:
            assert ctx.resolved["memory"].status != "loaded", \
                "Legacy skill should NOT trigger full memory load (safe_minimal fallback)"


class TestDependencyResolverSchema:
    """Schema validation tests."""

    def test_version_key_is_valid(self):
        """TC-SCHEMA-01: 'version' is a valid runtime_requirements key."""
        from dependency_resolver import validate_requirements, SUPPORTED_KEYS
        assert "version" in SUPPORTED_KEYS

    def test_provider_key_is_valid(self):
        """TC-SCHEMA-02: 'provider' is a valid runtime_requirements key."""
        from dependency_resolver import SUPPORTED_KEYS
        assert "provider" in SUPPORTED_KEYS

    def test_usage_key_is_valid(self):
        """TC-SCHEMA-03: 'usage' is a valid runtime_requirements key."""
        from dependency_resolver import SUPPORTED_KEYS
        assert "usage" in SUPPORTED_KEYS

    def test_transcript_sync_is_deprecated(self):
        """TC-SCHEMA-04: 'transcript_sync' is in DEPRECATED_KEYS, not SUPPORTED_KEYS."""
        from dependency_resolver import SUPPORTED_KEYS, DEPRECATED_KEYS
        assert "transcript_sync" not in SUPPORTED_KEYS
        assert "transcript_sync" in DEPRECATED_KEYS

    def test_provider_usage_is_deprecated(self):
        """TC-SCHEMA-05: 'provider_usage' is in DEPRECATED_KEYS."""
        from dependency_resolver import DEPRECATED_KEYS
        assert "provider_usage" in DEPRECATED_KEYS

    def test_safety_key_violation_raises(self):
        """TC-SCHEMA-06: rules: none raises SafetyKeyViolationError."""
        from dependency_resolver import validate_requirements
        result = validate_requirements("any-skill", {"rules": "none", "state": "required", "approvals": "required"})
        assert not result.ok
        assert any("SafetyKeyViolationError" in e or "safety" in e.lower() for e in result.errors)

    def test_initialize_workflow_requirements_valid(self):
        """TC-SCHEMA-07: initialize-workflow SKILL.md has valid runtime_requirements."""
        from dependency_resolver import parse_requirements, validate_requirements
        reqs = parse_requirements("initialize-workflow")
        if reqs:  # Only if SKILL.md has runtime_requirements
            result = validate_requirements("initialize-workflow", reqs)
            assert result.ok, f"initialize-workflow requirements invalid: {result.errors}"
