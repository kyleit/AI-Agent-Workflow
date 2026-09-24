"""`aiwf provider` CLI: config/status handlers, unsupported actions, exit codes, masking."""
import argparse
import json
import os
import subprocess
import sys

import pytest

from workflow_runtime.infrastructure.knowledge import provider_manager
from workflow_runtime.infrastructure.knowledge.provider_manager.masking import MASK
from workflow_runtime.presentation.cli.commands.provider_command import ProviderCommand

pytestmark = pytest.mark.integration

RUNTIME_PACKAGE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "workflow-runtime"))


def _run(*argv: str) -> int:
    parser = argparse.ArgumentParser()
    command = ProviderCommand()
    command.add_parser(parser.add_subparsers(dest="command"))
    return command.run(parser.parse_args(["provider", *argv]))


def _save(providers: dict) -> None:
    assert provider_manager.save_global_config({"providers": providers})


def _write_project_override(project: str, providers: dict) -> None:
    os.makedirs(os.path.join(project, ".agents"), exist_ok=True)
    with open(os.path.join(project, ".agents", "memory.config.json"), "w", encoding="utf-8") as f:
        json.dump({"providers": providers}, f)


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / "my_project"
    root.mkdir()
    monkeypatch.chdir(root)
    return str(root)


def _stdout_json(capsys):
    captured = capsys.readouterr()
    return json.loads(captured.out), captured


# --- masking: CLI uses the shared provider_manager implementation ---------------

def test_list_masks_with_shared_implementation(project, capsys):
    _save({"openai": {"enabled": True, "api_key": "sk-live", "credentials": {"user": "u", "pass": "p"},
                      "base_url": "https://api.example"}})
    assert _run("list") == 0
    data, captured = _stdout_json(capsys)
    assert data["openai"]["api_key"] == MASK
    assert data["openai"]["credentials"] == MASK
    assert data["openai"]["base_url"] == "https://api.example"
    assert "sk-live" not in captured.out and '"p"' not in captured.out


def test_resolve_masks_with_shared_implementation(project, tmp_path, capsys):
    vault = tmp_path / "Vault"
    vault.mkdir()
    _save({"obsidian": {"enabled": True, "mode": "file-sync", "vault_root": str(vault),
                        "api_key": "obs-secret", "sync_structure": False}})
    assert _run("resolve", "obsidian") == 0
    data, captured = _stdout_json(capsys)
    assert data["provider_config"]["api_key"] == MASK
    assert "obs-secret" not in captured.out


# --- config ----------------------------------------------------------------------

def test_config_shows_effective_masked_config(project, monkeypatch, capsys):
    monkeypatch.setenv("FIX423_OPENAI_KEY", "sk-from-env")
    _save({"openai": {"enabled": True, "api_key": "${FIX423_OPENAI_KEY}", "model": "global-model"},
           "qdrant": {"enabled": False, "host": "10.0.0.1"}})
    _write_project_override(project, {"openai": {"model": "project-model"}})

    assert _run("config") == 0
    data, captured = _stdout_json(capsys)
    assert data["openai"] == {"enabled": True, "api_key": MASK, "model": "project-model"}
    assert data["qdrant"]["host"] == "10.0.0.1"
    assert "sk-from-env" not in captured.out

    assert _run("config", "openai") == 0
    data, captured = _stdout_json(capsys)
    assert data == {"enabled": True, "api_key": MASK, "model": "project-model"}

    assert _run("config", "--name", "qdrant") == 0
    data, _ = _stdout_json(capsys)
    assert data == {"enabled": False, "host": "10.0.0.1"}


def test_config_unknown_provider_exits_1(project, capsys):
    assert _run("config", "missing") == 1
    data, _ = _stdout_json(capsys)
    assert data == {"status": "failure", "message": "Provider missing is not configured."}


# --- status ------------------------------------------------------------------------

def test_status_named_provider(project, capsys):
    _save({"openai": {"enabled": True, "api_key": "sk"}, "qdrant": {"enabled": False}})

    assert _run("status", "openai") == 0
    data, _ = _stdout_json(capsys)
    assert data == {"name": "openai", "configured": True, "enabled": True, "status": "success",
                    "message": "OpenAI provider API Key configured."}

    # Disabled is a reported state, not a failure.
    assert _run("status", "qdrant") == 0
    data, _ = _stdout_json(capsys)
    assert (data["configured"], data["enabled"], data["status"]) == (True, False, "failure")

    assert _run("status", "missing") == 1
    data, _ = _stdout_json(capsys)
    assert (data["configured"], data["enabled"]) == (False, False)


def test_status_all_providers(project, capsys):
    _save({"openai": {"enabled": True, "api_key": "sk"}, "qdrant": {"enabled": False}})
    assert _run("status") == 0
    data, _ = _stdout_json(capsys)
    assert [e["name"] for e in data["providers"]] == ["openai", "qdrant"]

    # An enabled provider failing its check makes the overall status unhealthy.
    _save({"openai": {"enabled": True, "api_key": ""}, "qdrant": {"enabled": False}})
    assert _run("status") == 1
    data, _ = _stdout_json(capsys)
    openai = data["providers"][0]
    assert (openai["name"], openai["status"]) == ("openai", "failure")


def test_status_with_no_providers_is_empty_and_ok(project, capsys):
    assert _run("status") == 0
    data, _ = _stdout_json(capsys)
    assert data == {"providers": []}


# --- unsupported scaffold actions ----------------------------------------------------

@pytest.mark.parametrize("action", ["select", "usage", "reset"])
def test_unsupported_actions_exit_2(project, capsys, action):
    assert _run(action) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"aiwf provider {action}: not supported" in captured.err
    assert "aiwf usage" in captured.err


# --- test / sync exit codes ------------------------------------------------------------

def test_test_exit_code_follows_result(project, capsys):
    assert _run("test", "openai") == 1
    data, _ = _stdout_json(capsys)
    assert data["status"] == "failure"

    _save({"openai": {"enabled": True, "api_key": "sk"}})
    assert _run("test", "openai") == 0
    data, _ = _stdout_json(capsys)
    assert data["status"] == "success"


def test_sync_exit_code_follows_result(project, tmp_path, capsys):
    assert _run("sync", "obsidian") == 1
    data, _ = _stdout_json(capsys)
    assert data == {"status": "failure", "message": "Obsidian is not configured."}

    vault = tmp_path / "SyncVault"
    vault.mkdir()
    _save({"obsidian": {"enabled": True, "mode": "file-sync", "vault_root": str(vault),
                        "create_if_missing": True, "sync_structure": True}})
    assert _run("sync", "obsidian") == 0
    data, _ = _stdout_json(capsys)
    assert data["status"] == "success"


def test_sync_non_obsidian_provider_exits_2(project, capsys):
    assert _run("sync", "qdrant") == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "only `obsidian` can be synced" in captured.err


def test_exit_codes_reach_the_process(project):
    env = os.environ.copy()
    env["PYTHONPATH"] = RUNTIME_PACKAGE_ROOT
    for argv, expected in ((["select"], 2), (["test", "openai"], 1), (["status"], 0)):
        result = subprocess.run([sys.executable, "-m", "workflow_runtime", "provider", *argv],
                                capture_output=True, text=True, cwd=project, env=env, timeout=60)
        assert result.returncode == expected, (argv, result.stdout, result.stderr)
