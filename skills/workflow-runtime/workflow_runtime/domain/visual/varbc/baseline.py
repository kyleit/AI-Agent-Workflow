from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class UIBaseline(BaseModel):
    """Represents an approved gold-standard visual baseline for a UI component."""

    model_config = ConfigDict(frozen=True)

    component_id: str = Field(
        ..., description="Unique UI component or page identifier"
    )
    baseline_image_path: str = Field(
        ..., description="Relative path to gold-standard reference PNG image"
    )
    expected_layout: str = Field(
        default="", description="JSON or description of expected layout elements"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when baseline was last updated",
    )
