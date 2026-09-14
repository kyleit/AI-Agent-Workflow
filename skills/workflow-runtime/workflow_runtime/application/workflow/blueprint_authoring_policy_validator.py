from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class BlueprintAuthoringPolicyResult:
    passed: bool
    blocking_findings: list[str] = field(default_factory=list[str])


class BlueprintAuthoringPolicyValidator:
    """Detect document generation performed by ad-hoc Agent scripts.

    Blueprint completeness is a reasoning task. A Markdown file can satisfy a
    structural validator while still having been manufactured by a script. The
    validator therefore inspects recent Agent scratch scripts as provenance
    evidence. It never treats script text as valid authorship.
    """

    _SCRIPT_SUFFIXES = {".py", ".ps1", ".js", ".ts", ".sh", ".bat", ".cmd"}
    _WRITE_OPERATIONS = re.compile(
        r"(?:write_text|write_bytes|writefilesync|fs\.writefile|"
        r"open\s*\([^\n]{0,240}[\"'](?:w|a|x|wb|ab)|"
        r"set-content|out-file|rmtree|\.unlink\s*\(|"
        r"shutil\.(?:copy|move|rmtree)|os\.(?:remove|unlink|rename|replace)|"
        r"move-item|copy-item|\brm\s+(?:-[^\n]*\s+)?|\bmv\s+)",
        re.IGNORECASE,
    )
    _DOCUMENT_TARGET = re.compile(
        r"(?:docs[\\/]features|docs[\\/]aiwf-runs|blueprint|specification|"
        r"brainstorm|roadmap|(?:^|[^a-z])plan(?:[^a-z]|$)|question)",
        re.IGNORECASE,
    )
    _INLINE_SCRIPT = re.compile(
        r"(?:python(?:\.exe)?\s+-c|powershell(?:\.exe)?\s+[^\n]*|node(?:\.exe)?\s+-e|"
        r"(?:^|\s)(?:bash|sh|cmd)(?:\.exe)?\s+[-/]c)",
        re.IGNORECASE,
    )
    _INLINE_WRITE = re.compile(
        r"(?:write_text|write_bytes|writefilesync|fs\.writefile|open\s*\([^\n]{0,240}"
        r"[\"'](?:w|a|x|wb|ab)|set-content|out-file|remove-item|rmdir|del\s+|"
        r"rmtree|\.unlink\s*\(|shutil\.(?:copy|move|rmtree)|os\.(?:remove|unlink|"
        r"rename|replace)|move-item|copy-item|\b(?:rm|mv)\s+(?:-[^\n]*\s+)?|"
        r"(?:>\s*|>>\s*))",
        re.IGNORECASE,
    )

    def validate(
        self,
        workspace_root: Path,
        blueprint_path: Path | None = None,
        *,
        brain_roots: list[Path] | None = None,
    ) -> BlueprintAuthoringPolicyResult:
        root = workspace_root.resolve()
        target = blueprint_path.resolve() if blueprint_path is not None else root
        baseline = self._framework_baseline(root)
        roots = brain_roots if brain_roots is not None else self._default_brain_roots()
        findings: list[str] = []

        for brain_root in roots:
            candidate_root = Path(brain_root).expanduser()
            if not candidate_root.is_dir():
                continue
            for scratch in self._scratch_dirs(candidate_root):
                for script in self._scripts(scratch):
                    try:
                        if script.stat().st_mtime < baseline:
                            continue
                        content = script.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    if not self._targets_workspace(content, root, target):
                        continue
                    if not self._WRITE_OPERATIONS.search(content):
                        continue
                    relative = self._safe_relative(script, candidate_root)
                    findings.append(
                        "script_authored_document_detected:"
                        f"{candidate_root.name}/{relative.as_posix()}"
                    )
            for transcript in self._transcripts(candidate_root):
                try:
                    if transcript.stat().st_mtime < baseline:
                        continue
                    transcript_findings = self._scan_transcript(
                        transcript, root, target, candidate_root
                    )
                except OSError:
                    continue
                findings.extend(transcript_findings)

        return BlueprintAuthoringPolicyResult(not findings, list(dict.fromkeys(findings)))

    def _framework_baseline(self, root: Path) -> float:
        candidates = (
            root / ".agents" / "skills" / "aiwf" / "SKILL.md",
            root / ".agents" / "skills" / "plan-to-blueprint" / "SKILL.md",
        )
        mtimes = []
        for path in candidates:
            try:
                mtimes.append(path.stat().st_mtime)
            except OSError:
                pass
        return max(mtimes, default=0.0)

    @staticmethod
    def _default_brain_roots() -> list[Path]:
        home = Path(os.path.expanduser("~"))
        configured = os.environ.get("ANTIGRAVITY_BRAIN_ROOT", "").strip()
        # An explicit root is an isolation boundary for the current host. Do
        # not mix unrelated Antigravity transcripts into a scoped validation.
        roots = (
            [Path(configured)]
            if configured
            else [
                home / ".gemini" / "antigravity-cli" / "brain",
                home / ".gemini" / "antigravity-ide" / "brain",
            ]
        )
        unique: list[Path] = []
        seen: set[str] = set()
        for path in roots:
            key = os.path.normcase(os.path.abspath(str(path)))
            if key and key not in seen:
                seen.add(key)
                unique.append(path)
        return unique

    @staticmethod
    def _scratch_dirs(brain_root: Path) -> list[Path]:
        try:
            return [
                path / "scratch"
                for path in brain_root.iterdir()
                if path.is_dir() and (path / "scratch").is_dir()
            ]
        except OSError:
            return []

    def _scripts(self, scratch: Path) -> list[Path]:
        try:
            return sorted(
                path
                for path in scratch.iterdir()
                if path.is_file() and path.suffix.lower() in self._SCRIPT_SUFFIXES
            )
        except OSError:
            return []

    @staticmethod
    def _transcripts(brain_root: Path) -> list[Path]:
        logs_root = brain_root
        try:
            return sorted(
                path
                for path in logs_root.glob("*/.system_generated/logs/transcript*.jsonl")
                if path.is_file()
            )
        except OSError:
            return []

    def _scan_transcript(
        self,
        transcript: Path,
        root: Path,
        target: Path,
        brain_root: Path,
    ) -> list[str]:
        findings: list[str] = []
        try:
            lines = transcript.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return findings

        for line in lines:
            lowered = line.replace("\\", "/").lower()
            if not self._targets_workspace(line, root, target):
                continue
            if not self._INLINE_SCRIPT.search(line):
                continue
            if not self._INLINE_WRITE.search(line):
                continue
            relative = self._safe_relative(transcript, brain_root)
            findings.append(
                "inline_script_authored_document_detected:"
                f"{brain_root.name}/{relative.as_posix()}"
            )
            break
        return findings

    @staticmethod
    def _targets_workspace(content: str, root: Path, target: Path) -> bool:
        lowered = re.sub(r"/+", "/", content.replace("\\", "/").lower())
        root_forms = {
            re.sub(r"/+", "/", str(root).replace("\\", "/").lower()).rstrip("/"),
            re.sub(r"/+", "/", str(target.parent).replace("\\", "/").lower()).rstrip("/"),
        }
        if any(form and form in lowered for form in root_forms):
            return True

        # Relative document paths are useful evidence only when validation is
        # running from this workspace. Otherwise an unrelated Antigravity
        # transcript can poison isolated fixture projects.
        current_workspace = Path.cwd().resolve() == root
        return current_workspace and "docs/features" in lowered and "blueprint" in lowered

    @staticmethod
    def _safe_relative(path: Path, root: Path) -> Path:
        try:
            return path.resolve().relative_to(root.resolve())
        except ValueError:
            return Path(path.name)


__all__ = ["BlueprintAuthoringPolicyResult", "BlueprintAuthoringPolicyValidator"]
