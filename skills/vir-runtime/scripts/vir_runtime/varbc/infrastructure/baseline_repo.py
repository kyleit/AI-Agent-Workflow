import os
import json
from typing import Optional
from vir_runtime.varbc.domain.baseline import UIBaseline
from vir_runtime.varbc.application.ports import BaselineRepositoryPort
from vir_runtime.varbc.domain.errors import RepositoryIOError


class FileBaselineRepo(BaselineRepositoryPort):
    """File-system based storage adapter for UIBaseline records and PNG reference images."""

    def __init__(self, baselines_dir: str = ".agents/state/var/baselines") -> None:
        """Initializes repository with disk target directory."""
        self._dir = baselines_dir
        os.makedirs(self._dir, exist_ok=True)

    async def save_baseline(self, baseline: UIBaseline, image_bytes: bytes) -> None:
        """Saves baseline metadata JSON and reference image PNG to disk.

        1. Path json_path = os.path.join(self._dir, f"{baseline.component_id}.json")
        2. Path img_path = os.path.join(self._dir, f"{baseline.component_id}.png")
        3. Write baseline.model_dump_json() to json_path.
        4. Write image_bytes to img_path.
        """
        try:
            json_path = os.path.join(self._dir, f"{baseline.component_id}.json")
            img_path = os.path.join(self._dir, f"{baseline.component_id}.png")

            with open(json_path, "w", encoding="utf-8") as f:
                f.write(baseline.model_dump_json(indent=2))

            with open(img_path, "wb") as f:
                f.write(image_bytes)
        except Exception as e:
            raise RepositoryIOError(
                f"Failed to save baseline '{baseline.component_id}': {e}"
            ) from e

    async def get_baseline(self, component_id: str) -> Optional[UIBaseline]:
        """Retrieves baseline metadata from disk by component_id.

        1. Path json_path = os.path.join(self._dir, f"{component_id}.json")
        2. If not os.path.exists(json_path), return None.
        3. Read JSON content, parse with UIBaseline.model_validate_json(content).
        4. Return UIBaseline instance.
        """
        json_path = os.path.join(self._dir, f"{component_id}.json")
        if not os.path.exists(json_path):
            return None
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                content = f.read()
            return UIBaseline.model_validate_json(content)
        except Exception as e:
            raise RepositoryIOError(
                f"Failed to read baseline '{component_id}': {e}"
            ) from e

    async def get_baseline_image(self, component_id: str) -> Optional[bytes]:
        """Retrieves raw PNG bytes for a baseline image."""
        img_path = os.path.join(self._dir, f"{component_id}.png")
        if not os.path.exists(img_path):
            return None
        try:
            with open(img_path, "rb") as f:
                return f.read()
        except Exception as e:
            raise RepositoryIOError(
                f"Failed to read baseline image '{component_id}': {e}"
            ) from e
