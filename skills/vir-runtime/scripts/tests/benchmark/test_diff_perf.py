import time
import io
import pytest
from PIL import Image, ImageDraw, ImageChops


def generate_test_image_bytes(width: int = 1920, height: int = 1080, color: str = "white") -> bytes:
    """Helper creating raw PNG bytes for a test HD image."""
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([100, 100, 300, 300], fill="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def compute_pixel_diff_latency(img_bytes1: bytes, img_bytes2: bytes) -> float:
    """Computes pixel diff latency in milliseconds using Pillow.

    1. Start timer = time.perf_counter()
    2. Open image1 and image2 using Image.open()
    3. Convert to RGB mode
    4. Compute difference using ImageChops.difference(img1, img2)
    5. Measure elapsed = (time.perf_counter() - start) * 1000.0
    6. Return elapsed latency in ms
    """
    start = time.perf_counter()
    img1 = Image.open(io.BytesIO(img_bytes1)).convert("RGB")
    img2 = Image.open(io.BytesIO(img_bytes2)).convert("RGB")
    _diff = ImageChops.difference(img1, img2)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms


def test_visual_diff_performance_under_150ms() -> None:
    """Verifies visual diff calculation on 1080p HD images executes < 150ms."""
    img1 = generate_test_image_bytes(1920, 1080, "white")
    img2 = generate_test_image_bytes(1920, 1080, "gray")

    # Warmup
    _ = compute_pixel_diff_latency(img1, img2)

    # Benchmark run
    latencies = [compute_pixel_diff_latency(img1, img2) for _ in range(5)]
    avg_latency = sum(latencies) / len(latencies)

    print(f"\n[BENCHMARK] 1080p Image Visual Diff Latency: {avg_latency:.2f} ms")
    assert avg_latency < 150.0, f"Visual Diff latency {avg_latency:.2f} ms exceeds 150ms SLA"
