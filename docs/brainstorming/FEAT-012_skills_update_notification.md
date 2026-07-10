# Brainstorming: Skills Auto-Update Notification (FEAT-012)

## Problem Statement
While the VSCode extension can notify users of updates through the VSCode Marketplace automatically, the **AI Skills and CLI templates** (which live inside the `.agents/` folder of the user's workspace) do not have any update notification mechanism. When a developer releases a new version of the skills (e.g. adding database synchronization, fixing token estimation, etc.), end-users have no way of knowing a newer, bug-free version is available.

---

## Proposed Options

### Option 1: VSCode Extension Background Checker (Recommended)
The VSCode extension checks for updates asynchronously when the Visualizer panel mounts or once every 24 hours.

#### Flow
1. The extension reads the current version from `.agents/MANIFEST.json`.
2. The extension performs an asynchronous HTTP GET request to the raw stable channel metadata:
   - URL: `https://raw.githubusercontent.com/kyleit/AI-Agent-Workflow/main/MANIFEST.json`
3. If `remote_version > local_version`:
   - It displays a sleek sticky warning banner at the top of the Webview Dashboard:
     `✨ AI Skill Framework update available: vX.Y.Z (Current: vA.B.C). [Update Now]`
   - Clicking `[Update Now]` runs `update.sh` (or `update.ps1`) in the VSCode integrated terminal automatically.
   - Alternatively, it displays a standard VSCode Toast notification.

#### Pros
- No performance impact on the AI Agent's command executions.
- Visual and interactive: User can click to update immediately.
- Cross-platform support (handled easily inside Node.js).

#### Cons
- Requires the user to have the VSCode Visualizer extension open/installed.

---

### Option 2: CLI-Based Check (With Local Caching)
The version check runs inside Python's `workflow_runtime.py init` or `validate` command.

#### Flow
1. When `init` runs, it compares the current timestamp with `last_update_check` stored in `.agents/project_runtime.db`.
2. If more than 24 hours have passed since the last check:
   - It makes a background request (or quick timeout-bounded request) to fetch the remote `MANIFEST.json`.
   - It updates the cache (`last_update_check` and `latest_available_version`).
3. If `latest_available_version > current_version`:
   - It prints a colored warning block in the terminal output:
     `[WARN] A new version of the AI Skill Framework (vX.Y.Z) is available! Run ./update.sh to update.`
   - It saves `update_available: "vX.Y.Z"` into `.session.json` so the extension can also read it.

#### Pros
- Works for users running purely from the CLI without VSCode.
- Guarantees visibility as it prints directly to the console where the agent/developer runs commands.

#### Cons
- Even with caching and small timeouts, network checks inside CLI commands can occasionally cause lag or hangs if the user is behind proxies/firewalls.

---

### Option 3: Joint Hybrid Approach
Combine **Option 1** and **Option 2** for maximum coverage:
1. VSCode extension performs the lightweight checking and displays it on the Dashboard UI.
2. CLI stores the version check cache in the SQLite database and prints warnings if a cached update is detected (never making direct blocking HTTP calls on critical paths).

---

## Next Steps
1. Select the preferred option (Option 1/Option 3 is recommended).
2. Transition to `brainstorming-to-plan` to design the network client utility and the visualizer UI banner components.
