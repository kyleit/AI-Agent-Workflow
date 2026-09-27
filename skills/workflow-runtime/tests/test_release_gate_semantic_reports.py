from pathlib import Path

from workflow_runtime.application.verification.release_gate import ReleaseGate


def test_release_gate_finds_semantic_slugged_reports(tmp_path: Path) -> None:
    debug = tmp_path / "docs/features/session-bus/debug/FEAT-616_persistent_client_debug.md"
    verify = tmp_path / "docs/features/session-bus/verification/FEAT-616_persistent_client_verify.md"
    debug.parent.mkdir(parents=True)
    verify.parent.mkdir(parents=True)
    debug.write_text("---\nstatus: PASS\n---\n", encoding="utf-8")
    verify.write_text("---\nstatus: PASS\n---\n", encoding="utf-8")

    gate = ReleaseGate(str(tmp_path))

    assert Path(gate._find_report("FEAT-616", "debug")) == debug
    assert Path(gate._find_report("FEAT-616", "verification")) == verify
