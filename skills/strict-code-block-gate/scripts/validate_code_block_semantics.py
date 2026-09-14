#!/usr/bin/env python3
"""Validate behavior-bearing implementation blocks, not only their metadata."""

from __future__ import annotations

import re
from pathlib import PurePosixPath


def _has_any(code: str, *patterns: str) -> bool:
    return any(re.search(pattern, code, re.IGNORECASE | re.MULTILINE) for pattern in patterns)


def _missing(block_id: str, target: str, contract: str) -> str:
    return f"code_block_semantic_contract_missing:{block_id}:{target}:{contract}"


def validate_code_block_semantics(discoveries: list[dict]) -> list[str]:
    """Return blocking findings for implementation-ready blocks with hollow behavior.

    The checks are intentionally role-based and framework-neutral. They verify
    that a claimed full-file delivery contains the minimum observable behavior
    implied by its path and symbols. They do not invent architecture or write
    documentation; the Agent must supply the actual implementation contract.
    """
    findings: list[str] = []
    implementation_files: dict[str, str] = {}
    for discovery in discoveries:
        for block in discovery.get("blocks", []):
            if not block.get("implementation_ready"):
                continue
            target = str(block.get("file", "")).replace("\\", "/").lower()
            if target:
                implementation_files[target] = str(block.get("code", ""))

    def require_file(target: str, contract: str, *patterns: str) -> None:
        code = implementation_files.get(target.lower())
        if code is None:
            return
        if not _has_any(code, *patterns):
            findings.append(_missing(f"file:{target}", target, contract))

    all_implementation_code = "\n".join(implementation_files.values())
    for discovery in discoveries:
        for block in discovery.get("blocks", []):
            if not block.get("implementation_ready"):
                continue
            block_id = str(block.get("id", "")).strip()
            target = str(block.get("file", "")).replace("\\", "/")
            code = str(block.get("code", ""))
            path = PurePosixPath(target)
            name = path.name.lower()
            lower = code.lower()

            if path.suffix == ".svelte":
                if "views/" in target.lower() or "routes/" in target.lower():
                    if not _has_any(code, r"\{#if", r"\{#each"):
                        findings.append(_missing(block_id, target, "view_render_state"))
                    if name.startswith("dashboard"):
                        if not _has_any(code, r"fetch\(", r"\.subscribe\(", r"eventsource"):
                            findings.append(_missing(block_id, target, "dashboard_data_loading"))
                        if not _has_any(code, r"empty", r"length\s*===?\s*0", r"\{:\s*else\}"):
                            findings.append(_missing(block_id, target, "dashboard_empty_state"))
                        if not _has_any(code, r"new\s+eventsource", r"new\s+websocket", r"\.subscribe\(", r"monitorstore"):
                            findings.append(_missing(block_id, target, "dashboard_realtime_updates"))
                        if not _has_any(code, r"uptime", r"sparkline", r"chart"):
                            findings.append(_missing(block_id, target, "dashboard_uptime_or_latency_visualization"))
                    elif name in {"hosts.svelte", "services.svelte"}:
                        resource = "host" if name == "hosts.svelte" else "service"
                        for contract, patterns in {
                            "load": (r"fetch\(", r"onmount"),
                            "create": (r"method\s*:\s*['\"]post", r"\.post\(", r"handlecreate"),
                            "update": (r"method\s*:\s*['\"](?:put|patch)", r"handleedit", r"handleupdate"),
                            "delete": (r"method\s*:\s*['\"]delete", r"handledelete"),
                            "error_feedback": (r"catch", r"dialog\.(?:alert|confirm)", r"error"),
                        }.items():
                            if not _has_any(code, *patterns):
                                findings.append(_missing(block_id, target, f"{resource}_crud_{contract}"))
                    elif name.startswith("monitormanage"):
                        for contract, patterns in {
                            "load": (r"fetch\(", r"fetchmonitors", r"onmount"),
                            "create": (r"method\s*:\s*['\"]post", r"\.post\(", r"handleadd"),
                            "update": (r"method\s*:\s*['\"]put", r"method\s*:\s*['\"]patch", r"handleedit", r"handleupdate"),
                            "delete": (r"method\s*:\s*['\"]delete", r"handledelete", r"customconfirm"),
                            "error_feedback": (r"catch", r"customalert", r"error"),
                        }.items():
                            if not _has_any(code, *patterns):
                                findings.append(_missing(block_id, target, f"monitor_crud_{contract}"))
                    elif name.startswith("settings"):
                        if not _has_any(code, r"fetch\(", r"axios", r"request\(", r"localstorage", r"settingsstore"):
                            findings.append(_missing(block_id, target, "settings_persistence"))
                        if not _has_any(code, r"method\s*:\s*['\"](?:put|patch|post)", r"\.put\(", r"\.patch\(", r"\.post\(", r"fetch\("):
                            findings.append(_missing(block_id, target, "settings_write_request"))
                        if not _has_any(code, r"catch", r"customalert", r"error"):
                            findings.append(_missing(block_id, target, "settings_error_feedback"))
                    elif name.startswith("targetdetail"):
                        if not _has_any(code, r"fetch\(", r"onmount"):
                            findings.append(_missing(block_id, target, "target_detail_data_loading"))
                        if not _has_any(code, r"history", r"latency", r"probe"):
                            findings.append(_missing(block_id, target, "target_detail_history_or_probe"))
                        if not _has_any(code, r"\{#if\s+error", r"error\s*=", r"error_message", r"customalert"):
                            findings.append(_missing(block_id, target, "target_detail_error_state"))
                    elif name in {"servicedetail.svelte", "servicedetails.svelte"}:
                        if not _has_any(code, r"fetch\(", r"onmount"):
                            findings.append(_missing(block_id, target, "service_detail_data_loading"))
                        if not _has_any(code, r"history", r"latency", r"probe"):
                            findings.append(_missing(block_id, target, "service_detail_history"))
                        if not _has_any(code, r"chart", r"sparkline", r"svg", r"canvas"):
                            findings.append(_missing(block_id, target, "service_detail_latency_visualization"))
                        if not _has_any(code, r"loading", r"\{#if\s+error", r"error\s*=", r"catch"):
                            findings.append(_missing(block_id, target, "service_detail_loading_or_error_state"))
                elif "router" in target.lower():
                    if not _has_any(code, r"location\.hash", r"hashchange"):
                        findings.append(_missing(block_id, target, "hash_change_listener"))
                    if not _has_any(code, r"notfound", r"404", r"route\s*\|\|", r"routes\["):
                        findings.append(_missing(block_id, target, "unknown_route_fallback"))
                    if not _has_any(code, r"push\(", r"navigate", r"render", r"component", r"router"):
                        findings.append(_missing(block_id, target, "hash_route_dispatch"))

            if path.suffix in {".js", ".ts", ".tsx"} and "store" in target.lower():
                if "monitor" in name:
                    for contract, patterns in {
                        "initial_fetch": (r"fetch\(", r"axios", r"request\("),
                        "realtime_subscription": (r"eventsource", r"websocket", r"subscribe"),
                        "state_update": (r"\.set\(", r"setstate", r"dispatch", r"update\("),
                        "failure_state": (r"catch", r"error", r"onerror"),
                    }.items():
                        if not _has_any(code, *patterns):
                            findings.append(_missing(block_id, target, f"monitor_store_{contract}"))
                if "dialog" in name:
                    for contract, patterns in {
                        "alert": (r"alert",),
                        "confirm": (r"confirm",),
                        "prompt": (r"prompt",),
                        "resolution": (r"resolve\(", r"reject\("),
                    }.items():
                        if not _has_any(code, *patterns):
                            findings.append(_missing(block_id, target, f"dialog_store_{contract}"))

            if path.suffix == ".go":
                if "/prober/" in target.lower():
                    if not _has_any(code, r"context\.withtimeout", r"context\.timeout", r"dialtimeout", r"client\s*:=.*timeout", r"timeout"):
                        findings.append(_missing(block_id, target, "probe_timeout"))
                    if name == "prober.go":
                        if not _has_any(code, r"switch"):
                            findings.append(_missing(block_id, target, "probe_dispatch"))
                        for contract, patterns in {
                            "http_dispatch": (r"typehttp", r"typehttps", r"http"),
                            "tcp_dispatch": (r"typetcp", r"tcp"),
                            "ping_dispatch": (r"ping", r"icmp", r"echo"),
                            "retry": (r"retry", r"attempt", r"for\s+.*attempt", r"maxattempt"),
                        }.items():
                            if not _has_any(code, *patterns):
                                findings.append(_missing(block_id, target, f"probe_{contract}"))
                if "/scheduler/" in target.lower():
                    for contract, patterns in {
                        "periodic_trigger": (r"ticker", r"time\.newticker", r"time\.tick"),
                        "concurrency": (r"go\s+func", r"goroutine", r"worker", r"semaphore", r"chan\s"),
                        "cancellation": (r"context", r"done\s*\(", r"cancel", r"stop\("),
                    }.items():
                        if not _has_any(code, *patterns):
                            findings.append(_missing(block_id, target, f"scheduler_{contract}"))
                if "/db/" in target.lower() or "migration" in name:
                    for contract, patterns in {
                        "schema_or_queries": (r"create\s+table", r"insert\s+into", r"select\s+", r"exec\("),
                        "transaction_or_locking": (r"transaction", r"begin\(", r"commit\(", r"wal", r"busy_timeout"),
                    }.items():
                        if not _has_any(code, *patterns):
                            findings.append(_missing(block_id, target, f"database_{contract}"))
                if "/api/" in target.lower() or name in {"routes.go", "handlers.go", "sse.go"}:
                    if name == "routes.go" and not _has_any(code, r"app\.(get|post|put|patch|delete|group)\s*\(", r"\.(get|post|put|patch|delete)\s*\("):
                        findings.append(_missing(block_id, target, "http_route_registration"))
                    if name == "handlers.go" and not _has_any(code, r"status\.(badrequest|internalservererror|ok)", r"status\(4\d\d\)", r"status\(5\d\d\)", r"return.*error"):
                        findings.append(_missing(block_id, target, "http_error_contract"))
                    if name == "sse.go" and not _has_any(code, r"event-stream", r"setbodystreamwriter", r"flush\("):
                        findings.append(_missing(block_id, target, "sse_stream_contract"))
                if "/tray/" in target.lower() or name in {"tray.go", "systray.go"}:
                    if not _has_any(code, r"green|healthy|ok", r"yellow|warning|degraded", r"red|down|critical"):
                        findings.append(_missing(block_id, target, "tray_status_color_mapping"))
                    for contract, patterns in {
                        "open": (r"open", r"showwindow", r"show\("),
                        "scan_or_refresh": (r"scan", r"probe", r"refresh", r"check\s+all"),
                        "pause": (r"pause", r"resume", r"suspend"),
                        "quit": (r"quit", r"exit"),
                    }.items():
                        if not _has_any(code, *patterns):
                            findings.append(_missing(block_id, target, f"tray_menu_{contract}"))
                if name.endswith("_test.go") or name == "main_test.go":
                    if not _has_any(code, r"func\s+Test[A-Z]", r"assert", r"require", r"if\s+.*!=", r"t\.error", r"t\.fatal"):
                        findings.append(_missing(block_id, target, "test_assertion"))

            if path.suffix == ".svelte" and "components/ui/" in target.lower():
                if not _has_any(code, r"export\s+let", r"bind:", r"createeventdispatcher", r"on:"):
                    findings.append(_missing(block_id, target, "interactive_control_contract"))

    # Cross-file contracts prevent a frontend from advertising endpoints that the
    # backend never registers. They also catch a generated blueprint that is
    # individually plausible but incomplete as a project.
    require_file("internal/api/handlers.go", "host_update_handler", r"UpdateHost")
    require_file("internal/api/handlers.go", "service_update_handler", r"UpdateService")
    require_file("internal/api/handlers.go", "settings_read_handler", r"GetSettings")
    require_file("internal/api/handlers.go", "settings_write_handler", r"UpdateSettings")
    require_file("internal/api/server.go", "host_put_route", r"hosts\.(?:Put|Patch)", r"hosts\.Route")
    require_file("internal/api/server.go", "service_put_route", r"services\.(?:Put|Patch)", r"services\.Route")
    require_file("internal/api/server.go", "settings_routes", r"settings\.(?:Get|Put|Patch)")
    require_file("internal/domain/models.go", "host_mac_address", r"MacAddress", r"mac_address")
    require_file("internal/domain/models.go", "unknown_status", r"StatusUnknown", r"UNKNOWN")
    require_file("internal/domain/models.go", "system_setting_entity", r"SystemSetting", r"system_setting")
    require_file("internal/repository/sqlite.go", "retention_or_settings_schema", r"system_settings", r"retention", r"health_check_logs")
    require_file("internal/repository/sqlite.go", "retention_cleanup_query", r"delete\s+from\s+health_check_logs", r"retention")
    require_file("internal/prober/scheduler.go", "scheduler_path_detection", r"ticker", r"worker")
    require_file("internal/prober/scheduler.go", "alert_event_recording", r"alert_events", r"service_down", r"service_recovered")
    require_file("internal/api/server.go", "static_frontend_delivery", r"app\.static", r"static\(", r"embed", r"frontend/dist")
    require_file("main.go", "systray_wiring", r"BuildSystrayMenu", r"systray", r"SystrayManager")

    # A Go file cannot declare const/var/type/func before its import block.
    for target, code in implementation_files.items():
        if not target.endswith(".go"):
            continue
        package_end = re.search(r"^package\s+\w+\s*$", code, re.MULTILINE)
        import_match = re.search(r"^import(?:\s|\()", code, re.MULTILINE)
        declaration_before_import = re.search(r"^(?:const|var|type|func)\b", code, re.MULTILINE)
        if import_match and declaration_before_import and declaration_before_import.start() < import_match.start():
            findings.append(_missing(f"file:{target}", target, "go_imports_before_declarations"))

    # Local-font requirements are behavioral: a local fallback alone is not an
    # offline font asset, and one font manifest cannot satisfy two named fonts.
    require_file("frontend/src/app.css", "local_font_assets", r"url\(", r"@font-face")
    if "@font-face" in all_implementation_code.lower():
        if not _has_any(all_implementation_code, r"inter", r"jetbrains\s*mono"):
            findings.append("code_block_semantic_contract_missing:project:frontend:both_required_local_fonts")
    font_assets = [target for target in implementation_files if "/font" in target or target.endswith((".woff", ".woff2", ".ttf", ".otf"))]
    if font_assets and not any("inter" in target for target in font_assets):
        findings.append("code_block_semantic_contract_missing:project:frontend:inter_font_asset")
    if font_assets and not any("jetbrains" in target or "mono" in target for target in font_assets):
        findings.append("code_block_semantic_contract_missing:project:frontend:jetbrains_mono_font_asset")

    return sorted(set(findings))


__all__ = ["validate_code_block_semantics"]
