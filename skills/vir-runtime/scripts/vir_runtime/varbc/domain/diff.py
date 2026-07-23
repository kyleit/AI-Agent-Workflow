from pydantic import BaseModel, Field, ConfigDict


class VisualDiff(BaseModel):
    """Represents the quantitative visual diff result between an observation and a baseline."""

    model_config = ConfigDict(frozen=True)

    baseline_id: str = Field(
        ..., description="Target UIBaseline component identifier"
    )
    observation_id: str = Field(
        ..., description="Target VisualObservation identifier"
    )
    diff_score: float = Field(
        ...,
        description="Normalized pixel difference percentage (0.0 = identical, 1.0 = completely different)",
    )
    diff_image_path: str = Field(
        default="",
        description="Relative path to generated diff heat-map PNG image",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="List of detected visual discrepancy summaries",
    )
