#!/usr/bin/env python3
"""Discover implementation-ready fenced code blocks in a Blueprint."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

FENCE_RE = re.compile(r"^```([A-Za-z0-9_+.#-]*)\s*$")
META_RE = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$")
PLACEHOLDER_RE = re.compile(
    r"(^|\n)\s*(?:TODO|FIXME|TBD)\b"
    r"|(^|\n)\s*(?://|#|--|/\*)\s*"
    r"(?:placeholder|sample\s+only|not\s+implemented|coming\s+soon|stub)\b"
    r"|(^|\n)\s*\.\.\.\s*(?=$|\n)|<\s*(implementation|code|todo)[^>]*>",
    re.IGNORECASE,
)
FULL_FILE_SUFFIXES = {
    ".go", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".svelte",
    ".vue", ".astro", ".css", ".scss", ".sql", ".html", ".htm",
    ".yaml", ".yml", ".json", ".toml", ".xml", ".sh", ".bash", ".zsh",
    ".ps1", ".psm1", ".psd1", ".py", ".java", ".kt", ".kts", ".rs",
    ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".php", ".rb", ".swift",
    ".dart", ".tf", ".tfvars", ".proto", ".graphql",
}
BINARY_ASSET_SUFFIXES = {".woff2", ".woff", ".ttf", ".otf", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".svg"}
GENERATED_LOCKFILE_NAMES = {
    "go.sum",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "cargo.lock",
    "composer.lock",
}


def _metadata(lines: list[str], fence_index: int) -> dict[str, str]:
    meta: dict[str, str] = {}
    idx = fence_index - 1
    while idx >= 0:
        line = lines[idx].strip()
        if not line:
            idx -= 1
            continue
        match = META_RE.match(line)
        if not match:
            break
        meta[match.group(1).replace("-", "_").lower()] = match.group(2).strip()
        idx -= 1
    return meta


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"true", "yes", "1", "y"}


def discover(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    blocks: list[dict] = []
    findings: list[str] = []
    i = 0
    while i < len(lines):
        match = FENCE_RE.match(lines[i])
        if not match:
            i += 1
            continue
        fence_language = match.group(1).strip()
        start = i + 1
        code_lines: list[str] = []
        i += 1
        while i < len(lines) and not lines[i].startswith("```"):
            code_lines.append(lines[i])
            i += 1
        end = i + 1 if i < len(lines) else len(lines)
        code = "\n".join(code_lines).rstrip() + "\n"
        meta = _metadata(lines, start - 1)
        implementation_ready = _truthy(meta.get("implementation_ready"))
        full_file = _truthy(meta.get("full_file"))
        block_scope = meta.get("block_scope", "").strip().lower()
        language = meta.get("language") or fence_language
        block_id = meta.get("id") or f"block-{len(blocks) + 1}"
        block_hash = hashlib.sha256(
            "|".join(
                [
                    block_id,
                    language,
                    meta.get("file", ""),
                    meta.get("operation", ""),
                    meta.get("symbol", ""),
                    code,
                ]
            ).encode("utf-8")
        ).hexdigest()
        block = {
            "id": block_id,
            "language": language,
            "file": meta.get("file", ""),
            "operation": meta.get("operation", ""),
            "symbol": meta.get("symbol", ""),
            "implementation_ready": implementation_ready,
            "full_file": full_file,
            "block_scope": block_scope,
            "start_line": start + 1,
            "end_line": end,
            "sha256": block_hash,
            "code": code,
            "status": "PASS",
            "findings": [],
        }
        if implementation_ready:
            for field in ("id", "language", "file", "operation"):
                if not meta.get(field):
                    block["status"] = "BLOCKED"
                    block["findings"].append(f"missing metadata field: {field}")
            suffix = Path(block["file"]).suffix.lower()
            filename = Path(block["file"]).name.lower()
            if suffix in BINARY_ASSET_SUFFIXES:
                if language.lower().strip() != "asset":
                    block["status"] = "BLOCKED"
                    block["findings"].append("binary_asset_requires_asset_manifest_language")
                if block_scope != "asset-manifest":
                    block["status"] = "BLOCKED"
                    block["findings"].append("binary_asset_requires_asset_manifest_scope")
                if full_file:
                    block["status"] = "BLOCKED"
                    block["findings"].append("binary_asset_must_not_use_full_file")
            elif filename in GENERATED_LOCKFILE_NAMES:
                if language.lower().strip() != "generated-manifest":
                    block["status"] = "BLOCKED"
                    block["findings"].append("generated_lockfile_requires_generated_manifest_language")
                if block_scope != "generated-manifest":
                    block["status"] = "BLOCKED"
                    block["findings"].append("generated_lockfile_requires_generated_manifest_scope")
                if full_file:
                    block["status"] = "BLOCKED"
                    block["findings"].append("generated_lockfile_must_not_use_full_file")
                if block.get("operation", "").lower() != "generate":
                    block["status"] = "BLOCKED"
                    block["findings"].append("generated_lockfile_requires_generate_operation")
                if not re.search(r"\b(?:go\s+mod\s+(?:tidy|download)|npm\s+(?:install|ci)|pnpm\s+install|yarn\s+install|cargo\s+generate-lockfile|composer\s+install)\b", code, re.IGNORECASE):
                    block["status"] = "BLOCKED"
                    block["findings"].append("generated_lockfile_missing_generator_command")
            elif suffix in FULL_FILE_SUFFIXES:
                if not full_file:
                    block["status"] = "BLOCKED"
                    block["findings"].append("full_file must be true for source/config/schema/UI files")
                if block_scope != "full-file":
                    block["status"] = "BLOCKED"
                    block["findings"].append("block_scope must be full-file for source/config/schema/UI files")
            if PLACEHOLDER_RE.search(code):
                block["status"] = "FAIL"
                block["findings"].append("placeholder or incomplete code detected")
            if language.lower().strip() == "asset":
                lower_code = code.lower()
                for required in ("source", "destination", "checksum"):
                    if required not in lower_code:
                        block["status"] = "BLOCKED"
                        block["findings"].append(f"asset manifest missing: {required}")
                if block_scope != "asset-manifest":
                    block["status"] = "BLOCKED"
                    block["findings"].append("asset block_scope must be asset-manifest")
        else:
            block["status"] = "NOT_APPLICABLE"
        blocks.append(block)
        i += 1
    return {"blueprint": str(path), "blocks": blocks, "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blueprint", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = discover(Path(args.blueprint))
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
