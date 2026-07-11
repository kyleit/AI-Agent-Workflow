# File path: vir_runtime/sensory/vision/pixel_comparer.py
import io
from typing import Tuple, List, Optional
try:
    from PIL import Image, ImageChops
except ImportError:
    Image = None

class PixelComparer:
    def compare(
        self, 
        current_png: bytes, 
        baseline_png: bytes, 
        ignore_masks: Optional[List[Tuple[int, int, int, int]]] = None
    ) -> Tuple[float, bytes]:
        """Apply structural pixel comparison on page screenshots."""
        # Safeguard for mock inputs in testing
        if not Image:
            # Fallback when Pillow is missing
            diff_ratio = 0.0 if current_png == baseline_png else 1.0
            return diff_ratio, b"diff_bytes"
            
        try:
            img_curr = Image.open(io.BytesIO(current_png))
            img_base = Image.open(io.BytesIO(baseline_png))
        except Exception:
            # Fallback if bytes are mock strings (not real images)
            diff_ratio = 0.0 if current_png == baseline_png else 1.0
            return diff_ratio, b"diff_bytes"

        # Check resolution matches
        if img_curr.size != img_base.size:
            # Size mismatch
            return 1.0, b"size_mismatch_diff"

        # Apply ignore masks (fill ignore areas with black in both images)
        if ignore_masks:
            img_curr = img_curr.copy()
            img_base = img_base.copy()
            for mask in ignore_masks:
                # mask is (x, y, w, h)
                x, y, w, h = mask
                black_box = Image.new("RGBA", (w, h), (0, 0, 0, 255))
                img_curr.paste(black_box, (x, y))
                img_base.paste(black_box, (x, y))

        # Compute absolute difference
        diff = ImageChops.difference(img_curr, img_base)
        
        # Calculate percentage of different pixels
        # getdata returns list of pixel tuples
        diff_pixels = 0
        total_pixels = img_curr.size[0] * img_curr.size[1]
        
        for pixel in diff.getdata():
            # Check if color difference is above threshold
            # pixel is typically (R, G, B, A) or (R, G, B)
            if sum(pixel[:3]) > 10: # threshold of color difference
                diff_pixels += 1
                
        diff_ratio = diff_pixels / total_pixels
        
        # Save diff image to bytes
        diff_io = io.BytesIO()
        diff.save(diff_io, format="PNG")
        
        return diff_ratio, diff_io.getvalue()
