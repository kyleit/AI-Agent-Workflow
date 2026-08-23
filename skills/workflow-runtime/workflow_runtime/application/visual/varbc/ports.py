from abc import ABC, abstractmethod
from typing import Optional

from workflow_runtime.domain.visual.varbc.action import ActionPlan, AgentAction
from workflow_runtime.domain.visual.varbc.baseline import UIBaseline
from workflow_runtime.domain.visual.varbc.observation import VisualObservation
from workflow_runtime.domain.visual.varbc.report import VARReport


class CDPClientPort(ABC):
    """Abstract Port for Chrome DevTools Protocol browser automation."""

    @abstractmethod
    async def navigate(self, url: str) -> None:
        """Navigates browser to target URL."""

    @abstractmethod
    async def capture_screenshot(self, selector: str = "body") -> bytes:
        """Captures element or page screenshot as PNG bytes."""

    @abstractmethod
    async def get_dom_snapshot(self) -> str:
        """Captures DOM HTML content snapshot."""

    @abstractmethod
    async def get_console_errors(self) -> list[str]:
        """Retrieves captured console error messages."""

    @abstractmethod
    async def execute_action(self, action: AgentAction) -> None:
        """Executes browser action against active page."""

    @abstractmethod
    async def close(self) -> None:
        """Closes browser session and WebSocket connection."""


class BaselineRepositoryPort(ABC):
    """Abstract Port for UI baseline storage operations."""

    @abstractmethod
    async def save_baseline(self, baseline: UIBaseline, image_bytes: bytes) -> None:
        """Persists baseline metadata and PNG bytes."""

    @abstractmethod
    async def get_baseline(self, component_id: str) -> Optional[UIBaseline]:
        """Retrieves baseline metadata by component_id."""

    @abstractmethod
    async def get_baseline_image(self, component_id: str) -> Optional[bytes]:
        """Retrieves raw PNG reference image bytes."""


class ReportRepositoryPort(ABC):
    """Abstract Port for VAR report storage operations."""

    @abstractmethod
    async def save_report(self, report: VARReport) -> None:
        """Persists VARReport document and formatted Markdown summary."""

    @abstractmethod
    async def get_report(self, report_id: str) -> Optional[VARReport]:
        """Loads VARReport document by report_id."""


class MemoryManagerPort(ABC):
    """Abstract Port for visual memory state caching."""

    @abstractmethod
    async def get_context(self, component_id: str) -> Optional[UIBaseline]:
        """Retrieves cached baseline context."""

    @abstractmethod
    async def update_memory(self, baseline: UIBaseline) -> None:
        """Updates in-memory baseline context cache."""


class LLMProviderPort(ABC):
    """Abstract Port for Vision LLM reasoning and action planning."""

    @abstractmethod
    async def plan_action(
        self, observation: VisualObservation, goal: str
    ) -> ActionPlan:
        """Generates ActionPlan from visual observation and user goal."""
