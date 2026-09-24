"""AIWF Loop Controller deterministic engine.

Turn-driven, no daemon, no server, no background process. Every step is a
single deterministic invocation that reads and writes files under
`.agents/state/loop/`. The host agent drives the loop one turn at a time.

Public contract (mirrors PROTOCOL.md exactly):
    loop_engine load    --workflow <id>
    loop_engine decide  --workflow <id> --verdict <PASS|BLOCK|FAIL|ERROR> ...
    loop_engine persist --workflow <id> --state <json>

The engine is agent-agnostic. Business logic lives here; per-agent adapters
only map "call the engine / read-write state".
"""

from loop_engine.domain.models import (
    LoopState,
    Transition,
    Verdict,
    StopCondition,
)

__all__ = ["LoopState", "Transition", "Verdict", "StopCondition"]
__version__ = "1.0.0"
