from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from workflow_runtime.application.workflow.runtime_link import linked_install_root


@dataclass(frozen=True)
class BlueprintAuthoringPolicyResult:
    passed: bool
    blocking_findings: list[str] = field(default_factory=list[str])
    # "We could not audit" is not "we detected a violation". Reporting an
    # undetectable baseline as a blocking finding would make every fresh or
    # isolated workspace unapprovable, which is worse than the defect it guards.
    diagnostics: list[str] = field(default_factory=list[str])


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
        baseline, baseline_reason = self._framework_baseline(root)
        roots = brain_roots if brain_roots is not None else self._default_brain_roots()
        findings: list[str] = []
        diagnostics: list[str] = []
        if baseline_reason:
            diagnostics.append(f"authoring_audit_baseline_unavailable:{baseline_reason}")

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

        return BlueprintAuthoringPolicyResult(
            not findings, list(dict.fromkeys(findings)), list(dict.fromkeys(diagnostics))
        )

    def _linked_install_root(self, root: Path) -> Path | None:
        """Resolve the global install root when this project is linked, not copied."""
        return linked_install_root(root)

    def _framework_baseline(self, root: Path) -> tuple[float, str]:
        """Return the audit baseline and, when it had to be guessed, why.

        A zero baseline means "every record in every session is newer than the
        framework", which flags all history. That is never the right answer, so it
        is never returned. In linked-install mode the project holds no copy of the
        candidate files, so the linked install is consulted next, then the work-item
        registry. If nothing can be derived, the current time is used, which flags
        nothing, and the caller reports that it could not establish a baseline.
        """
        relative_candidates = (
            Path(".agents") / "skills" / "aiwf" / "SKILL.md",
            Path(".agents") / "skills" / "plan-to-blueprint" / "SKILL.md",
        )
        mtimes: list[float] = []
        for relative in relative_candidates:
            try:
                mtimes.append((root / relative).stat().st_mtime)
            except OSError:
                pass
        if mtimes:
            return max(mtimes), ""

        linked = self._linked_install_root(root)
        if linked is not None:
            for relative in ("skills/aiwf/SKILL.md", "skills/plan-to-blueprint/SKILL.md"):
                try:
                    mtimes.append((linked / relative).stat().st_mtime)
                except OSError:
                    pass
            if mtimes:
                return max(mtimes), ""

        try:
            registry = root / ".agents" / "state" / "active-work-items.json"
            return registry.stat().st_mtime, ""
        except OSError:
            pass

        return time.time(), "no framework baseline, linked install, or work-item registry found"

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
            if not self._targets_artifact(line, root, target):
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
        """Broad predicate, used for this Agent's own scratch scripts.

        A scratch script that writes anywhere into the workspace during Blueprint
        authoring is suspicious on its own, so breadth is deliberate here. It is
        kept unchanged; see `_targets_artifact` for why foreign transcripts need a
        stricter rule.
        """
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
    def _targets_artifact(content: str, root: Path, target: Path) -> bool:
        """Strict predicate, used for another tool's session transcripts.

        A foreign transcript is not this Agent's scratch space. Accepting any
        mention of the workspace root — or, worse, any line containing both
        `docs/features` and `blueprint` — meant every past session that had ever
        worked in this repository was held against every future Blueprint, forever.
        The accusation is that a script authored *this document*, so the evidence
        must name *this document*.

        Known limitation, accepted deliberately: a command that changes directory
        first and then names only a bare unrecognizable path would be missed.
        Blueprint filenames here are long and work-item prefixed, so the file name
        is included as a match form to keep that gap narrow.
        """
        if target == root or target.is_dir():
            return False
        lowered = re.sub(r"/+", "/", content.replace("\\", "/").lower())
        forms = {
            re.sub(r"/+", "/", str(target).replace("\\", "/").lower()),
            target.name.lower(),
        }
        try:
            forms.add(target.relative_to(root).as_posix().lower())
        except ValueError:
            pass
        return any(form and form in lowered for form in forms)

    @staticmethod
    def _safe_relative(path: Path, root: Path) -> Path:
        try:
            return path.resolve().relative_to(root.resolve())
        except ValueError:
            return Path(path.name)


__all__ = ["BlueprintAuthoringPolicyResult", "BlueprintAuthoringPolicyValidator"]
