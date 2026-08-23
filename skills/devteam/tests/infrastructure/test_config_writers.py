"""Config writers (§15): three tools, refuse-without-approval, non-destructive merge."""

import json
import os

from devteam.infrastructure.install import config_writers as cw


def test_plan_all_returns_three_tools(tmp_path):
    tools = {c.tool for c in cw.plan_all(str(tmp_path))}
    assert tools == {"claude", "codex", "antigravity"}


def test_apply_refuses_without_approval(tmp_path):
    res = cw.apply(cw.plan_claude(str(tmp_path)), approved=False)
    assert res["applied"] is False
    assert "approval required" in res["reason"].lower()


def test_merge_json_preserves_existing_servers(tmp_path):
    target = os.path.join(str(tmp_path), ".mcp.json")
    open(target, "w", encoding="utf-8").write(json.dumps({"mcpServers": {"other": {"command": "x"}}}))
    res = cw.apply(cw.plan_claude(str(tmp_path)), approved=True)
    assert res["applied"] is True and os.path.exists(res["backup"])
    data = json.loads(open(target, encoding="utf-8").read())
    assert "other" in data["mcpServers"]            # not clobbered
    assert data["mcpServers"]["devteam"]["command"] == "python"


def test_merge_json_creates_when_missing(tmp_path):
    cw.apply(cw.plan_claude(str(tmp_path)), approved=True)
    data = json.loads(open(os.path.join(str(tmp_path), ".mcp.json"), encoding="utf-8").read())
    assert "devteam" in data["mcpServers"]


def test_toml_append_is_idempotent_and_non_destructive(tmp_path, monkeypatch):
    cfg = os.path.join(str(tmp_path), "config.toml")
    open(cfg, "w", encoding="utf-8").write("[mcp_servers.node_repl]\ncommand = \"node\"\n")
    change = cw.ConfigChange("codex", cfg, "append-toml-block", cw._toml_block(), cfg + ".bak")
    first = cw.apply(change, approved=True)
    assert first["applied"] is True
    text = open(cfg, encoding="utf-8").read()
    assert "[mcp_servers.node_repl]" in text and "[mcp_servers.devteam]" in text
    # second apply must not duplicate the block
    second = cw.apply(change, approved=True)
    assert second["applied"] is False
    assert open(cfg, encoding="utf-8").read().count("[mcp_servers.devteam]") == 1
