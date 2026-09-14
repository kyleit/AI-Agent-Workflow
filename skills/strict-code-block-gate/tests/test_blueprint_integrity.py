import importlib.util
from pathlib import Path


_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_strict_code_block_gate.py"
_SPEC = importlib.util.spec_from_file_location("run_strict_code_block_gate_integrity", _SCRIPT)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
validate_blueprint_location = _MODULE.validate_blueprint_location


def _discover_module():
    script = Path(__file__).resolve().parents[1] / "scripts" / "discover_code_blocks.py"
    spec = importlib.util.spec_from_file_location("discover_code_blocks_integrity", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_blueprint_must_use_canonical_feature_blueprints_folder(tmp_path: Path) -> None:
    assert validate_blueprint_location(
        tmp_path, tmp_path / "docs" / "features" / "monitor" / "blueprints" / "master.md"
    ) == []
    assert validate_blueprint_location(tmp_path, tmp_path / "docs" / "features" / "monitor" / "blueprint.md")


def test_binary_asset_must_be_a_verified_manifest(tmp_path: Path) -> None:
    discover = _discover_module()
    blueprint = tmp_path / "blueprint.md"
    blueprint.write_text(
        """id: FONT
language: text
file: frontend/src/assets/fonts/Inter-Regular.woff2
operation: create
implementation_ready: true
full_file: true
block_scope: full-file
```text
font binary stub
```
""",
        encoding="utf-8",
    )
    block = discover.discover(blueprint)["blocks"][0]
    assert block["status"] == "BLOCKED"
    assert "binary_asset_requires_asset_manifest_language" in block["findings"]
    assert "binary_asset_must_not_use_full_file" in block["findings"]


def test_generated_lockfile_must_use_generator_contract(tmp_path: Path) -> None:
    discover = _discover_module()
    blueprint = tmp_path / "blueprint.md"
    blueprint.write_text(
        """id: SUM
language: text
file: backend/go.sum
operation: create
implementation_ready: true
full_file: true
block_scope: full-file
```text
github.com/example/module v1.0.0 h1=guessed
```
""",
        encoding="utf-8",
    )
    block = discover.discover(blueprint)["blocks"][0]
    assert block["status"] == "BLOCKED"
    assert "generated_lockfile_requires_generated_manifest_language" in block["findings"]
    assert "generated_lockfile_requires_generate_operation" in block["findings"]
    assert "generated_lockfile_missing_generator_command" in block["findings"]
