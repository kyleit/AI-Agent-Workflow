import importlib.util
import sys
from pathlib import Path


def _module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "validate_artifact_set_code_blocks.py"
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("artifact_set_code_blocks", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_projected_lines_cannot_be_lowered_below_observable_integration_floor() -> None:
    code = '\n'.join([
        'package api',
        'import "github.com/gofiber/fiber/v2"',
        'func RegisterRoutes(app *fiber.App) {',
        ' app.Get("/healthz", health)',
        ' app.Post("/hosts", create)',
        ' app.Put("/hosts/:id", update)',
        ' app.Delete("/hosts/:id", delete)',
        '}',
    ])

    assert _module()._intrinsic_line_floor("internal/api/routes.go", code) == 40


def test_generated_lockfile_is_not_required_to_be_a_hand_authored_full_file() -> None:
    assert _module()._intrinsic_line_floor("frontend/package-lock.json", "{}\n") == 0


def test_multi_route_matrix_cannot_map_feature_routes_to_only_app_shell() -> None:
    module = _module()
    root = Path(__file__).resolve().parent / "_tmp_screen_route_matrix.md"
    root.write_text(
        """# Screen And Route Coverage Matrix

| Route | Screen | Concrete Files | Code Blocks |
| --- | --- | --- | --- |
| `#/` | Dashboard | `frontend/src/routes/Dashboard.svelte` | CB-DASH |
| `#/hosts` | Hosts | `frontend/src/App.svelte` | CB-HOSTS |
| `#/settings` | Settings | `frontend/src/App.svelte` | CB-SETTINGS |
""",
        encoding="utf-8",
    )
    try:
        findings = module._screen_route_findings(
            [root],
            {
                "CB-DASH": {"file": "frontend/src/routes/Dashboard.svelte"},
                "CB-HOSTS": {"file": "frontend/src/App.svelte"},
                "CB-SETTINGS": {"file": "frontend/src/App.svelte"},
            },
        )
    finally:
        root.unlink(missing_ok=True)
    assert "screen_route_shared_app_shell_for_feature_route:#/hosts:frontend/src/App.svelte" in findings
    assert "screen_route_shared_app_shell_for_feature_route:#/settings:frontend/src/App.svelte" in findings


def test_greenfield_requires_explicit_completeness_matrices() -> None:
    module = _module()
    root = Path(__file__).resolve().parent / "_tmp_greenfield_matrix.md"
    root.write_text(
        """---\nproject_initialization: true\n---\n# Master Blueprint\n\nSvelte frontend, Go Fiber backend, SQLite persistence.\n""",
        encoding="utf-8",
    )
    try:
        findings = module.validate_greenfield_completeness_matrices([root])
    finally:
        root.unlink(missing_ok=True)
    assert "greenfield_required_matrix_missing:Greenfield Completeness Matrix" in findings
    assert "greenfield_required_matrix_missing:Mobile-First Visual Coverage Matrix" in findings
