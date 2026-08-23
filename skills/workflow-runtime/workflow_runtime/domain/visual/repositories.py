from typing import Protocol

from workflow_runtime.domain.visual.entities import (A11YReport, Screenshot,
                                                     VisualDiff)


class IVisualRepository(Protocol):
    def save_screenshot(self, screenshot: Screenshot) -> None:
        ...

    def get_screenshot(self, image_id: str) -> Screenshot:
        ...

    def save_visual_diff(self, diff: VisualDiff) -> None:
        ...

    def save_a11y_report(self, report: A11YReport) -> None:
        ...
