from typing import Protocol

from workflow_runtime.domain.release.entities import Artifact, ReleaseGate


class IReleaseRepository(Protocol):
    def get_release_gate(self, gate_id: str) -> ReleaseGate:
        ...

    def save_release_gate(self, gate: ReleaseGate) -> None:
        ...

    def record_artifact(self, artifact: Artifact) -> None:
        ...
