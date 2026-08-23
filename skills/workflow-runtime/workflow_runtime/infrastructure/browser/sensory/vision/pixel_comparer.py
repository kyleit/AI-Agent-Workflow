# File path: vir_runtime/sensory/vision/pixel_comparer.py
from __future__ import annotations

import io
from typing import Any, cast

try:
    from PIL import Image, ImageChops
except ImportError:
    Image = None
    ImageChops = None


class PixelComparer:
    def compare(
        self,
        current_png: bytes,
        baseline_png: bytes,
        ignore_masks: list[tuple[int, int, int, int]] | None = None
    ) -> tuple[float, bytes]:
        """Apply structural pixel comparison on page screenshots."""
        if Image is None or ImageChops is None:
            diff_ratio = 0.0 if current_png == baseline_png else 1.0
            return diff_ratio, b"diff_bytes"

        try:
            img_curr = Image.open(io.BytesIO(current_png))
            img_base = Image.open(io.BytesIO(baseline_png))
        except Exception:
            diff_ratio = 0.0 if current_png == baseline_png else 1.0
            return diff_ratio, b"diff_bytes"

        if img_curr.size != img_base.size:
            return 1.0, b"size_mismatch_diff"

        if ignore_masks:
            img_curr = img_curr.copy()
            img_base = img_base.copy()
            for mask in ignore_masks:
                x, y, w, h = mask
                black_box = Image.new("RGBA", (w, h), (0, 0, 0, 255))
                img_curr.paste(black_box, (x, y))
                img_base.paste(black_box, (x, y))

        diff = ImageChops.difference(img_curr, img_base)

        diff_pixels = 0
        total_pixels = img_curr.size[0] * img_curr.size[1]

        raw_data: Any = diff.getdata()
        for pixel in raw_data:
            if isinstance(pixel, (tuple, list)):
                p_tuple = cast(tuple[int, ...], pixel)
                if sum(p_tuple[:3]) > 10:
                    diff_pixels += 1

        diff_ratio = diff_pixels / total_pixels if total_pixels > 0 else 0.0

        diff_io = io.BytesIO()
        diff.save(diff_io, format="PNG")

        return diff_ratio, diff_io.getvalue()


__all__ = ["PixelComparer"]
