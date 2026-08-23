import re
from dataclasses import dataclass

from workflow_runtime.domain.workflow.value_objects import ArtifactPath


@dataclass
class Version:
    major: int
    minor: int
    patch: int
    prerelease: str | None = None

    def bump_major(self) -> "Version":
        return Version(self.major + 1, 0, 0)

    def bump_minor(self) -> "Version":
        return Version(self.major, self.minor + 1, 0)

    def bump_patch(self) -> "Version":
        return Version(self.major, self.minor, self.patch + 1)

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            return f"{base}-{self.prerelease}"
        return base

    @staticmethod
    def parse(version_str: str) -> "Version":
        pattern = r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$"
        match = re.match(pattern, version_str.strip())
        if not match:
            raise ValueError(f"Invalid semver string: '{version_str}'")
        major, minor, patch, pre = match.groups()
        return Version(int(major), int(minor), int(patch), pre)


@dataclass
class ReleaseGate:
    gate_id: str
    auditor_pass: bool
    manager_pass: bool
    verification_report_path: ArtifactPath

    def is_approved(self) -> bool:
        return self.auditor_pass and self.manager_pass

    def grant_auditor_pass(self) -> None:
        self.auditor_pass = True

    def grant_manager_pass(self) -> None:
        self.manager_pass = True


@dataclass
class Artifact:
    artifact_id: str
    name: str
    path: ArtifactPath
    checksum_sha256: str
    size_bytes: int

    def verify_checksum(self, actual_hash: str) -> bool:
        return self.checksum_sha256.strip().lower() == actual_hash.strip().lower()
