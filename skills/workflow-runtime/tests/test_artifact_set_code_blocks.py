from pathlib import Path
import sys


def _modules():
    script_dir = Path(__file__).resolve().parents[3] / "skills" / "strict-code-block-gate" / "scripts"
    sys.path.insert(0, str(script_dir))
    from discover_code_blocks import discover
    from validate_artifact_set_code_blocks import validate_artifact_set

    return discover, validate_artifact_set


def test_file_matrix_requires_a_real_block_for_each_file(tmp_path: Path) -> None:
    discover, validate_artifact_set = _modules()
    blueprint = tmp_path / "phase.md"
    blueprint.write_text(
        """## File-By-File Change Matrix
| File Path | Code Block IDs | Operation |
|---|---|---|
| internal/app.go | B01 | NEW |
| internal/store.go | B02 | NEW |

id: B01
language: go
file: internal/app.go
operation: create
implementation_ready: true
```go
package app
```
""",
        encoding="utf-8",
    )
    findings = validate_artifact_set([blueprint], [discover(blueprint)])
    assert "file_matrix_unknown_code_block:internal/store.go:B02" in findings


def test_file_matrix_rejects_unknown_or_mismatched_blocks(tmp_path: Path) -> None:
    discover, validate_artifact_set = _modules()
    blueprint = tmp_path / "phase.md"
    blueprint.write_text(
        """## File-By-File Change Matrix
| File Path | Code Block IDs | Operation |
|---|---|---|
| internal/app.go | UNKNOWN | NEW |

id: B01
language: go
file: internal/other.go
operation: create
implementation_ready: true
```go
package other
```
""",
        encoding="utf-8",
    )
    findings = validate_artifact_set([blueprint], [discover(blueprint)])
    assert "file_matrix_unknown_code_block:internal/app.go:UNKNOWN" in findings
    assert "code_block_target_missing_from_file_matrix:B01:internal/other.go" in findings


def test_matrix_must_declare_code_block_ids(tmp_path: Path) -> None:
    discover, validate_artifact_set = _modules()
    blueprint = tmp_path / "phase.md"
    blueprint.write_text(
        """## File-By-File Change Matrix
| File Path | Operation |
|---|---|
| internal/app.go | NEW |
""",
        encoding="utf-8",
    )
    findings = validate_artifact_set([blueprint], [discover(blueprint)])
    assert "file_matrix_missing_code_block_ids_column:" + str(blueprint) in findings


def test_large_file_matrix_rejects_representative_source_block(tmp_path: Path) -> None:
    discover, validate_artifact_set = _modules()
    blueprint = tmp_path / "master.md"
    blueprint.write_text(
        """# Master Blueprint
## File-By-File Change Matrix
| File Path | Layer | Operation | Owner | Imports | Exports | Exact Signatures | Projected Lines | Profile | Commands | Code Block IDs | Tests | Evidence |
|---|---|---|---|---|---|---|---:|---|---|---|---|---|
| internal/app.go | Application | NEW | app | context | NewApp | NewApp() (*App, error) | 100 | go | go test ./... | B01 | T01 | evidence/app.log |

id: B01
language: go
file: internal/app.go
operation: create
implementation_ready: true
block_scope: full-file
full_file: true
```go
package app
```
""",
        encoding="utf-8",
    )
    findings = validate_artifact_set([blueprint], [discover(blueprint)])
    assert "code_block_too_thin:B01:1<20:internal/app.go" in findings


def test_large_file_matrix_requires_full_file_metadata(tmp_path: Path) -> None:
    discover, validate_artifact_set = _modules()
    blueprint = tmp_path / "master.md"
    blueprint.write_text(
        """# Master Blueprint
## Feature Coverage Matrix
## File-By-File Change Matrix
| File Path | Layer | Operation | Owner | Imports | Exports | Exact Signatures | Projected Lines | Profile | Commands | Code Block IDs | Tests | Evidence |
|---|---|---|---|---|---|---|---:|---|---|---|---|---|
| internal/app.go | Application | NEW | app | context | NewApp | NewApp() (*App, error) | 1 | go | go test ./... | B01 | T01 | evidence/app.log |

id: B01
language: go
file: internal/app.go
operation: create
implementation_ready: true
```go
package app
```
""",
        encoding="utf-8",
    )
    findings = validate_artifact_set([blueprint], [discover(blueprint)])
    assert "code_block_not_full_file:B01:internal/app.go" in findings
