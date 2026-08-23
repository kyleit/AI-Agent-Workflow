"""Shared test fixtures — put the engine package on sys.path, provide temp repo."""

from __future__ import annotations

import os
import sys

import pytest

_SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from devteam.interface.composition import build_container  # noqa: E402


@pytest.fixture()
def root(tmp_path):
    for d in ("src", "app", "docs"):
        (tmp_path / d).mkdir()
    return str(tmp_path)


@pytest.fixture()
def container(root):
    return build_container(root)


@pytest.fixture()
def team(container):
    container.init.execute(apply=True)
    return container
