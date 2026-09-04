from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast


def do_update_source(args: Any) -> int:
    from workflow_runtime.application.system import update_source
    return update_source.handle_update_source(args)


RUNTIME_COMMAND_DIR = os.path.join(".agents", "runtime", "commands")
RUNTIME_REQUEST_PATH = os.path.join(RUNTIME_COMMAND_DIR, "runtime.request.json")
RUNTIME_RESPONSE_PATH = os.path.join(RUNTIME_COMMAND_DIR, "runtime.response.json")
RUNTIME_LAST_REQUEST_PATH = os.path.join(RUNTIME_COMMAND_DIR, "runtime.last.request.json")

_LOCAL_PATH_ROOTS = ("Users", "Volumes", "private", "home", "tmp", "var", "var/folders")
_LOCAL_SLASH = chr(47)
_LOCAL_FILE_URL_RE = re.compile("file:" + (_LOCAL_SLASH * 3) + r"(?:" + "|".join(_LOCAL_PATH_ROOTS) + r"|[A-Za-z]:)[^\s\"')\]]*")
_LOCAL_ABS_PATH_RE = re.compile(r"(?<![\w:" + re.escape(_LOCAL_SLASH) + r".-])(?:"
                                + re.escape(_LOCAL_SLASH)
                                + r"(?:"
                                + "|".join(_LOCAL_PATH_ROOTS)
                                + r")[^\s\"')\]]*|[A-Za-z]:[\\/][^\s\"')\]]*)")


def _read_json_file(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return cast(dict[str, Any], data)


def _write_json_file_atomic(path: str, data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp_path, path)


def _sanitize_runtime_string(value: str) -> str:
    value = re.sub(r"\$\{(?:USERPROFILE|HOME)\}", "[local-env-path-redacted]", value, flags=re.IGNORECASE)
    value = re.sub(r"%(?:USERPROFILE|HOME)%", "[local-env-path-redacted]", value, flags=re.IGNORECASE)
    value = _LOCAL_FILE_URL_RE.sub("[local-file-url-redacted]", value)
    return _LOCAL_ABS_PATH_RE.sub("[local-path-redacted]", value)


def _sanitize_runtime_value(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_runtime_string(value)
    if isinstance(value, list):
        list_val = cast(list[Any], value)
        return [_sanitize_runtime_value(item) for item in list_val]
    if isinstance(value, tuple):
        tuple_val = cast(tuple[Any, ...], value)
        return [_sanitize_runtime_value(item) for item in tuple_val]
    if isinstance(value, dict):
        dict_val = cast(dict[str, Any], value)
        return {str(key): _sanitize_runtime_value(item) for key, item in dict_val.items()}
    return value


def _sanitize_artifact_tree(base_dir: str, roots: tuple[str, ...]) -> list[str]:
    changed: list[str] = []
    text_suffixes = {".md", ".json", ".yaml", ".yml", ".txt", ".log"}
    for root in roots:
        abs_root = os.path.join(base_dir, root)
        if not os.path.isdir(abs_root):
            continue
        for root_dir, _dirs, files in os.walk(abs_root):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in text_suffixes:
                    continue
                file_path = os.path.join(root_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    sanitized = _sanitize_runtime_string(content)
                    if sanitized != content:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(sanitized)
                        rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
                        changed.append(rel_path)
                except Exception:
                    pass
    return changed


def _capture_file_hashes(base_dir: str, paths: tuple[str, ...]) -> dict[str, str]:
    import hashlib
    hashes: dict[str, str] = {}
    for rel_path in paths:
        abs_path = os.path.join(base_dir, rel_path)
        if os.path.isfile(abs_path):
            try:
                with open(abs_path, "rb") as f:
                    hashes[rel_path.replace("\\", "/")] = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                pass
    return hashes


def _capture_tree_hashes(base_dir: str, roots: tuple[str, ...]) -> dict[str, str]:
    import hashlib
    hashes: dict[str, str] = {}
    for root in roots:
        abs_root = os.path.join(base_dir, root)
        if not os.path.isdir(abs_root):
            continue
        for root_dir, _dirs, files in os.walk(abs_root):
            for filename in files:
                file_path = os.path.join(root_dir, filename)
                try:
                    rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
                    with open(file_path, "rb") as f:
                        hashes[rel_path] = hashlib.sha256(f.read()).hexdigest()
                except Exception:
                    pass
    return hashes


def _capture_tree_contents(base_dir: str, roots: tuple[str, ...]) -> dict[str, bytes]:
    contents: dict[str, bytes] = {}
    for root in roots:
        abs_root = os.path.join(base_dir, root)
        if not os.path.isdir(abs_root):
            continue
        for root_dir, _dirs, files in os.walk(abs_root):
            for filename in files:
                file_path = os.path.join(root_dir, filename)
                try:
                    rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
                    with open(file_path, "rb") as f:
                        contents[rel_path] = f.read()
                except Exception:
                    pass
    return contents


def _restore_tree_contents(base_dir: str, roots: tuple[str, ...], before: dict[str, bytes]) -> None:
    after_keys = set(_capture_tree_contents(base_dir, roots).keys())
    for rel_path in after_keys:
        if rel_path not in before:
            abs_path = os.path.join(base_dir, rel_path)
            try:
                os.remove(abs_path)
            except Exception:
                pass
    for rel_path, content in before.items():
        abs_path = os.path.join(base_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(content)


def _capture_aiwf_guarded_source_hashes(base_dir: str) -> dict[str, str]:
    return _capture_tree_hashes(base_dir, ("skills", os.path.join(".agents", "skills")))


def _diff_tree_hashes(before: dict[str, str], after: dict[str, str]) -> list[str]:
    changed: list[str] = []
    for path in sorted(set(before) | set(after)):
        if before.get(path) != after.get(path):
            changed.append(path)
    return changed


def _has_workflow_documentation_changes(before: dict[str, str], after: dict[str, str]) -> bool:
    return any(path.startswith("docs/") for path in _diff_tree_hashes(before, after))


def _has_workflow_report_changes(changed_docs: list[str]) -> bool:
    return any(path.startswith("docs/reports/") or "/reports/" in path for path in changed_docs)


def _capture_release_metadata_hashes(base_dir: str) -> dict[str, str]:
    return _capture_file_hashes(
        base_dir,
        (
            "CHANGELOG.md",
            "MANIFEST.json",
            os.path.join(".agents", "MANIFEST.json"),
            "package.json",
            "pyproject.toml",
        ),
    )


def _has_release_metadata_changes(before: dict[str, str], after: dict[str, str]) -> bool:
    return bool(_diff_tree_hashes(before, after))


def _runtime_bus_response(
    status: str,
    command: str,
    idempotency_key: str,
    message: str,
    data: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "type": "RUNTIME_RESULT",
        "status": status,
        "command": command,
        "idempotency_key": idempotency_key,
        "message": _sanitize_runtime_value(message),
        "completed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    if data is not None:
        response["data"] = _sanitize_runtime_value(data)
    if error is not None:
        response["error"] = _sanitize_runtime_value(error)
    return response


def _audit_workflow_document_quality(base_dir: str, require_standard_chain: bool = False) -> list[str]:
    root = os.path.abspath(base_dir)
    issues: list[str] = []
    docs_root = os.path.join(root, "docs")
    markdown_files = [
        os.path.join(dirpath, name)
        for dirpath, _dirs, names in os.walk(docs_root)
        for name in names if name.lower().endswith(".md")
    ] if os.path.isdir(docs_root) else []
    for filename in markdown_files:
        try:
            content = open(filename, "r", encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        relative = os.path.relpath(filename, root).replace("\\", "/")
        if _LOCAL_FILE_URL_RE.search(content) or _LOCAL_ABS_PATH_RE.search(content):
            issues.append(f"{relative}: local absolute path or local-file URL")
        if "\ufffd" in content or "â€“" in content:
            issues.append(f"{relative}: mojibake")
        # Lowercase words such as "todo" are valid prose; only explicit marker
        # spellings are actionable placeholders.
        if re.search(r"\b(?:TODO|TBD|FIXME)\b", content):
            issues.append(f"{relative}: contains placeholder marker")
        if "/blueprints/" in f"/{relative}/" and "```" not in content:
            issues.append(f"{relative}: missing fenced code block")
        if "/architecture-reviews/" in f"/{relative}/" and re.search(r"PASS", content, re.IGNORECASE) and "Failed Points" in content and "None" in content:
            issues.append(f"{relative}: rubber-stamp PASS")
        if "/reports/" in f"/{relative}/" and "no test files" in content.lower():
            issues.append(f"{relative}: claims test coverage from no-test-files output")
        if "/reports/" in f"/{relative}/" and "VERIFIED" in content and not re.search(r"runtime|live|process|http", content, re.IGNORECASE):
            issues.append(f"{relative}: final completion claim lacks live runtime evidence")
    if require_standard_chain:
        features_root = os.path.join(root, "docs", "features")
        for family in [Path(features_root) / item for item in os.listdir(features_root)] if os.path.isdir(features_root) else []:
            if not family.is_dir():
                continue
            family_files = [path.replace("\\", "/") for path in markdown_files if path.startswith(str(family))]
            required_entries = ("roadmaps", "architecture-reviews", "brainstorming", "plans", "blueprints/master", "blueprints/phase-NN")
            for entry in required_entries:
                if entry == "blueprints/master":
                    present = any("/blueprints/master/" in path for path in family_files)
                elif entry == "blueprints/phase-NN":
                    present = any(re.search(r"/blueprints/phase-\d{2}(?:-[^/]+)?/", path) for path in family_files)
                else:
                    present = any(f"/{entry}/" in path for path in family_files)
                if not present:
                    issues.append(f"{family.as_posix()}: missing {entry} artifact")
    return issues


def _prepare_agy_prompt_and_mode(
    raw_prompt: str,
    requested_mode: str = "",
    context: dict[str, Any] | None = None,
) -> tuple[str, str, bool]:
    context = context or {}
    if context.get("allow_raw_agy_prompt"):
        return raw_prompt, requested_mode, False
    if requested_mode == "implement" and context.get("blueprint_approved"):
        return raw_prompt, requested_mode, False
    normalized = raw_prompt if raw_prompt.lstrip().startswith("/aiwf") else f"/aiwf {raw_prompt}"
    guard = (
        "NO BLUEPRINT - NO CODE. Follow AIWF workflow even when the user did not type /aiwf. "
        "Do not stop after workflow detection. Never emit local absolute paths or file:/// links.\n\n"
    )
    return guard + normalized, "plan", True


def _resolve_runtime_working_dir() -> str:
    return os.getcwd()


do_update_source_handler = do_update_source
audit_workflow_document_quality = _audit_workflow_document_quality
capture_aiwf_guarded_source_hashes = _capture_aiwf_guarded_source_hashes
capture_release_metadata_hashes = _capture_release_metadata_hashes
capture_tree_contents = _capture_tree_contents
capture_tree_hashes = _capture_tree_hashes
diff_tree_hashes = _diff_tree_hashes
has_release_metadata_changes = _has_release_metadata_changes
has_workflow_documentation_changes = _has_workflow_documentation_changes
has_workflow_report_changes = _has_workflow_report_changes
prepare_agy_prompt_and_mode = _prepare_agy_prompt_and_mode
read_json_file = _read_json_file
resolve_runtime_working_dir = _resolve_runtime_working_dir
restore_tree_contents = _restore_tree_contents
runtime_bus_response = _runtime_bus_response
sanitize_artifact_tree = _sanitize_artifact_tree
write_json_file_atomic = _write_json_file_atomic


__all__ = [
    "do_update_source",
    "do_update_source_handler",
    "audit_workflow_document_quality",
    "capture_aiwf_guarded_source_hashes",
    "capture_release_metadata_hashes",
    "capture_tree_contents",
    "capture_tree_hashes",
    "diff_tree_hashes",
    "has_release_metadata_changes",
    "has_workflow_documentation_changes",
    "has_workflow_report_changes",
    "prepare_agy_prompt_and_mode",
    "read_json_file",
    "resolve_runtime_working_dir",
    "restore_tree_contents",
    "runtime_bus_response",
    "sanitize_artifact_tree",
    "write_json_file_atomic",
]
