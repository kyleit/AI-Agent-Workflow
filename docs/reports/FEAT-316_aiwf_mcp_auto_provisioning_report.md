# FEAT-316 AIWF MCP Auto Provisioning CLI Report

This report documents the architecture, supported IDEs, configuration strategy, and test validation results for the Model Context Protocol (MCP) auto-provisioning feature (**FEAT-316**).

---

## 1. Architecture

The auto-provisioning CLI component acts as a bridge between the core AIWF installation and the localized settings profile directories of various IDEs. Users do not need to copy and paste command configurations or script paths into IDE setup panels.

```text
       aiwf CLI (mcp subcommand)
                │
                ▼
           MCPManager ────> IDE Adapter Router
                                   │
               ┌───────────────────┼───────────────────┐
               ▼                   ▼                   ▼
      AntigravityAdapter     VSCodeAdapter       CursorAdapter
               │                   │                   │
               ▼                   ▼                   ▼
       ~/.gemini/...      ~/Library/...Code/  ~/Library/...Cursor/
         mcp.json           settings.json       settings.json
```

---

## 2. Supported IDEs & Paths

- **Antigravity IDE**:
  - Config path (All platforms): `~/.gemini/antigravity-ide/mcp.json`
- **VS Code** (Roo Cline):
  - Windows: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
  - macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
  - Linux: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- **Cursor** (Roo Cline):
  - Windows: `%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
  - macOS: `~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
  - Linux: `~/.config/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

---

## 3. Configuration & Security Merge Strategy

Auto-provisioning modifications enforce strict safety bounds:

1. **Backup before write**: Existing configurations are copied to `.agents/state/mcp/backup/{ide}_{timestamp}.json` before making changes.
2. **Merge strategy**: The configuration reads the JSON keys, updates the target `"aiwf"` block inside `"mcpServers"`, and preserves all other pre-existing custom servers.
3. **JSON Schema validation**: Written configurations are validated for syntax correctness using Pythons `json.loads` check prior to saving to disk to prevent corrupted configuration output.
4. **Non-destructive rollback**: If installation fails, users can restore configurations from the backup directory. Uninstall commands safely remove ONLY the `"aiwf"` entry.

---

## 4. CLI Usage

Run these commands globally (or via Python runner):

- **Install AIWF MCP servers**:
  ```bash
  aiwf mcp install antigravity
  ```
- **Inspect installation status**:
  ```bash
  aiwf mcp status antigravity
  ```
- **Execute diagnostics (doctor)**:
  ```bash
  aiwf mcp doctor antigravity
  ```
- **Uninstall AIWF MCP servers**:
  ```bash
  aiwf mcp uninstall antigravity
  ```

---

## 5. Setup Integration with initialize-workspace

During setup initialization (`initialize-workspace` step in `SessionBootstrapGuard`), the system will check the configuration status:
1. If the AIWF MCP server is not registered, it auto-provisions it on-the-fly.
2. The installation log is outputted to stderr, and setup continues smoothly without stopping the workflow.

---

## 6. Automated Testing Verification

We verified this implementation using two test suites:

- **`test_mcp_manager.py`**:
  - Mocked IDE configuration locations to point to isolated workspace folders.
  - Verified `doctor()` diagnostics checks and `status()` output states.
- **`test_mcp_antigravity_adapter.py`**:
  - Validated clean installations, automatic backup creation under `.agents/state/mcp/backup/`.
  - Confirmed merging preserves pre-existing user servers (e.g. `"custom_server"`).
  - Confirmed uninstallation removes the `"aiwf"` block cleanly.

### Running Test Verification:
```bash
pytest -v -s skills/workflow-runtime/tests/test_mcp_manager.py skills/workflow-runtime/tests/test_mcp_antigravity_adapter.py
```

Result:
```text
skills/workflow-runtime/tests/test_mcp_manager.py::test_mcp_manager_doctor PASSED
skills/workflow-runtime/tests/test_mcp_antigravity_adapter.py::test_antigravity_adapter_lifecycle PASSED
============================== 2 passed in 1.42s ===============================
```
