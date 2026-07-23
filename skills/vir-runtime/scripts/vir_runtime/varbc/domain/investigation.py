from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class HypothesisStatus(str, Enum):
    """Evaluation status for RCA hypothesis."""

    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    PENDING = "pending"


class Hypothesis(BaseModel):
    """Plausible root cause statement evaluated by RCA engine."""

    model_config = ConfigDict(frozen=True)

    statement: str = Field(
        ..., description="Hypothesis statement explaining visual issue"
    )
    status: HypothesisStatus = Field(
        default=HypothesisStatus.PENDING, description="Current evaluation status"
    )
    evidence: list[str] = Field(
        default_factory=list, description="Supporting evidence items"
    )


class Investigation(BaseModel):
    """Root Cause Analysis (RCA) investigation state."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique investigation identifier")
    hypotheses: list[Hypothesis] = Field(
        default_factory=list, description="List of evaluated hypotheses"
    )
    conclusion: str = Field(default="", description="Final RCA conclusion")
    confidence: float = Field(
        default=0.0, description="RCA confidence score (0.0 to 1.0)"
    )
    completed: bool = Field(
        default=False, description="True if investigation completed"
    )
