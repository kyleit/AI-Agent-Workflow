"""Keep the owner approval boundary small, explicit, and hash-bound."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workflow_runtime.application.workflow.blueprint_validation_loop import (
        BlueprintValidationResult,
    )


@dataclass(frozen=True)
class ApprovalPresentation:
    work_item_id: str
    blueprint_path: str
    blueprint_sha256: str
    source_snapshot: str
    validation_result_id: str
    title: str
    summary: str
    choices: tuple[str, str] = ("Approve implementation", "Cancel")


@dataclass(frozen=True)
class ApprovalResumeResult:
    resumed: bool
    status: str
    reason: str


class ApprovalOrchestrator:
    """Translate one validated Blueprint into one user decision boundary.

    The orchestrator does not authorize writes. It only makes sure a response
    still refers to the exact Blueprint that was presented to the owner.
    """

    def prepare_user_approval(
        self,
        work_item_id: str,
        blueprint_path: Path,
        validation: BlueprintValidationResult,
    ) -> ApprovalPresentation:
        if validation.status != "APPROVAL_READY":
            raise ValueError("approval_requires_approval_ready_validation")
        if not blueprint_path.is_file():
            raise ValueError("approval_requires_existing_blueprint")

        current_hash = self._hash(blueprint_path)
        if validation.blueprint_sha256 != current_hash:
            raise ValueError("approval_validation_hash_is_stale")
        return ApprovalPresentation(
            work_item_id=work_item_id,
            blueprint_path=blueprint_path.as_posix(),
            blueprint_sha256=current_hash,
            source_snapshot=validation.source_snapshot,
            validation_result_id=validation.result_id,
            title="Approve implementation",
            summary="Blueprint and validation gates are ready for implementation.",
        )

    def resume_after_approval(
        self,
        choice: str,
        presentation: ApprovalPresentation,
    ) -> ApprovalResumeResult:
        current_hash = self._hash(Path(presentation.blueprint_path))
        if current_hash != presentation.blueprint_sha256:
            return ApprovalResumeResult(
                False,
                "STALE_PRESENTATION",
                "blueprint_hash_changed;_validation_and_approval_must_restart",
            )

        normalized = choice.strip().casefold()
        if normalized == presentation.choices[0].casefold():
            return ApprovalResumeResult(
                True,
                "IMPLEMENTATION_ENTRY_PENDING",
                "approval_bound_to_current_blueprint",
            )
        if normalized == presentation.choices[1].casefold():
            return ApprovalResumeResult(False, "CANCELLED", "owner_cancelled")
        return ApprovalResumeResult(False, "INVALID_CHOICE", "choice_not_in_presentation")

    def handle_adapter_result(
        self,
        adapter_status: str,
        presentation: ApprovalPresentation,
    ) -> ApprovalResumeResult:
        """Map prompt adapters without turning unavailable UI into approval."""
        if adapter_status == "PROMPT_UNAVAILABLE":
            return ApprovalResumeResult(
                False,
                "PROMPT_UNAVAILABLE",
                "native_and_bridge_prompt_unavailable;_one_bound_chat_fallback_allowed",
            )
        return self.resume_after_approval(adapter_status, presentation)

    @staticmethod
    def _hash(path: Path) -> str:
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise ValueError("approval_blueprint_unreadable") from exc


__all__ = ["ApprovalOrchestrator", "ApprovalPresentation", "ApprovalResumeResult"]
