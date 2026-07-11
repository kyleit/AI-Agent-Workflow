# File path: tests/unit/test_pixel_comparer.py
import unittest
import io
from PIL import Image
from vir_runtime.sensory.vision.pixel_comparer import PixelComparer

class TestPixelComparer(unittest.TestCase):
    def setUp(self):
        self.comparer = PixelComparer()
        
        # Create image 1 (Red square 10x10)
        img1 = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        img1_io = io.BytesIO()
        img1.save(img1_io, format="PNG")
        self.img1_bytes = img1_io.getvalue()

        # Create image 2 (Red square 10x10 with 4 pixels colored blue)
        img2 = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        for x in range(2):
            for y in range(2):
                img2.putpixel((x, y), (0, 0, 255, 255))
        img2_io = io.BytesIO()
        img2.save(img2_io, format="PNG")
        self.img2_bytes = img2_io.getvalue()

    def test_compare_identical(self):
        diff_ratio, diff_img = self.comparer.compare(self.img1_bytes, self.img1_bytes)
        self.assertEqual(diff_ratio, 0.0)

    def test_compare_different(self):
        diff_ratio, diff_img = self.comparer.compare(self.img1_bytes, self.img2_bytes)
        # 4 out of 100 pixels are different -> diff_ratio should be 0.04
        self.assertAlmostEqual(diff_ratio, 0.04)

    def test_ignore_masks(self):
        # Ignore the top-left 2x2 area
        ignore_masks = [(0, 0, 2, 2)]
        diff_ratio, diff_img = self.comparer.compare(self.img1_bytes, self.img2_bytes, ignore_masks)
        # Because we ignored the blue pixels area, diff_ratio should be 0.0
        self.assertEqual(diff_ratio, 0.0)

if __name__ == "__main__":
    unittest.main()
