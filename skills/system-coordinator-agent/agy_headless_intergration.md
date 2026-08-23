# AGY Headless CLI — Integration Reference

> **Purpose**: This document is the authoritative reference for any AI agent or developer who needs to invoke `agy` (Antigravity IDE CLI) in headless (non-interactive) mode from an external process.
> **Last updated**: 2026-07-23 — reflects confirmed Ba's directives (ADR-005)

---

## 🧠 What is AGY?

`agy` is the **Antigravity IDE CLI worker agent**. It receives a prompt, thinks, uses tools (reads/writes files, runs terminal commands), and prints the result to stdout before exiting.

> ⚠️ **AGY ≠ Antigravity (reviewer/coordinator)**
> - **AGY** = worker agent that *produces* artifacts (Spec, Blueprint, code, reports)
> - **Antigravity** (the IDE) = reviewer/coordinator that *independently audits* AGY's output

---

## 📍 Installation Paths

| OS | Default Path |
|---|---|
| **macOS** | `~/.local/bin/agy` |
| **Windows** | `%USERPROFILE%\AppData\Local\agy\bin\agy.exe` |

Add the binary directory to your system `PATH` so you can call `agy` directly.

---

## ✅ Canonical Command (Ba's Confirmed Standard — ADR-005)

For all headless invocations in this project, use **exactly** this structure:

```bash
# macOS / Linux — run from inside the project directory
agy \
  --model gemini-3.6-flash-high \
  --effort high \
  --dangerously-skip-permissions \
  --add-dir "$(git rev-parse --show-toplevel)" \
  --print-timeout 10m \
  --print "<your prompt here>"
```

```powershell
# Windows PowerShell — run from inside the project directory
$projectRoot = (git rev-parse --show-toplevel)
agy `
  --model gemini-3.6-flash-high `
  --effort high `
  --dangerously-skip-permissions `
  --add-dir "$projectRoot" `
  --print-timeout 10m `
  --print "<your prompt here>"
```

> `git rev-parse --show-toplevel` automatically resolves the project root on any machine — no hardcoded paths.

### Why each flag is mandatory

| Flag | Value | Why |
|---|---|---|
| `--model` | `gemini-3.6-flash-high` | Ba's confirmed model (ADR-005, 2026-07-23). Do NOT substitute. |
| `--effort` | `high` | Activates deep thinking / extended reasoning mode. Use `low` or `medium` only for trivial tasks. |
| `--dangerously-skip-permissions` | _(flag)_ | **Required for headless.** Without it, AGY hangs forever waiting for TTY stdin (deadlock). |
| `--add-dir` | `$(git rev-parse --show-toplevel)` | Scopes AGY's file access to the project root. Always resolve dynamically — **never hardcode a local machine path.** |
| `--print-timeout` | `10m` | Minimum timeout for complex document/planning tasks. Increase to `20m` for very large tasks. |
| `--print` | `"<prompt>"` | Activates non-interactive mode: run once, print result, exit. |

---

## 🚫 Common Mistakes — Never Do These

| ❌ Wrong | ✅ Correct |
|---|---|
| Omit `--dangerously-skip-permissions` | Always include it |
| Use `--effort` on old AGY versions | Current version supports it. Use `--effort high` |
| Hardcode `--add-dir /some/local/path` | Always resolve with `$(git rev-parse --show-toplevel)` |
| Set `--print-timeout 1m` | Use at least `10m` for planning/blueprint tasks |
| Trust AGY's self-assessment of its own output | Antigravity must independently review every artifact |

---

## 🔄 AGY Role in the AIWF Workflow

```
Planning Phase (Document Loop):
  ┌─────────────────────────────────────────────────────────┐
  │ AGY (worker) writes artifact                            │
  │   → brainstorming → brainstorming-to-plan → blueprint   │
  └────────────────────┬────────────────────────────────────┘
                       │
                       ▼
  ┌─────────────────────────────────────────────────────────┐
  │ Antigravity reviews INDEPENDENTLY                       │
  │   → runs document-compliance-assessment                  │
  │   → score must be >= 95/100                              │
  └────────────────────┬────────────────────────────────────┘
                       │
              ┌────────┴────────┐
              │                 │
           FAIL               PASS
              │                 │
              ▼                 ▼
        Fix specific      Next phase
        failed points     (Blueprint → Implementation)
        Re-review
```

> If AGY is **not installed** on the machine → use a **subagent Planner** to write the artifact instead. The review loop is identical.

---

## 💻 Integration Examples

### Python

```python
import subprocess
import os

def get_project_root() -> str:
    """Resolve the project root dynamically (works on any machine)."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()

def run_agy(prompt: str, timeout_seconds: int = 600) -> dict:
    """
    Runs AGY in headless mode with deep thinking enabled.
    Returns: {"success": bool, "stdout": str, "stderr": str, "exit_code": int}
    """
    cmd = [
        "agy",
        "--model", "gemini-3.6-flash-high",
        "--effort", "high",
        "--dangerously-skip-permissions",
        "--add-dir", get_project_root(),  # resolved dynamically
        "--print-timeout", "10m",
        "--print", prompt,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_seconds,
            check=True,
        )
        return {"success": True, "stdout": result.stdout, "stderr": result.stderr, "exit_code": 0}
    except subprocess.TimeoutExpired as e:
        return {"success": False, "error": "TIMEOUT", "stdout": e.stdout or "", "stderr": e.stderr or ""}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": "EXEC_ERROR", "stdout": e.stdout, "stderr": e.stderr, "exit_code": e.returncode}

# Usage
if __name__ == "__main__":
    result = run_agy("Write a mini spec for feature X following AIWF standards.")
    if result["success"]:
        print(result["stdout"])
    else:
        print(f"Error: {result['error']}\n{result['stderr']}")
```

### Node.js

```javascript
const { execFile, execFileSync } = require('child_process');

// Resolve project root dynamically (works on any machine)
const projectRoot = execFileSync('git', ['rev-parse', '--show-toplevel'], { encoding: 'utf-8' }).trim();

function runAgy(prompt, callback) {
    const args = [
        '--model', 'gemini-3.6-flash-high',
        '--effort', 'high',
        '--dangerously-skip-permissions',
        '--add-dir', projectRoot,  // resolved dynamically
        '--print-timeout', '10m',
        '--print', prompt,
    ];
    execFile('agy', args, { encoding: 'utf-8', timeout: 600000 }, (error, stdout, stderr) => {
        if (error) return callback(error, null);
        callback(null, stdout);
    });
}

// Usage
runAgy('Write a mini spec for feature X.', (err, output) => {
    if (err) console.error('AGY error:', err.message);
    else console.log(output);
});
```

### PowerShell

```powershell
# Resolve project root dynamically (works on any machine)
$projectRoot = (git rev-parse --show-toplevel).Trim()

$prompt = "Write a mini spec for feature X following AIWF standards."

$process = Start-Process -FilePath "agy" `
    -ArgumentList "--model", "gemini-3.6-flash-high", "--effort", "high", `
                  "--dangerously-skip-permissions", `
                  "--add-dir", "$projectRoot", `
                  "--print-timeout", "10m", `
                  "--print", "`"$prompt`"" `
    -NoNewWindow -PassThru `
    -RedirectStandardOutput "agy_stdout.txt" `
    -RedirectStandardError "agy_stderr.txt"

$process.WaitForExit()

if ($process.ExitCode -eq 0) {
    Get-Content "agy_stdout.txt"
} else {
    Write-Error (Get-Content "agy_stderr.txt")
}
```

---

## 🛠️ Useful Subcommands

```bash
# List available agents (Planner, Coder, Architect, etc.)
agy --dangerously-skip-permissions agents

# List supported models
agy --dangerously-skip-permissions models

# Show local changelog
agy changelog
```

---

## 📊 --effort Flag Values

| Value | When to use |
|---|---|
| `low` | Simple, quick tasks (summarize, format, rename) |
| `medium` | Standard implementation tasks |
| `high` | Complex planning, deep architecture decisions, blueprint writing, multi-step reasoning |

> For all AIWF planning and blueprint tasks, always use `--effort high`.

---

## ⚠️ Troubleshooting

| Symptom | Root Cause | Fix |
|---|---|---|
| Process hangs / no output | Missing `--dangerously-skip-permissions` | Add the flag |
| Permission error on Windows Service | Service account lacks access to project dir or `~/.gemini/` | Grant read/write permissions |
| Exit code `1` | Syntax error, API error, or permissions error | Check `stderr` output |
| Exit code `0` but empty output | Prompt was too short or ambiguous | Make the prompt more specific and detailed |
| Timeout error | Task too complex for default timeout | Increase `--print-timeout` to `20m` or `30m` |

**Exit Codes:**
- `0` = Success
- `1+` = Error (check stderr for details)

---

## 🔒 Security Rules

1. **Never log or commit secrets**: API keys, tokens, passwords, cookies must never appear in AGY prompts or logged output.
2. **Never use `--add-dir` outside project root**: Only grant AGY access to the intended workspace directory.
3. **Review before trusting**: Antigravity (the coordinator) MUST independently review every artifact AGY produces. Never auto-approve AGY's self-assessed PASS.

---

## 🤖 Multi-Agent 5-Role CLI Topology

When executing a coordinated AIWF task, you **MUST spawn 5 separate, sequential AGY CLI invocations**, each acting as a distinct operational role with its own isolated context.

> ⚠️ **Do NOT use a single AGY call to perform all roles.** Each invocation is stateless and does not share memory with any other. Outputs must be passed between roles explicitly via file paths written into the next agent's `--print` prompt.

---

### Role → CLI Responsibility Mapping

| # | Role | Responsibility | Scope |
|---|---|---|---|
| 1 | **Planner** | Writes Spec / Roadmap / Mini Spec from user requirements | Creates artifacts only — no code changes |
| 2 | **Architect** | Writes Technical Blueprint from the approved Spec | Creates blueprint — no code changes |
| 3 | **Coder** | Implements source code strictly within the approved Blueprint scope | Edits source files — no artifacts, no review |
| 4 | **Auditor** | Independently audits code quality, tests, and blueprint adherence | **Read-only** — must NOT modify code or artifacts |
| 5 | **Manager** | Final gate: validates functional completion, risk, integration readiness | **Read-only** — must NOT modify code or artifacts |

---

### Execution Order & File Hand-off

```
[1] PLANNER invocation
    agy --print "You are the Planner agent. ..."
        └─→ Output: docs/features/<family>/specs/QUICK-XXX_spec.md

[2] ARCHITECT invocation
    agy --print "You are the Architect agent. Read the spec at docs/features/<family>/specs/QUICK-XXX_spec.md ..."
        └─→ Output: docs/features/<family>/blueprints/QUICK-XXX_blueprint.md

    ════════ STOP: User Blueprint Approval Gate ════════
    Preferred: native Agent/IDE ask_question with Continue|Cancel.
    Fallback bridge only:
    aiwf prompt select --question "Approve this Technical Design Blueprint for implementation?" \
                       --options "Continue|Cancel" --default "Cancel"
    ════════════════════════════════════════════════════

[3] CODER invocation   (only after explicit approval evidence exists)
    agy --print "You are the Coder agent. Read the approved blueprint at docs/features/<family>/blueprints/QUICK-XXX_blueprint.md ..."
        └─→ Output: source code changes committed to workspace

[4] AUDITOR invocation   (independent — reads Coder output, does NOT consult Coder)
    agy --print "You are the Auditor agent. Read the blueprint at ... and the git diff. ..."
        └─→ Output: Auditor: PASS | FAIL + findings report

[5] MANAGER invocation   (independent — reads Auditor report, does NOT consult Coder or Auditor)
    agy --print "You are the Manager agent. Read the Auditor report at ... ..."
        └─→ Output: Manager: PASS | FAIL + delivery decision
```

---

### System Prompt Templates (copy and fill in for each role)

#### 1. Planner Agent
```
You are the Planner agent in an AIWF multi-agent workflow.

YOUR ONLY JOB: Write a Mini Spec / Roadmap for the following user request.
- Read project rules from `.agents/AGENTS.md` and `.agents/AI_RULES.md` before starting.
- Use Memory First: read `.agents/memory/` before scanning source code.
- Save output to: docs/features/<feature-family>/specs/<WORK-ITEM-ID>_spec.md
- Do NOT write code. Do NOT run tests. Do NOT modify any source file.
- Your artifact MUST contain an `Internal Review Evidence` section scoring >= 95/100.

User request: <INSERT REQUEST HERE>
```

#### 2. Architect Agent
```
You are the Architect agent in an AIWF multi-agent workflow.

YOUR ONLY JOB: Write a Technical Design Blueprint from the approved Spec.
- Read the Spec at: <SPEC_PATH>
- Read project rules from `.agents/AGENTS.md` and `.agents/AI_RULES.md`.
- Save output to: docs/features/<feature-family>/blueprints/<WORK-ITEM-ID>_blueprint.md
- The Blueprint MUST contain zero placeholders (no TBD, TODO, etc.). Any placeholder = FAIL.
- The Blueprint MUST contain: File-by-File Change Matrix, API Signatures, Data Schemas, Test Strategy, Risk Analysis, Acceptance Criteria.
- Do NOT write code. Do NOT run tests. Do NOT modify any source file.
- Your artifact MUST contain an `Internal Review Evidence` section scoring >= 95/100.
```

#### 3. Coder Agent
```
You are the Coder agent in an AIWF multi-agent workflow.

YOUR ONLY JOB: Implement the approved Technical Blueprint — nothing more, nothing less.
- Read the approved Blueprint at: <BLUEPRINT_PATH>
- Read project rules from `.agents/AGENTS.md` and `.agents/AI_RULES.md`.
- Implement ONLY what is explicitly specified in the Blueprint File-by-File Change Matrix.
- Do NOT create new features beyond Blueprint scope.
- Do NOT modify documentation or artifacts.
- After implementation, run the Code → Build → Test loop until ZERO errors remain.
- Write test log to: .agents/runtime/tests.log
```

#### 4. Auditor Agent
```
You are the Auditor agent in an AIWF multi-agent workflow.

YOUR ONLY JOB: Conduct an independent, zero-trust audit of the Coder's output.
- Read the approved Blueprint at: <BLUEPRINT_PATH>
- Read the git diff (run: git diff HEAD~1) to see exactly what the Coder changed.
- Read the test log at: .agents/runtime/tests.log
- DO NOT trust the Coder's self-assessment. Verify everything independently.
- DO NOT modify any source file or artifact.
- Check: (1) code matches Blueprint scope, (2) no linter errors, (3) all tests pass, (4) no absolute paths, (5) no secrets leaked.
- Output a report with explicit verdict: `Auditor: PASS` or `Auditor: FAIL` + exact findings list.
```

#### 5. Manager Agent
```
You are the Manager agent in an AIWF multi-agent workflow.

YOUR ONLY JOB: Make the final delivery decision based on independent validation.
- Read the approved Blueprint at: <BLUEPRINT_PATH>
- Read the Auditor report at: <AUDITOR_REPORT_PATH>
- DO NOT trust the Coder's or Auditor's combined assessment without independent verification.
- DO NOT modify any source file or artifact.
- Verify: (1) all Acceptance Criteria from Blueprint are met, (2) Auditor PASS exists, (3) no open blockers or unresolved risks, (4) integration readiness is confirmed.
- Output a report with explicit verdict: `Manager: PASS` or `Manager: FAIL` + delivery recommendation.
- A phase may only be marked complete when BOTH `Auditor: PASS` AND `Manager: PASS` exist as separate entries.
```

---

### Critical Rules for Multi-Agent Execution

1. **Isolation is mandatory**: Each AGY invocation is a fresh, stateless process. Never assume one agent "remembers" the previous one.
2. **Explicit file hand-off**: Always write the output file path into the next agent's `--print` prompt so it can read the previous agent's work.
3. **No rubber-stamping**: The Auditor and Manager prompts explicitly forbid trusting the previous agent. Include this constraint in every prompt.
4. **Blueprint Approval is a hard gate**: Never invoke the Coder agent until the user has explicitly approved the Blueprint via native Agent/IDE `ask_question` or the `aiwf prompt select` fallback bridge returning `Continue`. A chat "yes" is not valid approval.
5. **Scope enforcement**: Explicitly state in each prompt what the agent MUST NOT do (e.g., "Do NOT modify source files" for Auditor/Manager).
