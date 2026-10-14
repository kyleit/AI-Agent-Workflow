"""Typed design contracts are coverage, not runnable implementation evidence."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import cast


def artifact_depth(text: str) -> str:
    if not text.startswith("---"):
        return ""
    parts = text.split("---", 2)
    if len(parts) != 3:
        return ""
    match = re.search(r"^blueprint_depth:\s*(.*?)\s*$", parts[1], re.MULTILINE)
    return match.group(1).strip("`\"'").upper() if match else ""


def is_contract(block: Mapping[str, object]) -> bool:
    return block.get("contract_ready") is True


def is_covered_block(block: Mapping[str, object]) -> bool:
    return bool(block.get("implementation_ready")) or is_contract(block)


def _mapping(value: object) -> dict[str, object]:
    return cast(dict[str, object], value) if isinstance(value, dict) else {}


def _items(value: object) -> list[object]:
    return cast(list[object], value) if isinstance(value, list) else []


def _strings(value: object) -> list[str]:
    items = _items(value)
    if not items or not all(isinstance(item, str) and item.strip() for item in items):
        return []
    return [str(item) for item in items]


def _payload(block: Mapping[str, object]) -> dict[str, object]:
    try:
        value: object = json.loads(str(block.get("code", "")))
    except (ValueError, TypeError):
        return {}
    return _mapping(value)


def _type_valid(node: ast.AST | None) -> bool:
    if node is None:
        return False
    allowed = (ast.Expression, ast.Name, ast.Attribute, ast.Subscript, ast.Tuple,
               ast.List, ast.Constant, ast.BinOp, ast.BitOr, ast.Load)
    for item in ast.walk(node):
        if not isinstance(item, allowed):
            return False
        if isinstance(item, ast.Name) and item.id in {"Any", "Unknown"}:
            return False
        if isinstance(item, ast.Attribute) and item.attr in {"Any", "Unknown"}:
            return False
        if isinstance(item, ast.Constant) and isinstance(item.value, str):
            try:
                if not _type_valid(ast.parse(item.value, mode="eval")):
                    return False
            except (SyntaxError, RecursionError):
                return False
    return True


def _signature(value: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    try:
        tree = ast.parse("def " + value + ":\n    raise NotImplementedError\n")
    except (SyntaxError, ValueError):
        return None
    node = tree.body[0]
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or len(tree.body) != 1:
        return None
    args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
    if node.args.vararg:
        args.append(node.args.vararg)
    if node.args.kwarg:
        args.append(node.args.kwarg)
    if not _type_valid(node.returns) or any(
        not _type_valid(arg.annotation) for arg in args if arg.arg not in {"self", "cls"}
    ):
        return None
    return node


def validate_contract(block: Mapping[str, object]) -> list[str]:
    findings: list[str] = []
    for field in ("id", "language", "file", "operation", "target_language"):
        if not str(block.get(field, "")).strip():
            findings.append(f"contract_metadata_missing:{field}")
    if block.get("blueprint_depth") != "CONTRACT":
        findings.append("contract_requires_contract_artifact_depth")
    if block.get("implementation_ready") or block.get("full_file"):
        findings.append("contract_is_not_implementation_ready")
    if block.get("block_scope") != "contract" or block.get("language") != "json":
        findings.append("contract_requires_typed_json_declaration")
    if block.get("contract_kind") not in {"interface", "schema"}:
        findings.append("contract_kind_invalid_pure_rules_require_real_bodies")
    target = str(block.get("file", ""))
    if (not target or PurePosixPath(target).is_absolute() or "\\" in target
            or any(char in target for char in (":", "*", "?", "\x00"))
            or any(part in {"", ".", ".."} for part in target.split("/"))):
        findings.append("contract_target_not_exact_relative_path")
    data = _payload(block)
    if data.get("schema_version") != "aiwf.contract/1":
        findings.append("contract_schema_invalid")
    for field in ("errors", "invariants", "acceptance", "verification"):
        if not _strings(data.get(field)):
            findings.append(f"contract_obligation_missing:{field}")
    exports = _items(data.get("exports"))
    if not exports:
        findings.append("contract_exports_missing")
    names: set[str] = set()
    for export in exports:
        entry = _mapping(export)
        name = str(entry.get("name", ""))
        if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", name) or name in names:
            findings.append("contract_export_name_invalid_or_duplicate")
        names.add(name)
        signature = str(entry.get("signature", ""))
        fields = _mapping(entry.get("fields"))
        if signature:
            node = _signature(signature)
            if node is None or node.name != name.rsplit(".", 1)[-1]:
                findings.append(f"contract_signature_untyped_or_invalid:{name}")
        elif fields:
            for field, type_name in fields.items():
                try:
                    valid = field.isidentifier() and _type_valid(ast.parse(str(type_name), mode="eval"))
                except (SyntaxError, ValueError, RecursionError):
                    valid = False
                if not valid:
                    findings.append(f"contract_field_untyped_or_invalid:{name}.{field}")
        else:
            findings.append(f"contract_export_definition_missing:{name}")
    return findings


def validate_baselines(root: Path, blocks: list[Mapping[str, object]]) -> list[str]:
    findings: list[str] = []
    for block in blocks:
        if not is_contract(block) or block.get("operation") != "modify":
            continue
        target = (root / str(block.get("file", ""))).resolve()
        try:
            target.relative_to(root.resolve())
            text = target.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip()
        except (ValueError, OSError, UnicodeError):
            findings.append(f"contract_baseline_unreadable:{block.get('id')}")
            continue
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest != block.get("base_sha256"):
            findings.append(f"contract_baseline_hash_mismatch:{block.get('id')}")
    return findings


def _shape(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = node.args
    def parameter(arg: ast.arg) -> str:
        return arg.arg + ":" + (ast.unparse(arg.annotation) if arg.annotation else "")
    parts = [parameter(arg) for arg in args.posonlyargs + args.args if arg.arg not in {"self", "cls"}]
    parts.extend("kw:" + parameter(arg) for arg in args.kwonlyargs)
    if args.vararg:
        parts.append("*" + parameter(args.vararg))
    if args.kwarg:
        parts.append("**" + parameter(args.kwarg))
    return "|".join(parts) + "->" + (ast.unparse(node.returns) if node.returns else "")


def _python_exports(target: Path, data: dict[str, object]) -> list[str]:
    findings: list[str] = []
    try:
        source = target.read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
        compile(tree, str(target), "exec")
    except (SyntaxError, ValueError, OSError, UnicodeError) as error:
        return [f"python_contract_source_invalid:{type(error).__name__}"]
    nodes: dict[str, ast.AST] = {}
    def collect(body: list[ast.stmt], prefix: str = "") -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                nodes[prefix + node.name] = node
                if isinstance(node, ast.ClassDef):
                    collect(node.body, prefix + node.name + ".")
    collect(tree.body)
    for value in _items(data.get("exports")):
        export = _mapping(value)
        name = str(export.get("name", ""))
        node = nodes.get(name)
        signature = str(export.get("signature", ""))
        if signature:
            expected = _signature(signature)
            if (not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or expected is None
                    or _shape(node) != _shape(expected)):
                findings.append(f"python_contract_signature_mismatch:{name}")
            elif all(isinstance(item, ast.Pass) or (
                isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant)
            ) for item in node.body):
                findings.append(f"python_contract_body_missing:{name}")
        elif isinstance(node, ast.ClassDef):
            actual_fields = {item.target.id: ast.unparse(item.annotation) for item in node.body
                             if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)}
            for field, declared in _mapping(export.get("fields")).items():
                if actual_fields.get(field) != declared:
                    findings.append(f"python_contract_field_mismatch:{name}.{field}")
        else:
            findings.append(f"python_contract_export_missing:{name}")
    return findings


def verify_implementation(root: Path, workflow_id: str, blocks: list[Mapping[str, object]]) -> list[str]:
    contracts = [block for block in blocks if is_contract(block)]
    if not contracts:
        return []
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", workflow_id):
        return ["contract_workflow_id_invalid"]
    evidence_path = root / "docs" / "aiwf-runs" / workflow_id / "verification" / "contract-implementation.json"
    try:
        evidence = _mapping(json.loads(evidence_path.read_text(encoding="utf-8")))
    except (OSError, ValueError, UnicodeError):
        evidence = {}
    findings: list[str] = []
    for block in contracts:
        identifier = str(block.get("id", ""))
        target = (root / str(block.get("file", ""))).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            findings.append(f"contract_target_outside_root:{identifier}")
            continue
        if not target.is_file():
            findings.append(f"contract_target_missing:{identifier}")
            continue
        data = _payload(block)
        if block.get("target_language") == "python":
            findings.extend(f"{identifier}:{item}" for item in _python_exports(target, data))
        record = _mapping(_mapping(evidence.get("contracts")).get(identifier))
        artifact = Path(str(block.get("artifact", "")))
        try:
            artifact_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
        except OSError:
            artifact_hash = ""
        source_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        runs = _items(record.get("runs"))
        passed_commands = {str(run.get("command", "")) for item in runs
                           if type((run := _mapping(item)).get("exit_code")) is int
                           and run.get("exit_code") == 0
                           and run.get("executed") is True}
        required = set(_strings(data.get("verification")))
        if (evidence.get("work_item_id") != workflow_id or not artifact_hash
                or record.get("artifact_sha256") != artifact_hash
                or record.get("source_sha256") != source_hash
                or not required or not required.issubset(passed_commands)):
            findings.append(f"contract_verification_evidence_missing_or_stale:{identifier}")
    return findings
