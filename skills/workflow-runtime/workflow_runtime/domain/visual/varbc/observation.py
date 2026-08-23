from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class VisualObservation(BaseModel):
    """Represents a visual capture of a web page at a specific timestamp."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique observation identifier")
    url: str = Field(..., description="Target web page URL")
    screenshot_path: str = Field(
        default="", description="Relative path to PNG screenshot file"
    )
    dom_snapshot: str = Field(
        default="", description="HTML DOM content snippet or tree summary"
    )
    console_errors: list[str] = Field(
        default_factory=list[str],
        description="List of captured browser console error logs",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of capture"
    )


__all__ = ["VisualObservation"]
