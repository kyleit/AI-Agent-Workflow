from __future__ import annotations

from typing import Any, Callable


class InfrastructureLocator:
    """Service locator for procedural functions to access infrastructure without importing it."""

    load_session: Callable[[], dict[str, Any]] = lambda: {}
    save_session_atomic: Callable[[dict[str, Any]], None] = lambda d: None
    OSFileLock: Any = None

    get_project_db_path: Callable[[], str] = lambda: ""
    connect_db: Callable[[str], Any] = lambda p: None
    init_db_schema: Callable[[], None] = lambda: None
    get_workflow_summary: Callable[[], dict[str, Any]] = lambda: {}

    is_process_alive: Callable[[int], bool] = lambda p: False

    SQLiteEventStore: Any = None
    ImplementationLedger: Any = None
    StateStoreAdapter: Any = None
    CapacityController: Any = None
    CDPClient: Any = None
    CDPSession: Any = None
    DOMInspector: Any = None
    ScreenshotCapturer: Any = None
    WorkerManager: Any = None
    PatchApplier: Any = None
    LockManager: Any = None
    AgyAdapter: Any = None
    TelegramDaemon: Any = None
    MemoryScanner: Any = None
    ProjectAnalyzer: Any = None
    RAGSearcher: Any = None
    RuntimeAPIServer: Any = None
    ERROR_CODES: dict[str, int] = {
        "SESSION_NOT_FOUND": 404,
        "PERMISSION_DENIED": 403,
        "INVALID_STATE_TRANSITION": 400,
        "TASK_CANCELLED": 409,
        "TOOL_EXECUTION_FAILED": 500,
    }


__all__ = ["InfrastructureLocator"]
