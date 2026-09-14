import importlib.util
from pathlib import Path


_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "aggregate_gate_results.py"
_SPEC = importlib.util.spec_from_file_location("aggregate_gate_results", _SCRIPT)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
aggregate = _MODULE.aggregate


def test_placeholder_code_cannot_pass_discovery(tmp_path: Path) -> None:
    discover_script = Path(__file__).resolve().parents[1] / "scripts" / "discover_code_blocks.py"
    discover_spec = importlib.util.spec_from_file_location("discover_code_blocks", discover_script)
    assert discover_spec and discover_spec.loader
    discover_module = importlib.util.module_from_spec(discover_spec)
    discover_spec.loader.exec_module(discover_module)

    blueprint = tmp_path / "blueprint.md"
    blueprint.write_text(
        """id: block-placeholder
language: go
file: backend/app.go
operation: create
implementation_ready: true
full_file: true
block_scope: full-file
```go
// placeholder
```\n""",
        encoding="utf-8",
    )
    result = discover_module.discover(blueprint)
    assert result["blocks"][0]["status"] == "FAIL"


def test_svelte_placeholder_prop_is_not_treated_as_incomplete_code(tmp_path: Path) -> None:
    discover_script = Path(__file__).resolve().parents[1] / "scripts" / "discover_code_blocks.py"
    discover_spec = importlib.util.spec_from_file_location("discover_code_blocks_svelte", discover_script)
    assert discover_spec and discover_spec.loader
    discover_module = importlib.util.module_from_spec(discover_spec)
    discover_spec.loader.exec_module(discover_module)
    blueprint = tmp_path / "blueprint.md"
    blueprint.write_text(
        """id: block-input
language: svelte
file: frontend/src/Input.svelte
operation: create
implementation_ready: true
full_file: true
block_scope: full-file
```svelte
<script>export let placeholder = \"Enter a value\";</script>
<input {placeholder} />
```
""",
        encoding="utf-8",
    )

    result = discover_module.discover(blueprint)

    assert result["blocks"][0]["status"] == "PASS"


def test_ui_ellipsis_text_is_not_treated_as_placeholder_code(tmp_path: Path) -> None:
    discover_script = Path(__file__).resolve().parents[1] / "scripts" / "discover_code_blocks.py"
    discover_spec = importlib.util.spec_from_file_location("discover_code_blocks_ellipsis", discover_script)
    assert discover_spec and discover_spec.loader
    discover_module = importlib.util.module_from_spec(discover_spec)
    discover_spec.loader.exec_module(discover_module)
    blueprint = tmp_path / "blueprint.md"
    blueprint.write_text(
        """id: block-loading
language: svelte
file: frontend/src/Loading.svelte
operation: create
implementation_ready: true
full_file: true
block_scope: full-file
```svelte
<script>export let message = \"Loading...\";</script>
<span>{message}</span>
```
""",
        encoding="utf-8",
    )

    result = discover_module.discover(blueprint)

    assert result["blocks"][0]["status"] == "PASS"


def test_blocking_findings_cannot_be_aggregated_as_pass() -> None:
    result = aggregate(
        {
            "per_code_block": [{"id": "B01", "status": "PASS"}],
            "profile_results": [{"id": "B01", "status": "PASS"}],
            "materialized_scope": [{"id": "B01", "status": "PASS"}],
            "architecture_results": [{"id": "B01", "status": "PASS"}],
            "blocking_findings": ["file_matrix_row_missing_code_block:src/app.go"],
        }
    )

    assert result["decision"] == "BLOCKED"


def test_aggregate_preserves_blocked_full_file_findings() -> None:
    result = aggregate(
        {
            "per_code_block": [
                {"id": "B01", "status": "BLOCKED", "findings": ["full_file metadata missing"]}
            ],
            "profile_results": [{"id": "B01", "status": "PASS"}],
            "materialized_scope": [{"id": "B01", "status": "PASS"}],
            "architecture_results": [{"id": "B01", "status": "PASS"}],
        }
    )

    assert result["decision"] == "BLOCKED"
    assert "B01: full_file metadata missing" in result["blocking_findings"]
