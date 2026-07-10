# test_deps_fix.py
"""
FEAT-050 — deps fix Tests
4 scenarios:
1. Proposes safe runtime_requirements template for skill missing it
2. Reports all affected SKILL.md files before writing (approval gate)
3. Migrates transcript_sync -> usage
4. Migrates provider_usage -> provider
"""
import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from dependency_resolver import (
    compute_deps_fix_diff, generate_safe_requirements_template,
    parse_requirements, DEPRECATED_KEYS,
)


@pytest.fixture
def skill_without_requirements(tmp_path):
    """Create a SKILL.md without runtime_requirements."""
    skill_dir = tmp_path / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        "---\nname: test-skill\ndescription: Test skill\n---\n\n# Test Skill\n",
        encoding="utf-8"
    )
    return str(skill_dir), str(skill_md)


@pytest.fixture
def skill_with_deprecated_keys(tmp_path):
    """Create a SKILL.md with deprecated transcript_sync and provider_usage keys."""
    skill_dir = tmp_path / "skills" / "legacy-skill"
    skill_dir.mkdir(parents=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        "---\nname: legacy-skill\ndescription: Legacy skill\nruntime_requirements:\n  rules: required\n  state: required\n  transcript_sync: cached\n  provider_usage: optional\n---\n\n# Legacy Skill\n",
        encoding="utf-8"
    )
    return str(skill_dir), str(skill_md)


@pytest.fixture(autouse=True)
def patch_skill_finder(tmp_path, monkeypatch):
    """Redirect skill discovery to tmp_path."""
    import dependency_resolver as dr

    def _find_skill_md_patched(skill_name):
        candidate = os.path.join(str(tmp_path), "skills", skill_name, "SKILL.md")
        if os.path.exists(candidate):
            return candidate
        return None

    monkeypatch.setattr(dr, "_find_skill_md", _find_skill_md_patched)


def test_proposes_safe_template_for_missing_requirements(skill_without_requirements, tmp_path, monkeypatch):
    """TC-FIX-01: deps fix proposes safe runtime_requirements template for skill without one."""
    import dependency_resolver as dr
    monkeypatch.setattr(dr, "_find_skill_md", lambda n: os.path.join(str(tmp_path), "skills", n, "SKILL.md"))

    diff = compute_deps_fix_diff("test-skill")
    assert diff is not None, "Expected diff for skill without runtime_requirements"
    assert diff["template_needed"] is True
    assert "ADD runtime_requirements" in diff["changes"][0]
    assert diff["proposed_template"] is not None
    # Template must include all required safe keys
    template = diff["proposed_template"]
    assert "rules: required" in template
    assert "state: required" in template
    assert "workspace_scan: none" in template


def test_reports_all_affected_files_before_writing(skill_without_requirements, tmp_path, monkeypatch):
    """TC-FIX-02: deps fix must report all affected files before any write (approval gate)."""
    import dependency_resolver as dr
    monkeypatch.setattr(dr, "_find_skill_md", lambda n: os.path.join(str(tmp_path), "skills", n, "SKILL.md"))

    diff = compute_deps_fix_diff("test-skill")
    assert diff is not None

    # Verify the diff contains skill_path (so user sees it before approval)
    assert "skill_path" in diff
    assert diff["skill_path"].endswith("SKILL.md")
    assert "changes" in diff
    assert len(diff["changes"]) > 0


def test_migrates_transcript_sync_to_usage(skill_with_deprecated_keys, tmp_path, monkeypatch):
    """TC-FIX-03: deps fix detects transcript_sync as deprecated and migrates to usage."""
    import dependency_resolver as dr
    monkeypatch.setattr(dr, "_find_skill_md", lambda n: os.path.join(str(tmp_path), "skills", n, "SKILL.md"))

    diff = compute_deps_fix_diff("legacy-skill")
    assert diff is not None, "Expected diff for legacy skill with transcript_sync"
    assert diff["migration_needed"] is True
    changes_str = " ".join(diff["changes"])
    assert "transcript_sync" in changes_str and "usage" in changes_str, \
        f"Expected migration of transcript_sync->usage in: {diff['changes']}"


def test_migrates_provider_usage_to_provider(skill_with_deprecated_keys, tmp_path, monkeypatch):
    """TC-FIX-04: deps fix detects provider_usage as deprecated and migrates to provider."""
    import dependency_resolver as dr
    monkeypatch.setattr(dr, "_find_skill_md", lambda n: os.path.join(str(tmp_path), "skills", n, "SKILL.md"))

    diff = compute_deps_fix_diff("legacy-skill")
    assert diff is not None
    changes_str = " ".join(diff["changes"])
    assert "provider_usage" in changes_str and "provider" in changes_str, \
        f"Expected migration of provider_usage->provider in: {diff['changes']}"


def test_no_diff_when_already_correct(tmp_path, monkeypatch):
    """TC-FIX-05: No diff when skill already has correct runtime_requirements."""
    import dependency_resolver as dr

    skill_dir = tmp_path / "skills" / "good-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: good-skill\nruntime_requirements:\n  rules: required\n  state: required\n  approvals: optional\n  git: cached\n  memory: cached\n  rag: cached\n  workspace_scan: none\n  environment: cached\n  version: cached\n  provider: optional\n  usage: cached\n---\n\n# Good Skill\n",
        encoding="utf-8"
    )
    monkeypatch.setattr(dr, "_find_skill_md", lambda n: str(skill_dir / "SKILL.md"))

    diff = compute_deps_fix_diff("good-skill")
    assert diff is None, "No diff expected for correctly configured skill"


def test_generate_safe_requirements_template():
    """TC-FIX-06: generate_safe_requirements_template returns valid YAML block."""
    template = generate_safe_requirements_template("any-skill")
    assert "runtime_requirements:" in template
    assert "rules: required" in template
    assert "state: required" in template
    assert "workspace_scan: none" in template
    assert "version: cached" in template
    assert "provider: optional" in template
    assert "usage: cached" in template
    # Must NOT contain deprecated keys
    assert "transcript_sync" not in template
    assert "provider_usage" not in template
