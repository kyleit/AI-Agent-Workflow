"""Lifecycle protection for technical blueprints.

The lifecycle is deliberately stored per work item.  This keeps an old
approval from becoming an authorization for a different feature while still
preserving the original document for audit and recovery.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


_TERMINAL = {"SUPERSEDED", "ABANDONED"}
_SOURCE_EXTENSIONS = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".go", ".h", ".hpp", ".html",
    ".java", ".js", ".jsx", ".json", ".kt", ".lua", ".php", ".py", ".rb",
    ".rs", ".scss", ".sh", ".sql", ".svelte", ".swift", ".ts", ".tsx",
    ".vue", ".xml", ".yaml", ".yml",
}
_EXCLUDED_PARTS = {
    ".git", ".agents", "docs", "artifacts", "scratch", "_to_delete",
    "node_modules", "dist", "build", ".venv", "venv", "__pycache__",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: str, fallback: datetime) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return fallback


@dataclass(frozen=True)
class BlueprintLifecycle:
    work_item_id: str
    blueprint_path: str
    state: str
    created_at: str
    source_snapshot: str
    updated_at: str
    reason: str = ""
    replacement_work_item: str | None = None
    actor: str = "aiwf"
    blueprint_sha256: str = ""


@dataclass(frozen=True)
class BlueprintInspection:
    lifecycle_state: str
    stale: bool
    reasons: tuple[str, ...]
    source_snapshot: str
    registry_path: str
    next_action: str
    blueprint_path: str
    work_item_id: str

    def payload(self) -> dict[str, Any]:
        body = asdict(self)
        body["reasons"] = list(self.reasons)
        return body


class BlueprintAgePolicy:
    def __init__(self, max_age_days: int | None = None) -> None:
        configured = max_age_days
        if configured is None:
            raw = os.environ.get("AIWF_BLUEPRINT_MAX_AGE_DAYS", "30")
            try:
                configured = int(raw)
            except ValueError:
                configured = 30
        self.max_age_days = max(1, configured)

    def expired(self, created_at: str, now: datetime) -> bool:
        created = _parse_time(created_at, now)
        return now - created > timedelta(days=self.max_age_days)


class BlueprintSourceSnapshotter:
    """Build a stable source-only snapshot without reading generated docs/state."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _source_revision(self) -> str:
        commands = [
            ["git", "log", "-1", "--format=%H", "--", ".", ":(exclude)docs", ":(exclude).agents"],
            ["git", "rev-parse", "HEAD"],
        ]
        for command in commands:
            try:
                result = subprocess.run(
                    command, cwd=self.root, capture_output=True, text=True,
                    check=False, timeout=10,
                )
                value = result.stdout.strip()
                if result.returncode == 0 and value:
                    return value
            except (OSError, subprocess.SubprocessError):
                continue
        return "uncommitted"

    def _files(self) -> list[Path]:
        try:
            result = subprocess.run(
                ["git", "ls-files", "-co", "--exclude-standard"],
                cwd=self.root, capture_output=True, text=True, check=False, timeout=20,
            )
            candidates = [self.root / line.strip() for line in result.stdout.splitlines() if line.strip()]
        except (OSError, subprocess.SubprocessError):
            candidates = [p for p in self.root.rglob("*") if p.is_file()]
        selected: list[Path] = []
        for path in candidates:
            try:
                relative = path.resolve().relative_to(self.root)
                if any(part in _EXCLUDED_PARTS for part in relative.parts):
                    continue
                if path.suffix.lower() not in _SOURCE_EXTENSIONS or path.stat().st_size > 1_048_576:
                    continue
                selected.append(path)
            except (OSError, ValueError):
                continue
        return sorted(set(selected), key=lambda item: item.as_posix())

    def current(self) -> str:
        digest = hashlib.sha256()
        for path in self._files():
            relative = path.relative_to(self.root).as_posix()
            try:
                stat = path.stat()
                content = path.read_bytes()
            except OSError:
                continue
            digest.update(relative.encode("utf-8"))
            digest.update(str(stat.st_size).encode("ascii"))
            digest.update(hashlib.sha256(content).digest())
        return f"git:{self._source_revision()};source:{digest.hexdigest()}"


class BlueprintLifecycleRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.base = self.root / ".agents" / "state" / "work-items"

    def path(self, work_item_id: str) -> Path:
        safe = "".join(ch for ch in work_item_id if ch.isalnum() or ch in "-_.")
        if not safe or safe != work_item_id:
            raise ValueError("invalid_work_item_id")
        return self.base / safe / "blueprint-lifecycle.json"

    def relative_path(self, work_item_id: str) -> str:
        return self.path(work_item_id).relative_to(self.root).as_posix()

    def load(self, work_item_id: str, blueprint_path: Path) -> BlueprintLifecycle | None:
        registry_path = self.path(work_item_id)
        if not registry_path.is_file():
            return None
        try:
            raw = json.loads(registry_path.read_text(encoding="utf-8"))
            record = BlueprintLifecycle(**{key: raw[key] for key in BlueprintLifecycle.__dataclass_fields__ if key in raw})
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            return None
        if Path(record.blueprint_path).as_posix() != blueprint_path.relative_to(self.root).as_posix():
            return None
        return record

    def write(self, record: BlueprintLifecycle) -> Path:
        target = self.path(record.work_item_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix="blueprint-lifecycle-", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(asdict(record), handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(temporary, target)
        except Exception:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise
        return target


class BlueprintLifecycleService:
    def __init__(self, root: Path | None = None, max_age_days: int | None = None) -> None:
        self.root = (root or Path(os.environ.get("AIWF_PROJECT_ROOT") or os.getcwd())).resolve()
        self.registry = BlueprintLifecycleRegistry(self.root)
        self.snapshotter = BlueprintSourceSnapshotter(self.root)
        self.age_policy = BlueprintAgePolicy(max_age_days)

    def _resolve(self, path: Path) -> tuple[Path, str]:
        resolved = path if path.is_absolute() else self.root / path
        resolved = resolved.resolve()
        relative = resolved.relative_to(self.root).as_posix()
        if not relative.startswith("docs/"):
            raise ValueError("blueprint_must_be_under_docs")
        return resolved, relative

    def _created_at(self, path: Path, now: datetime) -> str:
        try:
            text = path.read_text(encoding="utf-8-sig")
            for line in text.splitlines():
                if line.lower().startswith("created_at:"):
                    return line.split(":", 1)[1].strip()
            return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
        except OSError:
            return now.isoformat()

    def inspect(self, path: Path, work_item_id: str, now: datetime | None = None) -> BlueprintInspection:
        moment = now or _now()
        blueprint_path, relative = self._resolve(path)
        current_snapshot = self.snapshotter.current()
        record = self.registry.load(work_item_id, blueprint_path)
        if record is None:
            record = BlueprintLifecycle(
                work_item_id=work_item_id,
                blueprint_path=relative,
                state="PENDING",
                created_at=self._created_at(blueprint_path, moment),
                source_snapshot=current_snapshot,
                updated_at=moment.isoformat(),
                blueprint_sha256=hashlib.sha256(blueprint_path.read_bytes()).hexdigest(),
            )
            self.registry.write(record)
        reasons: list[str] = []
        if record.state in _TERMINAL:
            reasons.append("blueprint_retired")
        if self.age_policy.expired(record.created_at, moment):
            reasons.append("blueprint_age_exceeded")
        if not record.source_snapshot:
            reasons.append("blueprint_source_drift")
        elif record.source_snapshot != current_snapshot:
            reasons.append("blueprint_source_drift")
        stale = bool(reasons)
        state = record.state if record.state in _TERMINAL else ("STALE" if stale else record.state)
        next_action = "create and approve a fresh Blueprint" if stale else "await owner approval"
        return BlueprintInspection(
            lifecycle_state=state,
            stale=stale,
            reasons=tuple(dict.fromkeys(reasons)),
            source_snapshot=current_snapshot,
            registry_path=self.registry.relative_path(work_item_id),
            next_action=next_action,
            blueprint_path=relative,
            work_item_id=work_item_id,
        )

    def retire(
        self, path: Path, work_item_id: str, reason: str, replacement: str | None = None,
        actor: str = "aiwf",
    ) -> BlueprintLifecycle:
        if not reason.strip():
            raise ValueError("retirement_reason_required")
        blueprint_path, relative = self._resolve(path)
        existing = self.registry.load(work_item_id, blueprint_path)
        state = "SUPERSEDED" if replacement else "ABANDONED"
        if existing and existing.state in _TERMINAL:
            if existing.state == state and existing.reason == reason.strip() and existing.replacement_work_item == replacement:
                return existing
            raise ValueError("blueprint_terminal_state_immutable")
        now = _now().isoformat()
        record = BlueprintLifecycle(
            work_item_id=work_item_id,
            blueprint_path=relative,
            state=state,
            created_at=existing.created_at if existing else self._created_at(blueprint_path, _now()),
            source_snapshot=existing.source_snapshot if existing else self.snapshotter.current(),
            updated_at=now,
            reason=reason.strip(),
            replacement_work_item=replacement,
            actor=actor,
            blueprint_sha256=hashlib.sha256(blueprint_path.read_bytes()).hexdigest(),
        )
        self.registry.write(record)
        return record


__all__ = [
    "BlueprintAgePolicy", "BlueprintInspection", "BlueprintLifecycle",
    "BlueprintLifecycleRegistry", "BlueprintLifecycleService", "BlueprintSourceSnapshotter",
]
