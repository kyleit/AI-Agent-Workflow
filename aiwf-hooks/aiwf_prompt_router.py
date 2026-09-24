#!/usr/bin/env python3
"""Claude Code UserPromptSubmit hook — AIWF auto-route injector.

Reads the Claude hook JSON payload from stdin and, for a normal natural-language
prompt, injects context instructing the agent to route the request through the
AIWF workflow (initialize-workflow -> workflow-coordinator) exactly as if the
user had typed `/aiwf <request>`. This lets users omit the `/aiwf` prefix.

It stays silent (adds no context) when there is nothing to route:
  - empty prompt
  - an explicit slash command (starts with "/") — the user chose a command
  - the prompt already begins with "aiwf" / "@aiwf" / "/aiwf"

Never blocks: any error results in exit 0 with no output.
"""

from __future__ import annotations

import json
import sys

_CONTEXT = (
    "AIWF Workflow-Coordinator-First is ACTIVE for this project. Treat this "
    "request as `/aiwf <request>`: first run the initialize-workflow skill to "
    "obtain a valid Bootstrap Receipt, then workflow-coordinator to classify "
    "intent and dispatch to the correct specialist skill (quick-fix, "
    "quick-feature, brainstorming, plan-to-blueprint, blueprint-to-implementation, "
    "debug, verify, git/release governance) and drive the loop-controller. Do "
    "NOT create, modify, or delete source code until a Technical Design "
    "Blueprint exists under docs/features/ AND is explicitly approved. Pure "
    "read-only questions, or an explicit slash command, need no workflow."
)


def _should_route(prompt: str) -> bool:
    stripped = prompt.strip()
    if not stripped:
        return False
    lowered = stripped.lower()
    if stripped.startswith("/"):
        return False
    if lowered.startswith(("aiwf", "@aiwf")):
        return False
    return True


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not _should_route(prompt):
        return 0
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": _CONTEXT,
        }
    }
    sys.stdout.write(json.dumps(output))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(0)
