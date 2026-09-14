import importlib.util
from pathlib import Path


def _module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "validate_code_block_semantics.py"
    spec = importlib.util.spec_from_file_location("code_block_semantics", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _block(target: str, code: str) -> list[dict]:
    return [{"blocks": [{"id": "B01", "file": target, "implementation_ready": True, "code": code}]}]


def test_dashboard_cannot_pass_with_timer_only() -> None:
    findings = _module().validate_code_block_semantics(
        _block("frontend/src/views/DashboardView.svelte", "<script>setTimeout(() => loading = false, 400)</script>")
    )
    assert "code_block_semantic_contract_missing:B01:frontend/src/views/DashboardView.svelte:dashboard_data_loading" in findings


def test_monitor_management_requires_crud_operations() -> None:
    findings = _module().validate_code_block_semantics(
        _block("frontend/src/views/MonitorManageView.svelte", "<form on:submit={handleAdd}><Input /></form>")
    )
    assert any(item.endswith(":monitor_crud_update") for item in findings)
    assert any(item.endswith(":monitor_crud_delete") for item in findings)


def test_realistic_backend_probe_contract_passes() -> None:
    code = """
    ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
    defer cancel()
    for attempt := 1; attempt <= maxRetry; attempt++ {
        switch monitor.ProbeType { case HTTP, TCP, PING: }
    }
    """
    assert _module().validate_code_block_semantics(_block("pkg/prober/prober.go", code)) == []


def test_settings_route_must_persist_and_report_failures() -> None:
    findings = _module().validate_code_block_semantics(
        _block(
            "frontend/src/routes/Settings.svelte",
            "<script>async function handleSave() { await customAlert('saved') }</script>",
        )
    )
    assert any(item.endswith(":settings_persistence") for item in findings)
    assert any(item.endswith(":settings_write_request") for item in findings)


def test_tray_must_map_health_to_visible_status_colors() -> None:
    findings = _module().validate_code_block_semantics(
        _block("backend/tray/tray.go", "func BuildTrayMenu() { runtime.Quit(ctx) }")
    )
    assert any(item.endswith(":tray_status_color_mapping") for item in findings)


def test_project_contracts_require_backend_routes_and_domain_fields() -> None:
    discoveries = [
        {"blocks": [
            {"id": "H", "file": "internal/api/handlers.go", "implementation_ready": True,
             "code": "func CreateHost() {} func DeleteService() {}"},
            {"id": "R", "file": "internal/api/server.go", "implementation_ready": True,
             "code": "hosts.Post(\"/\", h.CreateHost); services.Delete(\"/:id\", h.DeleteService)"},
            {"id": "M", "file": "internal/domain/models.go", "implementation_ready": True,
             "code": "type Host struct { Name string } type ServiceStatus string"},
        ]}
    ]
    findings = _module().validate_code_block_semantics(discoveries)
    assert any(item.endswith(":host_update_handler") for item in findings)
    assert any(item.endswith(":settings_write_handler") for item in findings)
    assert any(item.endswith(":service_put_route") for item in findings)
    assert any(item.endswith(":host_mac_address") for item in findings)


def test_go_declarations_cannot_precede_import_block() -> None:
    findings = _module().validate_code_block_semantics(
        _block("internal/prober/scheduler.go", "package prober\nconst timeout = 1\nimport (\"time\")\nvar ticker time.Ticker")
    )
    assert any(item.endswith(":go_imports_before_declarations") for item in findings)
