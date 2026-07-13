---
artifact_type: code_size_verification
feature_id: FEAT-001
status: FAIL
violations_count: 449
---

# Code Size Governance Report – FEAT-001

## 1. Executive Summary
Báo cáo kiểm soát kích thước mã nguồn và nợ kỹ thuật cho Work Item FEAT-001.

- **File Size Policy**: FAIL
- **Function Size Policy**: FAIL
- **Class Size Policy**: FAIL
- **Overall Status**: FAIL

## 2. Policy Violations & Recommendations

| File | Scope | Name | Current Size / Lines | Policy Limit | Status | Recommendation |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| tools/obsidian_sync.py | Function | run_push | 89 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_push' thành các hàm con (helper functions). |
| tools/obsidian_sync.py | Function | run_pull | 67 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_pull' thành các hàm con (helper functions). |
| tools/test_obsidian_sync.py | Function | test_push_and_pull_simulation | 78 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_push_and_pull_simulation' thành các hàm con (helper functions). |
| public_export/runtime/scripts/project_memory/update.py | Function | parse_new_lessons | 63 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'parse_new_lessons' thành các hàm con (helper functions). |
| public_export/runtime/scripts/project_memory/update.py | Function | run_update | 182 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_update' thành các hàm con (helper functions). |
| public_export/runtime/scripts/project_memory/bootstrap.py | Function | run_bootstrap | 124 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_bootstrap' thành các hàm con (helper functions). |
| public_export/runtime/scripts/project_memory/markdown_writer.py | Function | generate_project_summary | 76 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'generate_project_summary' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/tests/conftest.py | Function | isolated_workspace | 67 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'isolated_workspace' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/tests/unit/test_orchestrator_singleton_pytest_limits.py | Function | test_pytest_coordinator_coalescing | 62 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_pytest_coordinator_coalescing' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/tests/unit/test_routing.py | Function | test_invalid_routing_detection | 56 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_invalid_routing_detection'. |
| public_export/skills/workflow-runtime/tests/unit/test_orchestrator_cli.py | Function | test_agents_workflows_queue_graph_locks | 47 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_agents_workflows_queue_graph_locks'. |
| public_export/skills/workflow-runtime/tests/unit/test_initialize_workspace_orchestrator.py | Function | test_do_init_second_invocation_attach | 46 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_do_init_second_invocation_attach'. |
| public_export/skills/workflow-runtime/tests/unit/test_project_memory.py | Function | setUp | 56 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'setUp'. |
| public_export/skills/workflow-runtime/tests/integration/test_refactoring.py | Class | TestRefactoringEngine | 371 | 300 | FAIL | Tách lớp 'TestRefactoringEngine' thành các lớp con chuyên trách (SRP). |
| public_export/skills/workflow-runtime/tests/integration/test_refactoring.py | ClassMethods | TestRefactoringEngine | 21 | 20 | FAIL | Lớp 'TestRefactoringEngine' chứa quá nhiều phương thức. Gom nhóm phương thức sang các lớp helper. |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | File | public_export/skills/workflow-runtime/tests/integration/test_runtime.py | 1153 | 500 | FAIL | Split file into smaller module files (e.g. test_runtimeCore, test_runtimeHelper). |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | Function | setUp | 61 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'setUp' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | Function | tearDown | 55 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'tearDown'. |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_sqlite_databases_and_scopes | 56 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_sqlite_databases_and_scopes'. |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_accurate_token_estimation_and_database_normalization | 74 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_accurate_token_estimation_and_database_normalization' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_suggestion_gate_scenarios | 154 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_suggestion_gate_scenarios' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_permission_mode_scenarios | 89 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_permission_mode_scenarios' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_execution_modes_and_persistence | 109 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_execution_modes_and_persistence' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_parallel_scope_constraints | 77 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_parallel_scope_constraints' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_analysis_agent_lifecycle | 80 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_analysis_agent_lifecycle' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_telemetry_config_loading_and_fallback | 102 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_telemetry_config_loading_and_fallback' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | Class | TestRuntimeEngine | 1122 | 300 | FAIL | Tách lớp 'TestRuntimeEngine' thành các lớp con chuyên trách (SRP). |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | ClassMethods | TestRuntimeEngine | 22 | 20 | FAIL | Lớp 'TestRuntimeEngine' chứa quá nhiều phương thức. Gom nhóm phương thức sang các lớp helper. |
| public_export/skills/workflow-runtime/tests/integration/test_agents_merge.py | Function | setUp | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'setUp'. |
| public_export/skills/workflow-runtime/tests/integration/test_agents_merge.py | Class | TestAgentsMerge | 374 | 300 | FAIL | Tách lớp 'TestAgentsMerge' thành các lớp con chuyên trách (SRP). |
| public_export/skills/workflow-runtime/tests/integration/test_agents_merge.py | ClassMethods | TestAgentsMerge | 21 | 20 | FAIL | Lớp 'TestAgentsMerge' chứa quá nhiều phương thức. Gom nhóm phương thức sang các lớp helper. |
| public_export/skills/workflow-runtime/tests/integration/test_state_engine.py | Function | test_cli_commands_and_state_recovery | 54 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_cli_commands_and_state_recovery'. |
| public_export/skills/workflow-runtime/tests/integration/test_code_size_governor.py | Function | test_run_code_size_audit | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_run_code_size_audit'. |
| public_export/skills/workflow-runtime/scripts/validator.py | Function | get_git_info | 53 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'get_git_info'. |
| public_export/skills/workflow-runtime/scripts/project_discovery.py | Function | run_discovery | 218 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_discovery' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | File | public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | 1251 | 500 | FAIL | Split file into smaller module files (e.g. autonomous_orchestratorCore, autonomous_orchestratorHelper). |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | create_authorization | 66 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'create_authorization' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | run_autonomous_delivery | 421 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_autonomous_delivery' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | get_orchestrator_status | 70 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_orchestrator_status' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | get_orchestrator_health | 102 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_orchestrator_health' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | print_agents_extended | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'print_agents_extended'. |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | print_workflows_extended | 63 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'print_workflows_extended' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | print_queue_extended | 59 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'print_queue_extended'. |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | print_metrics_extended | 69 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'print_metrics_extended' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | print_logs_extended | 51 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'print_logs_extended'. |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | execute_node | 133 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'execute_node' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/db.py | File | public_export/skills/workflow-runtime/scripts/db.py | 1324 | 500 | FAIL | Split file into smaller module files (e.g. dbCore, dbHelper). |
| public_export/skills/workflow-runtime/scripts/db.py | Function | init_db_schema | 264 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'init_db_schema' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/db.py | Function | save_provider_request | 53 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'save_provider_request'. |
| public_export/skills/workflow-runtime/scripts/db.py | Function | get_provider_requests | 92 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_provider_requests' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/db.py | Function | save_timeline_event | 47 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'save_timeline_event'. |
| public_export/skills/workflow-runtime/scripts/db.py | Function | save_usage_to_dbs | 71 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'save_usage_to_dbs' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/db.py | Function | get_workflow_summary | 174 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_workflow_summary' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/db.py | Function | get_project_summary | 70 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_project_summary' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/db.py | Function | get_global_summary | 69 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_global_summary' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/db.py | Function | normalize_database_records | 53 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'normalize_database_records'. |
| public_export/skills/workflow-runtime/scripts/state_store.py | Function | get | 63 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/state_store.py | Function | set | 68 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'set' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/diff_engine.py | Function | calculate_diff | 54 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'calculate_diff'. |
| public_export/skills/workflow-runtime/scripts/artifact_validator.py | Function | validate_blueprint_file | 127 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate_blueprint_file' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/aiwf_registry.py | Function | register_project | 66 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'register_project' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/aiwf_registry.py | Function | update_all_projects | 99 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'update_all_projects' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/code_size_governor.py | Function | analyze_python_file | 58 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'analyze_python_file'. |
| public_export/skills/workflow-runtime/scripts/code_size_governor.py | Function | analyze_go_file | 81 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'analyze_go_file' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/code_size_governor.py | Function | run_code_size_audit | 150 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_code_size_audit' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/code_size_governor.py | Function | generate_code_size_report | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'generate_code_size_report'. |
| public_export/skills/workflow-runtime/scripts/test_coordinator.py | File | public_export/skills/workflow-runtime/scripts/test_coordinator.py | 598 | 500 | FAIL | Split file into smaller module files (e.g. test_coordinatorCore, test_coordinatorHelper). |
| public_export/skills/workflow-runtime/scripts/test_coordinator.py | Function | run_stability_worker | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'run_stability_worker'. |
| public_export/skills/workflow-runtime/scripts/test_coordinator.py | Function | check_rate_limit | 57 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'check_rate_limit'. |
| public_export/skills/workflow-runtime/scripts/test_coordinator.py | Function | run_coordinated | 115 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_coordinated' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/test_coordinator.py | Function | _wait_in_queue | 71 | 60 | FAIL | Trích xuất mã nguồn trong hàm '_wait_in_queue' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/test_coordinator.py | Function | _execute_pytest | 187 | 60 | FAIL | Trích xuất mã nguồn trong hàm '_execute_pytest' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/test_coordinator.py | Class | TestCoordinator | 501 | 300 | FAIL | Tách lớp 'TestCoordinator' thành các lớp con chuyên trách (SRP). |
| public_export/skills/workflow-runtime/scripts/update_source.py | Function | handle_update_source | 67 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'handle_update_source' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/update_source.py | Function | check_status | 73 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'check_status' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/patch_skill_requirements.py | File | public_export/skills/workflow-runtime/scripts/patch_skill_requirements.py | 449 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| public_export/skills/workflow-runtime/scripts/hierarchical_runtime.py | File | public_export/skills/workflow-runtime/scripts/hierarchical_runtime.py | 746 | 500 | FAIL | Split file into smaller module files (e.g. hierarchical_runtimeCore, hierarchical_runtimeHelper). |
| public_export/skills/workflow-runtime/scripts/hierarchical_runtime.py | Function | setup_windows_job_object | 80 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'setup_windows_job_object' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/hierarchical_runtime.py | Function | execute_subagent | 67 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'execute_subagent' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/hierarchical_runtime.py | Function | update_canonical_state_files | 110 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'update_canonical_state_files' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/hierarchical_runtime.py | Function | can_spawn_subagent | 76 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'can_spawn_subagent' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/hierarchical_runtime.py | Function | start_daemon_loop | 59 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'start_daemon_loop'. |
| public_export/skills/workflow-runtime/scripts/hierarchical_runtime.py | Class | HierarchicalRuntime | 577 | 300 | FAIL | Tách lớp 'HierarchicalRuntime' thành các lớp con chuyên trách (SRP). |
| public_export/skills/workflow-runtime/scripts/session.py | File | public_export/skills/workflow-runtime/scripts/session.py | 759 | 500 | FAIL | Split file into smaller module files (e.g. sessionCore, sessionHelper). |
| public_export/skills/workflow-runtime/scripts/session.py | Function | get_default_authorization_state | 53 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'get_default_authorization_state'. |
| public_export/skills/workflow-runtime/scripts/session.py | Function | migrate_session_schema | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'migrate_session_schema'. |
| public_export/skills/workflow-runtime/scripts/session.py | Function | load_session | 58 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'load_session'. |
| public_export/skills/workflow-runtime/scripts/session.py | Function | save_session_atomic | 47 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'save_session_atomic'. |
| public_export/skills/workflow-runtime/scripts/session.py | Function | load_guardrails_summary | 51 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'load_guardrails_summary'. |
| public_export/skills/workflow-runtime/scripts/session.py | Function | validate_runtime_policy | 58 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'validate_runtime_policy'. |
| public_export/skills/workflow-runtime/scripts/adaptive_scheduler.py | File | public_export/skills/workflow-runtime/scripts/adaptive_scheduler.py | 422 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| public_export/skills/workflow-runtime/scripts/adaptive_scheduler.py | Function | plan_team_and_graph | 66 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'plan_team_and_graph' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/adaptive_scheduler.py | Function | execute_task | 90 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'execute_task' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/adaptive_scheduler.py | Function | execute_graph | 54 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'execute_graph'. |
| public_export/skills/workflow-runtime/scripts/release_manager.py | Function | run_release_execute | 111 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_release_execute' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/context.py | File | public_export/skills/workflow-runtime/scripts/context.py | 557 | 500 | FAIL | Split file into smaller module files (e.g. contextCore, contextHelper). |
| public_export/skills/workflow-runtime/scripts/context.py | Function | parse_transcript | 106 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'parse_transcript' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/context.py | Function | sync_request_history | 323 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'sync_request_history' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/utils.py | Function | prompt_select | 91 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'prompt_select' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_state.py | Function | resume_session | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'resume_session'. |
| public_export/skills/workflow-runtime/scripts/budget_controller.py | Function | init_budget_tables | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'init_budget_tables'. |
| public_export/skills/workflow-runtime/scripts/budget_controller.py | Function | evaluate_budget | 57 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'evaluate_budget'. |
| public_export/skills/workflow-runtime/scripts/dependency_resolver.py | File | public_export/skills/workflow-runtime/scripts/dependency_resolver.py | 929 | 500 | FAIL | Split file into smaller module files (e.g. dependency_resolverCore, dependency_resolverHelper). |
| public_export/skills/workflow-runtime/scripts/dependency_resolver.py | Function | parse_requirements | 51 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'parse_requirements'. |
| public_export/skills/workflow-runtime/scripts/dependency_resolver.py | Function | validate_requirements | 76 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate_requirements' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/dependency_resolver.py | Function | resolve_requirements | 71 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'resolve_requirements' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/dependency_resolver.py | Function | get_doctor_report | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'get_doctor_report'. |
| public_export/skills/workflow-runtime/scripts/task_orchestrator.py | File | public_export/skills/workflow-runtime/scripts/task_orchestrator.py | 681 | 500 | FAIL | Split file into smaller module files (e.g. task_orchestratorCore, task_orchestratorHelper). |
| public_export/skills/workflow-runtime/scripts/task_orchestrator.py | Function | build_task_graph | 103 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'build_task_graph' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/task_orchestrator.py | Function | transition_task_state | 85 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'transition_task_state' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/task_orchestrator.py | Function | get_next_ready_task | 93 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_next_ready_task' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/task_orchestrator.py | Function | validate_phase_completion | 95 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate_phase_completion' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/init_wizard.py | Function | generate_scaffold | 66 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'generate_scaffold' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/init_wizard.py | Function | run_interactive | 61 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_interactive' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/forecaster.py | Function | make_forecast | 72 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'make_forecast' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/skill_classifier.py | Function | classify_intent | 128 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'classify_intent' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/optimizer.py | Function | init_optimizer_tables | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'init_optimizer_tables'. |
| public_export/skills/workflow-runtime/scripts/architecture_validator.py | Function | run_architecture_validation | 141 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_architecture_validation' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/architecture_validator.py | Function | generate_architecture_report | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'generate_architecture_report'. |
| public_export/skills/workflow-runtime/scripts/validation_runner.py | Function | run_pipeline | 83 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_pipeline' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/validation_runner.py | Function | run_verify | 80 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_verify' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/lease.py | Function | inspect | 59 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'inspect'. |
| public_export/skills/workflow-runtime/scripts/lease.py | Function | acquire | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'acquire'. |
| public_export/skills/workflow-runtime/scripts/isolation_rules.py | Function | process_incoming_prompt | 90 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'process_incoming_prompt' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/safe_multi_agent_writes.py | File | public_export/skills/workflow-runtime/scripts/safe_multi_agent_writes.py | 604 | 500 | FAIL | Split file into smaller module files (e.g. safe_multi_agent_writesCore, safe_multi_agent_writesHelper). |
| public_export/skills/workflow-runtime/scripts/safe_multi_agent_writes.py | Function | plan_team | 94 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'plan_team' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/safe_multi_agent_writes.py | Function | acquire_lease | 70 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'acquire_lease' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/safe_multi_agent_writes.py | Function | validate_write | 62 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate_write' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/safe_multi_agent_writes.py | Function | integrate_next | 120 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'integrate_next' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/breakdown_engine.py | Function | generate_breakdown | 279 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'generate_breakdown' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/insights_engine.py | Function | generate_recommendations | 100 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'generate_recommendations' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/agent_routing.py | Function | validate_routing | 90 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate_routing' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/benchmark_init_flow.py | File | public_export/skills/workflow-runtime/scripts/benchmark_init_flow.py | 614 | 500 | FAIL | Split file into smaller module files (e.g. benchmark_init_flowCore, benchmark_init_flowHelper). |
| public_export/skills/workflow-runtime/scripts/benchmark_init_flow.py | Function | setup_workspace | 76 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'setup_workspace' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/benchmark_init_flow.py | Function | run_old_init | 121 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_old_init' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/benchmark_init_flow.py | Function | run_new_init | 102 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_new_init' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/benchmark_init_flow.py | Function | run_benchmark | 59 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'run_benchmark'. |
| public_export/skills/workflow-runtime/scripts/benchmark_init_flow.py | Function | print_report | 90 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'print_report' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | File | public_export/skills/workflow-runtime/scripts/workflow_runtime.py | 4952 | 500 | FAIL | Split file into smaller module files (e.g. workflow_runtimeCore, workflow_runtimeHelper). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | requires_approval | 54 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'requires_approval'. |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | update_context_health | 157 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'update_context_health' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | ensure_daemon_running | 54 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'ensure_daemon_running'. |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_init | 255 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_init' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_usage | 671 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_usage' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_suggest | 127 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_suggest' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_choice | 263 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_choice' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_active_workflow | 180 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_active_workflow' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_permission | 159 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_permission' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_compact | 98 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_compact' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | sync_execution_state_to_session | 52 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'sync_execution_state_to_session'. |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_task | 75 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_task' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_lock | 78 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_lock' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_execution | 62 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_execution' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_analysis_agent | 75 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_analysis_agent' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_orchestrator | 296 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_orchestrator' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_state_action | 96 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_state_action' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_knowledge_action | 57 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'do_knowledge_action'. |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_test_action | 216 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_test_action' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_provider_action | 320 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_provider_action' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_registry | 51 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'do_registry'. |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_update | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'do_update'. |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_deps | 171 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_deps' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_task_orchestrator | 102 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_task_orchestrator' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_runtime_action | 52 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'do_runtime_action'. |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | Function | main | 563 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'main' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/state_sync.py | Function | aggregate_state | 141 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'aggregate_state' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/state_sync.py | Function | deconstruct_state | 87 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'deconstruct_state' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/state_sync.py | Function | write_initialization_summary | 52 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'write_initialization_summary'. |
| public_export/skills/workflow-runtime/scripts/state_sync.py | Function | validate_no_heavy_init_operations | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'validate_no_heavy_init_operations'. |
| public_export/skills/workflow-runtime/scripts/context_rebuilder.py | Function | build_context_bundle | 57 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'build_context_bundle'. |
| public_export/skills/workflow-runtime/scripts/tia_engine.py | Function | validate_test_architecture | 76 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate_test_architecture' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/tia_engine.py | Function | resolve_affected_tests | 47 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'resolve_affected_tests'. |
| public_export/skills/workflow-runtime/scripts/analytics_engine.py | Function | detect_duplicate_reads | 64 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'detect_duplicate_reads' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/analytics_engine.py | Function | update_analytics | 88 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'update_analytics' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/memory/update.py | Function | parse_new_lessons | 63 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'parse_new_lessons' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/memory/update.py | Function | run_update | 161 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_update' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/memory/bootstrap.py | Function | run_bootstrap | 103 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_bootstrap' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/memory/markdown_writer.py | Function | generate_project_summary | 76 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'generate_project_summary' thành các hàm con (helper functions). |
| public_export/skills/workflow-runtime/scripts/memory/search.py | Function | vector_search | 51 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'vector_search'. |
| public_export/skills/skill-self-verification/scripts/verify_skill.py | File | public_export/skills/skill-self-verification/scripts/verify_skill.py | 419 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| public_export/skills/skill-self-verification/scripts/verify_skill.py | Function | main | 57 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'main'. |
| public_export/skills/skill-self-verification/scripts/verify_skill.py | Function | report | 109 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'report' thành các hàm con (helper functions). |
| public_export/skills/skill-self-verification/scripts/verify_skill.py | Class | SkillVerifier | 322 | 300 | FAIL | Tách lớp 'SkillVerifier' thành các lớp con chuyên trách (SRP). |
| public_export/skills/vir-runtime/scripts/vir_runtime/multi_agent/consensus.py | Function | collect_votes | 59 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'collect_votes'. |
| public_export/skills/vir-runtime/scripts/vir_runtime/sensory/vision/pixel_comparer.py | Function | compare | 58 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'compare'. |
| public_export/skills/frontend-design/scripts/ux_audit.py | File | public_export/skills/frontend-design/scripts/ux_audit.py | 722 | 500 | FAIL | Split file into smaller module files (e.g. ux_auditCore, ux_auditHelper). |
| public_export/skills/frontend-design/scripts/ux_audit.py | Function | audit_file | 568 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'audit_file' thành các hàm con (helper functions). |
| public_export/skills/frontend-design/scripts/ux_audit.py | Class | UXAuditor | 592 | 300 | FAIL | Tách lớp 'UXAuditor' thành các lớp con chuyên trách (SRP). |
| public_export/skills/frontend-design/scripts/accessibility_checker.py | Function | check_accessibility | 65 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'check_accessibility' thành các hàm con (helper functions). |
| public_export/skills/frontend-design/scripts/accessibility_checker.py | Function | main | 69 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'main' thành các hàm con (helper functions). |
| public_export/skills/knowledge-runtime/tests/integration/test_provider_manager.py | File | public_export/skills/knowledge-runtime/tests/integration/test_provider_manager.py | 409 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| public_export/skills/knowledge-runtime/tests/integration/test_provider_manager.py | Class | TestProviderManager | 391 | 300 | FAIL | Tách lớp 'TestProviderManager' thành các lớp con chuyên trách (SRP). |
| public_export/skills/knowledge-runtime/scripts/obsidian_resolver.py | Function | extract_section | 47 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'extract_section'. |
| public_export/skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py | File | public_export/skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py | 712 | 500 | FAIL | Split file into smaller module files (e.g. provider_managerCore, provider_managerHelper). |
| public_export/skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py | Function | test_provider | 55 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_provider'. |
| public_export/skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py | Function | resolve_obsidian_project_folder | 182 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'resolve_obsidian_project_folder' thành các hàm con (helper functions). |
| public_export/skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py | Function | sync_obsidian | 215 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'sync_obsidian' thành các hàm con (helper functions). |
| runtime/scripts/project_memory/update.py | Function | parse_new_lessons | 63 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'parse_new_lessons' thành các hàm con (helper functions). |
| runtime/scripts/project_memory/update.py | Function | run_update | 182 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_update' thành các hàm con (helper functions). |
| runtime/scripts/project_memory/bootstrap.py | Function | run_bootstrap | 124 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_bootstrap' thành các hàm con (helper functions). |
| runtime/scripts/project_memory/markdown_writer.py | Function | generate_project_summary | 76 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'generate_project_summary' thành các hàm con (helper functions). |
| desktop/registry_test.go | Function | TestRegistryOperations | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'TestRegistryOperations'. |
| scratch/spawn_profiler.py | Function | get_process_tree_stats | 67 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_process_tree_stats' thành các hàm con (helper functions). |
| scratch/spawn_profiler.py | Function | main | 60 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'main'. |
| scratch/initialize.py | File | scratch/initialize.py | 513 | 500 | FAIL | Split file into smaller module files (e.g. initializeCore, initializeHelper). |
| scratch/initialize.py | Function | main | 450 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'main' thành các hàm con (helper functions). |
| scratch/update_session.py | Function | main | 133 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'main' thành các hàm con (helper functions). |
| scratch/simulate_user.py | Function | main | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'main'. |
| scratch/run_real_orchestrator_case.py | File | scratch/run_real_orchestrator_case.py | 408 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| scratch/run_real_orchestrator_case.py | Function | run_node | 116 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_node' thành các hàm con (helper functions). |
| scratch/test_parser_filtered.py | Function | parse_with_filter | 46 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'parse_with_filter'. |
| skills/workflow-runtime/tests/test_bat_feat048_053.py | File | skills/workflow-runtime/tests/test_bat_feat048_053.py | 734 | 500 | FAIL | Split file into smaller module files (e.g. test_bat_feat048_053Core, test_bat_feat048_053Helper). |
| skills/workflow-runtime/tests/test_bat_feat048_053.py | Function | test_full_e2e_single_phase_lifecycle | 55 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_full_e2e_single_phase_lifecycle'. |
| skills/workflow-runtime/tests/conftest.py | Function | isolated_workspace | 67 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'isolated_workspace' thành các hàm con (helper functions). |
| skills/workflow-runtime/tests/test_runtime_stress.py | Function | run_blueprint_lifecycle | 62 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_blueprint_lifecycle' thành các hàm con (helper functions). |
| skills/workflow-runtime/tests/test_versioned_pricing.py | Function | test_effective_date_lookup | 69 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_effective_date_lookup' thành các hàm con (helper functions). |
| skills/workflow-runtime/tests/test_feat048_provider_engine.py | File | skills/workflow-runtime/tests/test_feat048_provider_engine.py | 420 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| skills/workflow-runtime/tests/test_task_dag_execution.py | Function | _run_full_phase | 59 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm '_run_full_phase'. |
| skills/workflow-runtime/tests/unit/test_orchestrator_singleton_pytest_limits.py | Function | test_pytest_coordinator_coalescing | 62 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_pytest_coordinator_coalescing' thành các hàm con (helper functions). |
| skills/workflow-runtime/tests/unit/test_routing.py | Function | test_invalid_routing_detection | 56 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_invalid_routing_detection'. |
| skills/workflow-runtime/tests/unit/test_orchestrator_cli.py | Function | test_agents_workflows_queue_graph_locks | 47 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_agents_workflows_queue_graph_locks'. |
| skills/workflow-runtime/tests/unit/test_initialize_workspace_orchestrator.py | Function | test_do_init_second_invocation_attach | 46 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_do_init_second_invocation_attach'. |
| skills/workflow-runtime/tests/unit/test_project_memory.py | Function | setUp | 56 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'setUp'. |
| skills/workflow-runtime/tests/integration/test_refactoring.py | Class | TestRefactoringEngine | 373 | 300 | FAIL | Tách lớp 'TestRefactoringEngine' thành các lớp con chuyên trách (SRP). |
| skills/workflow-runtime/tests/integration/test_refactoring.py | ClassMethods | TestRefactoringEngine | 21 | 20 | FAIL | Lớp 'TestRefactoringEngine' chứa quá nhiều phương thức. Gom nhóm phương thức sang các lớp helper. |
| skills/workflow-runtime/tests/integration/test_runtime.py | File | skills/workflow-runtime/tests/integration/test_runtime.py | 1153 | 500 | FAIL | Split file into smaller module files (e.g. test_runtimeCore, test_runtimeHelper). |
| skills/workflow-runtime/tests/integration/test_runtime.py | Function | setUp | 61 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'setUp' thành các hàm con (helper functions). |
| skills/workflow-runtime/tests/integration/test_runtime.py | Function | tearDown | 55 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'tearDown'. |
| skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_sqlite_databases_and_scopes | 56 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_sqlite_databases_and_scopes'. |
| skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_accurate_token_estimation_and_database_normalization | 74 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_accurate_token_estimation_and_database_normalization' thành các hàm con (helper functions). |
| skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_suggestion_gate_scenarios | 154 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_suggestion_gate_scenarios' thành các hàm con (helper functions). |
| skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_permission_mode_scenarios | 89 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_permission_mode_scenarios' thành các hàm con (helper functions). |
| skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_execution_modes_and_persistence | 109 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_execution_modes_and_persistence' thành các hàm con (helper functions). |
| skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_parallel_scope_constraints | 77 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_parallel_scope_constraints' thành các hàm con (helper functions). |
| skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_analysis_agent_lifecycle | 80 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_analysis_agent_lifecycle' thành các hàm con (helper functions). |
| skills/workflow-runtime/tests/integration/test_runtime.py | Function | test_telemetry_config_loading_and_fallback | 102 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'test_telemetry_config_loading_and_fallback' thành các hàm con (helper functions). |
| skills/workflow-runtime/tests/integration/test_runtime.py | Class | TestRuntimeEngine | 1122 | 300 | FAIL | Tách lớp 'TestRuntimeEngine' thành các lớp con chuyên trách (SRP). |
| skills/workflow-runtime/tests/integration/test_runtime.py | ClassMethods | TestRuntimeEngine | 22 | 20 | FAIL | Lớp 'TestRuntimeEngine' chứa quá nhiều phương thức. Gom nhóm phương thức sang các lớp helper. |
| skills/workflow-runtime/tests/integration/test_agents_merge.py | Function | setUp | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'setUp'. |
| skills/workflow-runtime/tests/integration/test_agents_merge.py | Class | TestAgentsMerge | 374 | 300 | FAIL | Tách lớp 'TestAgentsMerge' thành các lớp con chuyên trách (SRP). |
| skills/workflow-runtime/tests/integration/test_agents_merge.py | ClassMethods | TestAgentsMerge | 21 | 20 | FAIL | Lớp 'TestAgentsMerge' chứa quá nhiều phương thức. Gom nhóm phương thức sang các lớp helper. |
| skills/workflow-runtime/tests/integration/test_state_engine.py | Function | test_cli_commands_and_state_recovery | 56 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_cli_commands_and_state_recovery'. |
| skills/workflow-runtime/tests/integration/test_code_size_governor.py | Function | test_run_code_size_audit | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_run_code_size_audit'. |
| skills/workflow-runtime/scripts/validator.py | Function | get_git_info | 53 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'get_git_info'. |
| skills/workflow-runtime/scripts/state_aggregator.py | Function | aggregate | 125 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'aggregate' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/state_aggregator.py | Function | _compute_gates | 70 | 60 | FAIL | Trích xuất mã nguồn trong hàm '_compute_gates' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/state_aggregator.py | Class | StateAggregator | 326 | 300 | FAIL | Tách lớp 'StateAggregator' thành các lớp con chuyên trách (SRP). |
| skills/workflow-runtime/scripts/project_discovery.py | Function | run_discovery | 218 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_discovery' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/patch_applier.py | Function | apply | 49 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'apply'. |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | File | skills/workflow-runtime/scripts/autonomous_orchestrator.py | 1414 | 500 | FAIL | Split file into smaller module files (e.g. autonomous_orchestratorCore, autonomous_orchestratorHelper). |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | create_authorization | 66 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'create_authorization' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | run_autonomous_delivery | 421 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_autonomous_delivery' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | get_orchestrator_status | 70 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_orchestrator_status' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | follow_orchestrator_status | 162 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'follow_orchestrator_status' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | get_orchestrator_health | 102 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_orchestrator_health' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | print_agents_extended | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'print_agents_extended'. |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | print_workflows_extended | 63 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'print_workflows_extended' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | print_queue_extended | 59 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'print_queue_extended'. |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | print_metrics_extended | 69 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'print_metrics_extended' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | print_logs_extended | 51 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'print_logs_extended'. |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | Function | execute_node | 133 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'execute_node' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/fingerprint_engine.py | Function | register | 58 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'register'. |
| skills/workflow-runtime/scripts/db.py | File | skills/workflow-runtime/scripts/db.py | 1621 | 500 | FAIL | Split file into smaller module files (e.g. dbCore, dbHelper). |
| skills/workflow-runtime/scripts/db.py | Function | init_db_schema | 439 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'init_db_schema' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/db.py | Function | save_provider_request | 58 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'save_provider_request'. |
| skills/workflow-runtime/scripts/db.py | Function | batch_insert_provider_requests | 70 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'batch_insert_provider_requests' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/db.py | Function | get_provider_requests | 97 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_provider_requests' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/db.py | Function | save_timeline_event | 47 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'save_timeline_event'. |
| skills/workflow-runtime/scripts/db.py | Function | save_usage_to_dbs | 71 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'save_usage_to_dbs' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/db.py | Function | get_workflow_summary | 174 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_workflow_summary' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/db.py | Function | get_project_summary | 70 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_project_summary' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/db.py | Function | get_global_summary | 69 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_global_summary' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/db.py | Function | normalize_database_records | 53 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'normalize_database_records'. |
| skills/workflow-runtime/scripts/state_store.py | Function | get | 63 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/state_store.py | Function | set | 68 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'set' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/lock_manager.py | Function | acquire | 66 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'acquire' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/diff_engine.py | Function | calculate_diff | 54 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'calculate_diff'. |
| skills/workflow-runtime/scripts/usage_validator.py | Function | main | 49 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'main'. |
| skills/workflow-runtime/scripts/usage_validator.py | Function | validate | 62 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/usage_validator.py | Function | doctor | 56 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'doctor'. |
| skills/workflow-runtime/scripts/artifact_validator.py | Function | validate_blueprint_file | 127 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate_blueprint_file' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/aiwf_registry.py | Function | register_project | 66 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'register_project' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/aiwf_registry.py | Function | update_all_projects | 99 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'update_all_projects' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/code_size_governor.py | Function | analyze_python_file | 58 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'analyze_python_file'. |
| skills/workflow-runtime/scripts/code_size_governor.py | Function | analyze_go_file | 81 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'analyze_go_file' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/code_size_governor.py | Function | run_code_size_audit | 150 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_code_size_audit' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/code_size_governor.py | Function | generate_code_size_report | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'generate_code_size_report'. |
| skills/workflow-runtime/scripts/provider_engine.py | Function | cmd_parse | 75 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'cmd_parse' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/provider_engine.py | Function | cmd_reprice | 77 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'cmd_reprice' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/provider_engine.py | Function | main | 51 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'main'. |
| skills/workflow-runtime/scripts/atomic_writer.py | Function | write_json_atomic | 57 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'write_json_atomic'. |
| skills/workflow-runtime/scripts/test_coordinator.py | File | skills/workflow-runtime/scripts/test_coordinator.py | 678 | 500 | FAIL | Split file into smaller module files (e.g. test_coordinatorCore, test_coordinatorHelper). |
| skills/workflow-runtime/scripts/test_coordinator.py | Function | kill_process_tree | 79 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'kill_process_tree' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/test_coordinator.py | Function | run_stability_worker | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'run_stability_worker'. |
| skills/workflow-runtime/scripts/test_coordinator.py | Function | check_rate_limit | 57 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'check_rate_limit'. |
| skills/workflow-runtime/scripts/test_coordinator.py | Function | run_coordinated | 115 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_coordinated' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/test_coordinator.py | Function | _wait_in_queue | 71 | 60 | FAIL | Trích xuất mã nguồn trong hàm '_wait_in_queue' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/test_coordinator.py | Function | _execute_pytest | 187 | 60 | FAIL | Trích xuất mã nguồn trong hàm '_execute_pytest' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/test_coordinator.py | Class | TestCoordinator | 501 | 300 | FAIL | Tách lớp 'TestCoordinator' thành các lớp con chuyên trách (SRP). |
| skills/workflow-runtime/scripts/update_source.py | Function | handle_update_source | 67 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'handle_update_source' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/update_source.py | Function | check_status | 73 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'check_status' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/patch_skill_requirements.py | File | skills/workflow-runtime/scripts/patch_skill_requirements.py | 449 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| skills/workflow-runtime/scripts/ledger.py | Function | init_from_blueprint | 104 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'init_from_blueprint' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/ledger.py | Class | ImplementationLedger | 344 | 300 | FAIL | Tách lớp 'ImplementationLedger' thành các lớp con chuyên trách (SRP). |
| skills/workflow-runtime/scripts/hierarchical_runtime.py | File | skills/workflow-runtime/scripts/hierarchical_runtime.py | 815 | 500 | FAIL | Split file into smaller module files (e.g. hierarchical_runtimeCore, hierarchical_runtimeHelper). |
| skills/workflow-runtime/scripts/hierarchical_runtime.py | Function | setup_windows_job_object | 80 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'setup_windows_job_object' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/hierarchical_runtime.py | Function | execute_subagent | 71 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'execute_subagent' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/hierarchical_runtime.py | Function | update_canonical_state_files | 107 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'update_canonical_state_files' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/hierarchical_runtime.py | Function | can_spawn_subagent | 76 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'can_spawn_subagent' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/hierarchical_runtime.py | Function | check_resource_drain_mode | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'check_resource_drain_mode'. |
| skills/workflow-runtime/scripts/hierarchical_runtime.py | Function | start_daemon_loop | 67 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'start_daemon_loop' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/hierarchical_runtime.py | Class | HierarchicalRuntime | 646 | 300 | FAIL | Tách lớp 'HierarchicalRuntime' thành các lớp con chuyên trách (SRP). |
| skills/workflow-runtime/scripts/session.py | File | skills/workflow-runtime/scripts/session.py | 794 | 500 | FAIL | Split file into smaller module files (e.g. sessionCore, sessionHelper). |
| skills/workflow-runtime/scripts/session.py | Function | get_default_authorization_state | 53 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'get_default_authorization_state'. |
| skills/workflow-runtime/scripts/session.py | Function | migrate_session_schema | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'migrate_session_schema'. |
| skills/workflow-runtime/scripts/session.py | Function | load_session | 58 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'load_session'. |
| skills/workflow-runtime/scripts/session.py | Function | save_session_atomic | 47 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'save_session_atomic'. |
| skills/workflow-runtime/scripts/session.py | Function | load_guardrails_summary | 51 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'load_guardrails_summary'. |
| skills/workflow-runtime/scripts/session.py | Function | validate_runtime_policy | 58 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'validate_runtime_policy'. |
| skills/workflow-runtime/scripts/event_reducer.py | File | skills/workflow-runtime/scripts/event_reducer.py | 404 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| skills/workflow-runtime/scripts/event_reducer.py | Class | EventReducer | 380 | 300 | FAIL | Tách lớp 'EventReducer' thành các lớp con chuyên trách (SRP). |
| skills/workflow-runtime/scripts/event_reducer.py | ClassMethods | EventReducer | 30 | 20 | FAIL | Lớp 'EventReducer' chứa quá nhiều phương thức. Gom nhóm phương thức sang các lớp helper. |
| skills/workflow-runtime/scripts/adaptive_scheduler.py | File | skills/workflow-runtime/scripts/adaptive_scheduler.py | 422 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| skills/workflow-runtime/scripts/adaptive_scheduler.py | Function | plan_team_and_graph | 66 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'plan_team_and_graph' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/adaptive_scheduler.py | Function | execute_task | 90 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'execute_task' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/adaptive_scheduler.py | Function | execute_graph | 54 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'execute_graph'. |
| skills/workflow-runtime/scripts/release_manager.py | Function | run_release_execute | 111 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_release_execute' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/reconciliation_engine.py | Function | sync | 181 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'sync' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/context.py | File | skills/workflow-runtime/scripts/context.py | 557 | 500 | FAIL | Split file into smaller module files (e.g. contextCore, contextHelper). |
| skills/workflow-runtime/scripts/context.py | Function | parse_transcript | 106 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'parse_transcript' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/context.py | Function | sync_request_history | 323 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'sync_request_history' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/event_logger.py | Function | emit | 46 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'emit'. |
| skills/workflow-runtime/scripts/utils.py | Function | prompt_select | 91 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'prompt_select' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/orchestrator.py | Function | run_phase | 67 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_phase' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/orchestrator.py | Function | run_task | 59 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'run_task'. |
| skills/workflow-runtime/scripts/workflow_state.py | Function | resume_session | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'resume_session'. |
| skills/workflow-runtime/scripts/budget_controller.py | Function | init_budget_tables | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'init_budget_tables'. |
| skills/workflow-runtime/scripts/budget_controller.py | Function | evaluate_budget | 57 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'evaluate_budget'. |
| skills/workflow-runtime/scripts/dependency_resolver.py | File | skills/workflow-runtime/scripts/dependency_resolver.py | 929 | 500 | FAIL | Split file into smaller module files (e.g. dependency_resolverCore, dependency_resolverHelper). |
| skills/workflow-runtime/scripts/dependency_resolver.py | Function | parse_requirements | 51 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'parse_requirements'. |
| skills/workflow-runtime/scripts/dependency_resolver.py | Function | validate_requirements | 76 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate_requirements' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/dependency_resolver.py | Function | resolve_requirements | 71 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'resolve_requirements' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/dependency_resolver.py | Function | get_doctor_report | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'get_doctor_report'. |
| skills/workflow-runtime/scripts/task_orchestrator.py | File | skills/workflow-runtime/scripts/task_orchestrator.py | 681 | 500 | FAIL | Split file into smaller module files (e.g. task_orchestratorCore, task_orchestratorHelper). |
| skills/workflow-runtime/scripts/task_orchestrator.py | Function | build_task_graph | 103 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'build_task_graph' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/task_orchestrator.py | Function | transition_task_state | 85 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'transition_task_state' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/task_orchestrator.py | Function | get_next_ready_task | 93 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'get_next_ready_task' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/task_orchestrator.py | Function | validate_phase_completion | 95 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate_phase_completion' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/init_wizard.py | Function | generate_scaffold | 66 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'generate_scaffold' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/init_wizard.py | Function | run_interactive | 61 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_interactive' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/forecaster.py | Function | make_forecast | 72 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'make_forecast' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/skill_classifier.py | Function | classify_intent | 128 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'classify_intent' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/optimizer.py | Function | init_optimizer_tables | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'init_optimizer_tables'. |
| skills/workflow-runtime/scripts/architecture_validator.py | Function | run_architecture_validation | 141 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_architecture_validation' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/architecture_validator.py | Function | generate_architecture_report | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'generate_architecture_report'. |
| skills/workflow-runtime/scripts/validation_runner.py | Function | run_pipeline | 83 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_pipeline' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/validation_runner.py | Function | run_verify | 80 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_verify' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/lease.py | Function | inspect | 59 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'inspect'. |
| skills/workflow-runtime/scripts/lease.py | Function | acquire | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'acquire'. |
| skills/workflow-runtime/scripts/isolation_rules.py | Function | process_incoming_prompt | 90 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'process_incoming_prompt' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/safe_multi_agent_writes.py | File | skills/workflow-runtime/scripts/safe_multi_agent_writes.py | 604 | 500 | FAIL | Split file into smaller module files (e.g. safe_multi_agent_writesCore, safe_multi_agent_writesHelper). |
| skills/workflow-runtime/scripts/safe_multi_agent_writes.py | Function | plan_team | 94 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'plan_team' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/safe_multi_agent_writes.py | Function | acquire_lease | 70 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'acquire_lease' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/safe_multi_agent_writes.py | Function | validate_write | 62 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate_write' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/safe_multi_agent_writes.py | Function | integrate_next | 120 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'integrate_next' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/breakdown_engine.py | Function | generate_breakdown | 279 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'generate_breakdown' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/insights_engine.py | Function | generate_recommendations | 100 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'generate_recommendations' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/phase_controller.py | Function | on_phase_completed | 52 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'on_phase_completed'. |
| skills/workflow-runtime/scripts/release_gate.py | Function | validate | 89 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/release_gate.py | Function | create_partial_release_note | 53 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'create_partial_release_note'. |
| skills/workflow-runtime/scripts/release_gate.py | Class | ReleaseGate | 327 | 300 | FAIL | Tách lớp 'ReleaseGate' thành các lớp con chuyên trách (SRP). |
| skills/workflow-runtime/scripts/agent_routing.py | Function | validate_routing | 90 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate_routing' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/benchmark_init_flow.py | File | skills/workflow-runtime/scripts/benchmark_init_flow.py | 614 | 500 | FAIL | Split file into smaller module files (e.g. benchmark_init_flowCore, benchmark_init_flowHelper). |
| skills/workflow-runtime/scripts/benchmark_init_flow.py | Function | setup_workspace | 76 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'setup_workspace' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/benchmark_init_flow.py | Function | run_old_init | 121 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_old_init' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/benchmark_init_flow.py | Function | run_new_init | 102 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_new_init' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/benchmark_init_flow.py | Function | run_benchmark | 59 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'run_benchmark'. |
| skills/workflow-runtime/scripts/benchmark_init_flow.py | Function | print_report | 90 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'print_report' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | File | skills/workflow-runtime/scripts/workflow_runtime.py | 5074 | 500 | FAIL | Split file into smaller module files (e.g. workflow_runtimeCore, workflow_runtimeHelper). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | requires_approval | 54 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'requires_approval'. |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | update_context_health | 157 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'update_context_health' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | ensure_daemon_running | 54 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'ensure_daemon_running'. |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_init | 283 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_init' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_usage | 671 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_usage' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_suggest | 127 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_suggest' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_choice | 263 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_choice' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_active_workflow | 180 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_active_workflow' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_permission | 159 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_permission' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_compact | 98 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_compact' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | sync_execution_state_to_session | 52 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'sync_execution_state_to_session'. |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_task | 75 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_task' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_lock | 78 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_lock' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_execution | 62 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_execution' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_analysis_agent | 75 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_analysis_agent' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_orchestrator | 301 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_orchestrator' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_state_action | 96 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_state_action' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_knowledge_action | 57 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'do_knowledge_action'. |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_test_action | 216 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_test_action' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_provider_action | 320 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_provider_action' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_registry | 51 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'do_registry'. |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_update | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'do_update'. |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_deps | 171 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_deps' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_task_orchestrator | 102 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'do_task_orchestrator' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | do_runtime_action | 52 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'do_runtime_action'. |
| skills/workflow-runtime/scripts/workflow_runtime.py | Function | main | 573 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'main' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/dag_planner.py | Function | build | 61 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'build' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/dag_planner.py | Function | topological_sort | 47 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'topological_sort'. |
| skills/workflow-runtime/scripts/dag_planner.py | Function | check_parallel_safety | 46 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'check_parallel_safety'. |
| skills/workflow-runtime/scripts/state_sync.py | Function | aggregate_state | 142 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'aggregate_state' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/state_sync.py | Function | deconstruct_state | 88 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'deconstruct_state' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/state_sync.py | Function | write_initialization_summary | 52 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'write_initialization_summary'. |
| skills/workflow-runtime/scripts/state_sync.py | Function | validate_no_heavy_init_operations | 48 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'validate_no_heavy_init_operations'. |
| skills/workflow-runtime/scripts/cost_engine.py | Function | calculate | 110 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'calculate' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/context_rebuilder.py | Function | build_context_bundle | 57 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'build_context_bundle'. |
| skills/workflow-runtime/scripts/tia_engine.py | Function | validate_test_architecture | 76 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'validate_test_architecture' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/tia_engine.py | Function | resolve_affected_tests | 47 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'resolve_affected_tests'. |
| skills/workflow-runtime/scripts/analytics_engine.py | Function | detect_duplicate_reads | 64 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'detect_duplicate_reads' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/analytics_engine.py | Function | update_analytics | 88 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'update_analytics' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/connectors/__init__.py | Function | build_default_registry | 47 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'build_default_registry'. |
| skills/workflow-runtime/scripts/connectors/vscode_agents.py | Function | parse_with_fingerprint | 64 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'parse_with_fingerprint' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/connectors/antigravity.py | File | skills/workflow-runtime/scripts/connectors/antigravity.py | 421 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| skills/workflow-runtime/scripts/connectors/antigravity.py | Function | parse_with_fingerprint | 127 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'parse_with_fingerprint' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/connectors/antigravity.py | Function | _parse_step | 61 | 60 | FAIL | Trích xuất mã nguồn trong hàm '_parse_step' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/connectors/antigravity.py | Class | AntigravityConnector | 392 | 300 | FAIL | Tách lớp 'AntigravityConnector' thành các lớp con chuyên trách (SRP). |
| skills/workflow-runtime/scripts/connectors/claude_code.py | Function | parse_with_fingerprint | 73 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'parse_with_fingerprint' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/connectors/cursor.py | Function | parse_with_fingerprint | 64 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'parse_with_fingerprint' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/memory/update.py | Function | parse_new_lessons | 63 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'parse_new_lessons' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/memory/update.py | Function | run_update | 161 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_update' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/memory/bootstrap.py | Function | run_bootstrap | 103 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'run_bootstrap' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/memory/markdown_writer.py | Function | generate_project_summary | 76 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'generate_project_summary' thành các hàm con (helper functions). |
| skills/workflow-runtime/scripts/memory/search.py | Function | vector_search | 51 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'vector_search'. |
| skills/skill-self-verification/scripts/verify_skill.py | File | skills/skill-self-verification/scripts/verify_skill.py | 419 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| skills/skill-self-verification/scripts/verify_skill.py | Function | main | 57 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'main'. |
| skills/skill-self-verification/scripts/verify_skill.py | Function | report | 109 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'report' thành các hàm con (helper functions). |
| skills/skill-self-verification/scripts/verify_skill.py | Class | SkillVerifier | 322 | 300 | FAIL | Tách lớp 'SkillVerifier' thành các lớp con chuyên trách (SRP). |
| skills/vir-runtime/scripts/vir_runtime/multi_agent/consensus.py | Function | collect_votes | 59 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'collect_votes'. |
| skills/vir-runtime/scripts/vir_runtime/sensory/vision/pixel_comparer.py | Function | compare | 58 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'compare'. |
| skills/frontend-design/scripts/ux_audit.py | File | skills/frontend-design/scripts/ux_audit.py | 722 | 500 | FAIL | Split file into smaller module files (e.g. ux_auditCore, ux_auditHelper). |
| skills/frontend-design/scripts/ux_audit.py | Function | audit_file | 568 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'audit_file' thành các hàm con (helper functions). |
| skills/frontend-design/scripts/ux_audit.py | Class | UXAuditor | 592 | 300 | FAIL | Tách lớp 'UXAuditor' thành các lớp con chuyên trách (SRP). |
| skills/frontend-design/scripts/accessibility_checker.py | Function | check_accessibility | 65 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'check_accessibility' thành các hàm con (helper functions). |
| skills/frontend-design/scripts/accessibility_checker.py | Function | main | 69 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'main' thành các hàm con (helper functions). |
| skills/knowledge-runtime/tests/integration/test_provider_manager.py | File | skills/knowledge-runtime/tests/integration/test_provider_manager.py | 409 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| skills/knowledge-runtime/tests/integration/test_provider_manager.py | Class | TestProviderManager | 391 | 300 | FAIL | Tách lớp 'TestProviderManager' thành các lớp con chuyên trách (SRP). |
| skills/knowledge-runtime/scripts/obsidian_resolver.py | Function | extract_section | 47 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'extract_section'. |
| skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py | File | skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py | 712 | 500 | FAIL | Split file into smaller module files (e.g. provider_managerCore, provider_managerHelper). |
| skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py | Function | test_provider | 55 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'test_provider'. |
| skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py | Function | resolve_obsidian_project_folder | 182 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'resolve_obsidian_project_folder' thành các hàm con (helper functions). |
| skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py | Function | sync_obsidian | 215 | 60 | FAIL | Trích xuất mã nguồn trong hàm 'sync_obsidian' thành các hàm con (helper functions). |

## 3. Code Metric Dashboards
### Largest Files
| File | Lines |
| :--- | :---: |
| skills/workflow-runtime/scripts/workflow_runtime.py | 5074 |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | 4952 |
| skills/workflow-runtime/scripts/db.py | 1621 |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | 1414 |
| public_export/skills/workflow-runtime/scripts/db.py | 1324 |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | 1251 |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | 1153 |
| skills/workflow-runtime/tests/integration/test_runtime.py | 1153 |
| public_export/skills/workflow-runtime/scripts/dependency_resolver.py | 929 |
| skills/workflow-runtime/scripts/dependency_resolver.py | 929 |

### Largest Functions
| File | Function Name | Lines |
| :--- | :--- | :---: |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | do_usage | 671 |
| skills/workflow-runtime/scripts/workflow_runtime.py | do_usage | 671 |
| skills/workflow-runtime/scripts/workflow_runtime.py | main | 573 |
| public_export/skills/frontend-design/scripts/ux_audit.py | audit_file | 568 |
| skills/frontend-design/scripts/ux_audit.py | audit_file | 568 |
| public_export/skills/workflow-runtime/scripts/workflow_runtime.py | main | 563 |
| scratch/initialize.py | main | 450 |
| skills/workflow-runtime/scripts/db.py | init_db_schema | 439 |
| public_export/skills/workflow-runtime/scripts/autonomous_orchestrator.py | run_autonomous_delivery | 421 |
| skills/workflow-runtime/scripts/autonomous_orchestrator.py | run_autonomous_delivery | 421 |

### Largest Classes
| File | Class Name | Lines | Methods |
| :--- | :--- | :---: | :---: |
| public_export/skills/workflow-runtime/tests/integration/test_runtime.py | TestRuntimeEngine | 1122 | 22 |
| skills/workflow-runtime/tests/integration/test_runtime.py | TestRuntimeEngine | 1122 | 22 |
| skills/workflow-runtime/scripts/hierarchical_runtime.py | HierarchicalRuntime | 646 | 19 |
| public_export/skills/frontend-design/scripts/ux_audit.py | UXAuditor | 592 | 4 |
| skills/frontend-design/scripts/ux_audit.py | UXAuditor | 592 | 4 |
| public_export/skills/workflow-runtime/scripts/hierarchical_runtime.py | HierarchicalRuntime | 577 | 18 |
| public_export/skills/workflow-runtime/scripts/test_coordinator.py | TestCoordinator | 501 | 10 |
| skills/workflow-runtime/scripts/test_coordinator.py | TestCoordinator | 501 | 10 |
| skills/workflow-runtime/scripts/connectors/antigravity.py | AntigravityConnector | 392 | 13 |
| public_export/skills/knowledge-runtime/tests/integration/test_provider_manager.py | TestProviderManager | 391 | 17 |
