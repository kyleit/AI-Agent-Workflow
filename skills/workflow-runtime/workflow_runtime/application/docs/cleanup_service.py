import datetime
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from workflow_runtime.shared.errors import DomainException, PathPolicyViolation


@dataclass(frozen=True)
class ComplianceReport:
    total_files: int
    clean_tracked_count: int
    violating_files: list[str]
    compliance_score: int


@dataclass(frozen=True)
class MigrationSummary:
    backup_path: str
    files_moved: int
    directories_created: int
    errors: list[str]
    moved_files: list[str] = field(default_factory=list[str])

    @property
    def is_success(self) -> bool:
        return len(self.errors) == 0


class DocsCleanupService:
    """Application service for semantic documentation auditing and file migration."""

    def __init__(self, workspace_root: str = ".") -> None:
        self.workspace_root = workspace_root

    def classify_family(self, file_path: str) -> str:
        """Classifies document file into semantic feature family using content keyword inspection."""
        abs_path = (
            Path(file_path)
            if Path(file_path).is_absolute()
            else Path(self.workspace_root) / file_path
        )
        if not abs_path.exists():
            raise DomainException(f"Target document file does not exist: {file_path}")

        try:
            with abs_path.open(encoding="utf-8", errors="ignore") as f:
                content = f.read(2048).lower()
        except OSError as e:
            raise DomainException(f"Failed to read document file: {file_path}") from e

        if "telegram" in content or "telegram" in file_path.lower():
            return "telegram"
        elif (
            "visualizer" in content
            or "vir" in content
            or "visualizer" in file_path.lower()
        ):
            return "visualizer"
        elif (
            "workflow-runtime" in content
            or "session" in content
            or "workflow" in file_path.lower()
        ):
            return "workflow-runtime"
        elif (
            "python-runtime" in content
            or "feat-500" in content
            or "workflow_runtime" in file_path.lower()
        ):
            return "python-runtime"
        else:
            return "general"

    def scan_docs(self, target_dir: str = "docs") -> list[str]:
        """Scans target documentation directory and returns all file paths relative to workspace_root."""
        abs_target = (
            Path(target_dir)
            if Path(target_dir).is_absolute()
            else (Path(self.workspace_root) / target_dir).resolve()
        )
        if not abs_target.exists():
            raise DomainException(f"Target directory does not exist: {target_dir}")

        result: list[str] = []
        for root, _, files in os.walk(abs_target):
            for file in files:
                file_abs = Path(root) / file
                rel_path = os.path.relpath(file_abs, self.workspace_root)
                result.append(rel_path)
        return result

    def validate_compliance(self, target_dir: str = "docs") -> ComplianceReport:
        """Audits target documentation directory for flat files and rule compliance."""
        abs_target = (
            Path(target_dir)
            if Path(target_dir).is_absolute()
            else (Path(self.workspace_root) / target_dir).resolve()
        )
        if not abs_target.exists():
            raise DomainException(f"Target directory does not exist: {target_dir}")

        violating: list[str] = []
        total = 0
        clean = 0

        for root, _, files in os.walk(abs_target):
            for file in files:
                total += 1
                file_abs = Path(root) / file
                rel_path = os.path.relpath(file_abs, self.workspace_root)

                # Check for absolute path format in relative path string representation
                if (
                    rel_path.startswith("C:")
                    or rel_path.startswith("D:")
                    or rel_path.startswith("E:")
                    or rel_path.startswith("/")
                ):
                    raise PathPolicyViolation(
                        f"Absolute path violation detected: {rel_path}"
                    )

                norm_root = Path(root).resolve()
                norm_target = abs_target.resolve()

                if (
                    norm_root == norm_target
                    and file.lower() != "readme.md"
                    and file != ".gitkeep"
                ):
                    violating.append(rel_path)
                else:
                    clean += 1

        score = int(clean / total * 100) if total > 0 else 100
        return ComplianceReport(
            total_files=total,
            clean_tracked_count=clean,
            violating_files=violating,
            compliance_score=score,
        )

    def dry_run_report(self, target_dir: str = "docs") -> ComplianceReport:
        """Generates dry-run compliance report."""
        return self.validate_compliance(target_dir=target_dir)

    def create_backup(
        self, backup_root: str = "_to_delete/semantic-docs-cleanup/backups"
    ) -> str:
        """Creates atomic directory backup prior to file migration."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target_backup = Path(self.workspace_root) / backup_root / f"docs_backup_{timestamp}"
        docs_dir = Path(self.workspace_root) / "docs"

        if docs_dir.exists():
            shutil.copytree(docs_dir, target_backup)
        else:
            target_backup.mkdir(parents=True, exist_ok=True)

        return os.path.relpath(target_backup, self.workspace_root)

    def backup(
        self, backup_root: str = "_to_delete/semantic-docs-cleanup/backups"
    ) -> str:
        """Alias for create_backup."""
        return self.create_backup(backup_root=backup_root)

    def move_to_semantic_folder(
        self,
        file_path: str,
        feature_family: str,
        stage: str = "general",
        dry_run: bool = True,
    ) -> str:
        """Calculates target semantic path and moves file if dry_run is False."""
        abs_src = (
            Path(file_path)
            if Path(file_path).is_absolute()
            else Path(self.workspace_root) / file_path
        )
        if not abs_src.exists():
            raise DomainException(f"Source file for move does not exist: {file_path}")

        filename = abs_src.name
        target_rel_dir = str(Path("docs") / "features" / feature_family / stage)
        target_abs_dir = Path(self.workspace_root) / target_rel_dir
        target_rel_file = str(Path(target_rel_dir) / filename)
        target_abs_file = Path(self.workspace_root) / target_rel_file

        if not dry_run:
            target_abs_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(abs_src, target_abs_file)

        return target_rel_file

    def apply_migration(
        self,
        dry_run: bool = True,
        feature_family: str | None = None,
        target_dir: str = "docs",
    ) -> MigrationSummary:
        """Executes physical move operations or records dry-run plan."""
        compliance = self.validate_compliance(target_dir=target_dir)

        if dry_run:
            return MigrationSummary(
                backup_path="dry-run-no-backup",
                files_moved=0,
                directories_created=0,
                errors=[],
                moved_files=[],
            )

        backup_path = self.create_backup()
        moved = 0
        dirs_created = 0
        errors: list[str] = []
        moved_files: list[str] = []

        created_dirs_set: set[Path] = set()

        for rel_file in compliance.violating_files:
            try:
                family = feature_family or self.classify_family(rel_file)
                target_rel_dir = str(Path("docs") / "features" / family / "general")
                target_abs_dir = Path(self.workspace_root) / target_rel_dir
                if not target_abs_dir.exists() and target_abs_dir not in created_dirs_set:
                    dirs_created += 1
                    created_dirs_set.add(target_abs_dir)

                dst_rel = self.move_to_semantic_folder(
                    file_path=rel_file,
                    feature_family=family,
                    stage="general",
                    dry_run=False,
                )
                moved += 1
                moved_files.append(dst_rel)
            except Exception as e:
                errors.append(f"Failed to move {rel_file}: {str(e)}")

        return MigrationSummary(
            backup_path=backup_path,
            files_moved=moved,
            directories_created=dirs_created,
            errors=errors,
            moved_files=moved_files,
        )

    def run(
        self,
        dry_run: bool = True,
        feature_family: str | None = None,
        target_dir: str = "docs",
    ) -> MigrationSummary:
        """Default entry point for running cleanup service. Safe mode default dry_run=True."""
        return self.apply_migration(
            dry_run=dry_run, feature_family=feature_family, target_dir=target_dir
        )
