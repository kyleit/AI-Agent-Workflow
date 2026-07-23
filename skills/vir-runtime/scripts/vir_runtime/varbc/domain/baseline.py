from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


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
        default_factory=datetime.utcnow,
        description="UTC timestamp when baseline was last updated",
    )
