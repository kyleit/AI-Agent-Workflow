import importlib.util
from pathlib import Path


_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_strict_code_block_gate.py"
_SPEC = importlib.util.spec_from_file_location("run_strict_code_block_gate", _SCRIPT)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def test_phase_discovery_accepts_phase_id_filenames(tmp_path: Path) -> None:
    root = tmp_path / "blueprints"
    (root / "backend").mkdir(parents=True)
    master = root / "FEAT-001_master_blueprint.md"
    phase = root / "backend" / "P01_backend_core.md"
    unrelated = root / "README.md"
    master.write_text("# Master\n", encoding="utf-8")
    phase.write_text("# Phase\n", encoding="utf-8")
    unrelated.write_text("# Index\n", encoding="utf-8")

    discovered = _MODULE.discover_phase_paths(master)

    assert phase.resolve() in discovered
    assert unrelated.resolve() in discovered
