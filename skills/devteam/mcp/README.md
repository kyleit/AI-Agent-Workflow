# DevTeam MCP server

Wraps the DevTeam engine as six MCP tools: `init`, `seat_enter`, `seat_leave`,
`mailbox_send`, `mailbox_poll`, `board`. Delivery-only — no business logic; each
tool builds the composition root and calls a use case.

## Requirements
- The DevTeam engine on disk (repo `skills/devteam/scripts/` or installed at
  `~/.aiwf/devteam/engine`).
- `pip install mcp` (the engine itself needs no third-party dependency).

## Run
```bash
python skills/devteam/mcp/server.py         # repo source
python ~/.aiwf/devteam/mcp/server.py        # after install
```
The server locates the engine via `AIWF_DEVTEAM_ENGINE`, then `~/.aiwf/devteam/
engine`, then the repo `scripts/` dir.

## Register (HARD-GATED — owner approval required, §15)
Plans are produced by `infrastructure/install/config_writers.py`; a `.bak` is
taken and the write is refused unless the owner explicitly approves.

**Claude Code** — `.mcp.json`:
```json
{ "mcpServers": { "devteam": { "command": "python", "args": ["<path>/mcp/server.py"] } } }
```

**Codex CLI** — `~/.codex/config.toml`:
```toml
[mcp_servers.devteam]
command = "python"
args = ["<path>/mcp/server.py"]
```

**Antigravity** — IDE MCP settings:
```json
{ "mcpServers": { "devteam": { "command": "python", "args": ["<path>/mcp/server.py"] } } }
```

## Tool results
Each tool returns the engine's structured JSON: `{"ok": true, ...}` on success or
`{"ok": false, "error": {code, message, details}}` on a domain error.
