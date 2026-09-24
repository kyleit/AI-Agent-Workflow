# conftest.py -- knowledge-runtime tests run against the unified workflow_runtime package.
# The legacy skills/knowledge-runtime/scripts package was consolidated into
# workflow_runtime (FEAT-500, c6df50ce), so this suite imports from there.
import os
import sys

import pytest

_RUNTIME_PKG_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "workflow-runtime")
)
if _RUNTIME_PKG_ROOT not in sys.path:
    sys.path.insert(0, _RUNTIME_PKG_ROOT)

# Mirror skills/workflow-runtime/tests/conftest.py: the root pytest.ini puts the
# flat persistence directory on sys.path, where `import db` would load db.py
# outside its package and fail on its relative imports.
sys.modules.setdefault("db", __import__("workflow_runtime.infrastructure.persistence.db", fromlist=["*"]))

from workflow_runtime.presentation.cli.bootstrap import bootstrap_di  # noqa: E402

# KnowledgeAPI resolves providers through the factory registry, which the CLI
# composition root populates.
bootstrap_di()


@pytest.fixture(autouse=True)
def _isolated_home(tmp_path, monkeypatch):
    """Keep provider config reads/writes (~/.aiwf/providers.json) out of the real home."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
