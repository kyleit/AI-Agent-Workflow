from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SourceContextValidationResult:
    passed: bool
    blocking_findings: list[str] = field(default_factory=list[str])


class SourceContextValidator:
    excluded_parts = {"docs", ".agents", "node_modules", "dist", "build", "__pycache__"}

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()

    def validate_blocks(
        self,
        blocks: list[dict[str, object]],
        allow_existing_creates: bool = False,
    ) -> SourceContextValidationResult:
        findings: list[str] = []
        for block in blocks:
            if not block.get("implementation_ready"):
                continue
            block_id = str(block.get("id", "unknown"))
            operation = str(block.get("operation", "")).strip().lower()
            relative = Path(str(block.get("file", "")))
            target = (self.workspace_root / relative).resolve()
            try:
                target.relative_to(self.workspace_root)
            except ValueError:
                findings.append(f"{block_id}:path_escapes_workspace")
                continue
            if any(part in self.excluded_parts for part in relative.parts):
                findings.append(f"{block_id}:path_in_excluded_folder")
            if operation == "modify":
                self._validate_modify(block, block_id, target, findings)
            elif operation in {"create", "generate"}:
                if target.exists() and not allow_existing_creates:
                    if operation == "create":
                        findings.append(f"{block_id}:create_target_already_exists")
                # A Blueprint is evaluated before implementation and may be the
                # first artifact in a newly initialized project. Parent folders
                # are therefore created by the implementation scaffold, not
                # required to exist during pre-approval.
            elif operation == "delete":
                if not target.is_file():
                    findings.append(f"{block_id}:delete_target_missing")
            else:
                findings.append(f"{block_id}:operation_unknown")
        return SourceContextValidationResult(not findings, findings)

    def _validate_modify(
        self,
        block: dict[str, object],
        block_id: str,
        target: Path,
        findings: list[str],
    ) -> None:
        if not target.is_file():
            findings.append(f"{block_id}:modify_target_missing")
            return
        symbol = str(block.get("anchor_symbol") or block.get("symbol", "")).strip()
        if not symbol:
            findings.append(f"{block_id}:modify_anchor_missing")
            return
        text = target.read_text(encoding="utf-8", errors="ignore")
        name = symbol.rsplit(".", 1)[-1]
        pattern = rf"\b(class|def|async def|function|const|let|var)\s+{re.escape(name)}\b"
        if name not in text and re.search(pattern, text) is None:
            findings.append(f"{block_id}:modify_anchor_not_found:{symbol}")


__all__ = ["SourceContextValidationResult", "SourceContextValidator"]
