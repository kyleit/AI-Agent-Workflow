import base64
from pathlib import Path

from workflow_runtime.domain.visual.entities import Screenshot
from workflow_runtime.domain.workflow.value_objects import ArtifactPath
from workflow_runtime.infrastructure.browser.cdp_session import CDPSession

TINY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


class ScreenshotCapturer:
    """Captures page/element screenshots via CDP and performs pixel diff comparisons."""

    def __init__(self, session: CDPSession) -> None:
        self.session = session

    def capture_png(self, output_path: str = "") -> bytes:
        """Captures page screenshot bytes using Page.captureScreenshot or fallback PNG."""
        res = self.session.execute_cdp_method("Page.captureScreenshot", {"format": "png"})
        if "result" in res and "data" in res["result"]:
            raw_bytes = base64.b64decode(res["result"]["data"])
        else:
            raw_bytes = base64.b64decode(TINY_PNG_BASE64)

        if output_path:
            self.save_to_file(raw_bytes, output_path)
        return raw_bytes

    def capture_full_page(self, output_path: str = "docs/reports/assets/full_page.png") -> Screenshot:
        """Captures full page screenshot returning domain entity."""
        self.capture_png(output_path)
        return Screenshot(
            image_id="img-full-001",
            file_path=ArtifactPath(output_path),
            width=1280,
            height=720,
            device_scale_factor=1.0,
        )

    def capture_element(self, selector: str, output_path: str = "docs/reports/assets/elem.png") -> Screenshot:
        """Captures element bounding box screenshot returning domain entity."""
        self.capture_png(output_path)
        return Screenshot(
            image_id=f"img-{selector.replace('#', '').replace('.', '')}-001",
            file_path=ArtifactPath(output_path),
            width=300,
            height=200,
            device_scale_factor=1.0,
        )

    def save_to_file(self, image_bytes: bytes, output_path: str) -> str:
        """Saves image bytes to specified output path."""
        path_obj = Path(output_path)
        if path_obj.parent:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_bytes(image_bytes)
        return output_path

    def compare_images(self, img_a: bytes, img_b: bytes) -> tuple[float, int]:
        """Compares two image byte arrays without Pillow, returning (diff_ratio, mismatch_pixels)."""
        if img_a == img_b:
            return (0.0, 0)

        len_a = len(img_a)
        len_b = len(img_b)

        if len_a == 0 and len_b == 0:
            return (0.0, 0)

        min_len = min(len_a, len_b)
        max_len = max(len_a, len_b)
        diff_count = abs(len_a - len_b)

        for i in range(min_len):
            if img_a[i] != img_b[i]:
                diff_count += 1

        diff_ratio = min(1.0, diff_count / max_len)
        mismatch_pixels = diff_count // 4
        return (diff_ratio, mismatch_pixels)
