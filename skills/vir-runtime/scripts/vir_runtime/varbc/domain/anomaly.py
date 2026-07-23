from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class AnomalySeverity(str, Enum):
    """Severity classification for visual layout anomalies."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Anomaly(BaseModel):
    """Detected visual anomaly or layout contradiction."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique anomaly identifier")
    description: str = Field(..., description="Detailed description of visual flaw")
    severity: AnomalySeverity = Field(..., description="Severity level")
    evidence: str = Field(
        default="", description="DOM snippet or screenshot reference"
    )


class AnomalyRule(BaseModel):
    """Rule definition for detecting visual anomalies during RCA investigation."""

    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    pattern: str = Field(
        ..., description="Detection pattern or DOM selector target"
    )
    threshold: float = Field(
        default=0.1, description="Numerical threshold for triggering anomaly"
    )
    severity: AnomalySeverity = Field(
        default=AnomalySeverity.MEDIUM, description="Assigned severity"
    )
