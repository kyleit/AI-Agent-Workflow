# File path: tests/unit/test_observers.py
import unittest
from vir_runtime.observers.accessibility.engine import AccessibilityObserver
from vir_runtime.observers.responsive.engine import ResponsiveObserver

class TestObservers(unittest.IsolatedAsyncioTestCase):
    async def test_a11y_observer(self):
        obs = AccessibilityObserver()
        findings = await obs.run_a11y_scan()
        
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].violation_type, "missing_alt")
        self.assertEqual(findings[0].severity, "SHOULD")

    async def test_responsive_observer(self):
        obs = ResponsiveObserver(breakpoints=[375])
        findings = await obs.verify_responsive_layouts()
        
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].violation_type, "overflow_spill")
        self.assertEqual(findings[0].viewport_width, 375)

    async def test_invalid_breakpoint(self):
        obs = ResponsiveObserver(breakpoints=[-10])
        with self.assertRaises(ValueError):
            await obs.verify_responsive_layouts()

if __name__ == "__main__":
    unittest.main()
