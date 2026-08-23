from pathlib import Path

from workflow_runtime.application.verification.self_verify_service import SelfVerifyService


def test_self_verify_allows_urls_and_policy_patterns(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "sample-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "repository: https://example.com/org/repo",
                "---",
                "Reject local absolute paths and placeholder strings.",
                "Use relative paths in artifacts.",
            ]
        ),
        encoding="utf-8",
    )
    (skill_dir / "path-sanitization-rules.yaml").write_text(
        'leak_detection_patterns:\n  - "file:///"\n  - "/Users/"\n',
        encoding="utf-8",
    )

    service = SelfVerifyService(workspace_root=str(tmp_path))

    assert service.check_static_violations("skills/sample-skill") == []


def test_self_verify_flags_real_local_absolute_path(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "sample-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "Write output to /Users/example/workspace/report.md\n",
        encoding="utf-8",
    )

    service = SelfVerifyService(workspace_root=str(tmp_path))

    violations = service.check_static_violations("skills/sample-skill")
    assert [violation.rule_id for violation in violations] == ["RULE-ABS-PATH"]


def test_self_verify_ignores_tests_and_cache_dirs(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "sample-skill"
    tests_dir = skill_dir / "tests"
    cache_dir = skill_dir / "__pycache__"
    tests_dir.mkdir(parents=True)
    cache_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("Clean skill body.\n", encoding="utf-8")
    (tests_dir / "test_paths.py").write_text(
        'bad_path = "/Users/example/workspace"\n',
        encoding="utf-8",
    )
    (cache_dir / "artifact.py").write_text(
        'bad_path = "/Users/example/workspace"\n',
        encoding="utf-8",
    )

    service = SelfVerifyService(workspace_root=str(tmp_path))

    assert service.check_static_violations("skills/sample-skill") == []
