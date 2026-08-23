"""One-shot setup + doctor — sandboxed to a temp HOME/AIWF_HOME (no real machine writes)."""

import os
import sysconfig

import pytest

from devteam.infrastructure.install.doctor import run_doctor
from devteam.infrastructure.install.setup import run_setup


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    site = tmp_path / "site"
    site.mkdir()
    monkeypatch.setenv("AIWF_HOME", str(tmp_path / "aiwf"))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    # keep the .pth out of the real site-packages during tests
    _orig = sysconfig.get_path
    monkeypatch.setattr(
        sysconfig,
        "get_path",
        lambda name, *a, **k: str(site) if name == "purelib" else _orig(name, *a, **k),
    )
    return {"home": str(home), "repo": str(repo), "site": str(site)}


def test_setup_installs_engine_and_adapters_without_configs(sandbox):
    res = run_setup(sandbox["repo"], write_configs=False, with_mcp=False)
    assert res["engine"]["installed"] is True
    assert len(res["adapters"]["installed"]) == 3
    # configs planned but NOT written (hard-gated)
    assert all(c["applied"] is False for c in res["configs"])
    assert res["configs_written"] is False
    # engine present, but claude config not written yet
    doc = res["doctor"]
    names = {c["name"]: c["ok"] for c in doc["checks"]}
    assert names["engine_installed"] is True
    assert names["config_claude"] is False


def test_setup_with_write_configs_registers_mcp(sandbox):
    res = run_setup(sandbox["repo"], write_configs=True, with_mcp=False)
    assert res["configs_written"] is True
    assert os.path.exists(os.path.join(sandbox["repo"], ".mcp.json"))
    doc = run_doctor(sandbox["repo"])
    names = {c["name"]: c["ok"] for c in doc["checks"]}
    assert names["config_claude"] is True
    assert names["adapter_claude"] is True
    assert names["engine_installed"] is True


def test_doctor_before_setup_reports_missing(sandbox):
    doc = run_doctor(sandbox["repo"])
    assert doc["ok"] is False
    assert "engine_installed" in doc["failed"]
