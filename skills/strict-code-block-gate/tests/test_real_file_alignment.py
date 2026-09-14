import importlib.util
from pathlib import Path


_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_strict_code_block_gate.py"
_SPEC = importlib.util.spec_from_file_location("run_strict_code_block_gate", _SCRIPT)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
validate_real_file_alignment = _MODULE.validate_real_file_alignment
validate_binary_asset_alignment = _MODULE.validate_binary_asset_alignment


def test_existing_workspace_file_must_match_full_file_block(tmp_path: Path) -> None:
    target = tmp_path / "backend" / "app.go"
    target.parent.mkdir()
    target.write_text("package app\n", encoding="utf-8")

    findings = validate_real_file_alignment(
        tmp_path,
        [
            {
                "id": "block-app",
                "implementation_ready": True,
                "full_file": True,
                "file": "backend/app.go",
                "code": "package other\n",
            }
        ],
    )

    assert "code_block_workspace_mismatch:block-app:backend/app.go" in findings


def test_font_asset_must_have_real_woff2_signature(tmp_path: Path) -> None:
    target = tmp_path / "frontend" / "src" / "assets" / "fonts" / "Inter.woff2"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"/* woff2 font binary placeholder */\n")

    findings = validate_binary_asset_alignment(
        tmp_path,
        [
            {
                "id": "font-block",
                "implementation_ready": True,
                "file": "frontend/src/assets/fonts/Inter.woff2",
            }
        ],
    )

    assert "binary_font_invalid_signature:font-block:frontend/src/assets/fonts/Inter.woff2" in findings
    assert "binary_asset_workspace_placeholder:font-block:frontend/src/assets/fonts/Inter.woff2" in findings


def test_real_woff2_asset_is_accepted(tmp_path: Path) -> None:
    target = tmp_path / "frontend" / "src" / "assets" / "fonts" / "Inter.woff2"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"wOF2" + b"\x00" * 32)

    findings = validate_binary_asset_alignment(
        tmp_path,
        [
            {
                "id": "font-block",
                "implementation_ready": True,
                "file": "frontend/src/assets/fonts/Inter.woff2",
            }
        ],
    )

    assert findings == []
