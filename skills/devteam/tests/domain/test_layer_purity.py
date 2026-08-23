"""Architecture fitness (§25): domain imports neither application nor infrastructure.

Static proof of the Clean Architecture dependency rule without a 3rd-party tool.
"""

from __future__ import annotations

import ast
import os

_HERE = os.path.dirname(__file__)
_DOMAIN = os.path.abspath(os.path.join(_HERE, "..", "..", "scripts", "devteam", "domain"))
_APP = os.path.abspath(os.path.join(_HERE, "..", "..", "scripts", "devteam", "application"))

_FORBIDDEN_IN_DOMAIN = ("infrastructure", "application", "interface")
_FORBIDDEN_IN_APP = ("infrastructure", "interface")


def _py_files(root: str):
    for base, _dirs, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(base, f)


def _imports(path: str) -> list[str]:
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
        elif isinstance(node, ast.Import):
            names.extend(a.name for a in node.names)
    return names


def test_domain_has_no_outward_imports():
    for path in _py_files(_DOMAIN):
        for mod in _imports(path):
            assert not any(bad in mod for bad in _FORBIDDEN_IN_DOMAIN), f"{path} imports {mod}"


def test_application_has_no_infra_or_interface_imports():
    for path in _py_files(_APP):
        for mod in _imports(path):
            assert not any(bad in mod for bad in _FORBIDDEN_IN_APP), f"{path} imports {mod}"
