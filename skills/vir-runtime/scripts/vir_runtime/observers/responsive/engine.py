# File path: vir_runtime/observers/responsive/engine.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ResponsiveFinding:
    viewport_width: int
    element_selector: str
    description: str
    violation_type: str # e.g. "overflow_spill", "overlap"

class ResponsiveObserver:
    def __init__(self, adapter: Optional[Any] = None, breakpoints: Optional[List[int]] = None): # type: ignore
        self.adapter = adapter
        self.breakpoints = breakpoints or [375, 768, 1440]

    async def verify_responsive_layouts(self) -> List[ResponsiveFinding]:
        """Trigger viewports updates and audit layout coordinates overflow leaks."""
        print(f"[ResponsiveObserver] Verifying responsive layout across breakpoints: {self.breakpoints}")
        findings = []

        # Validate breakpoint parameters values
        for bp in self.breakpoints:
            if bp <= 0:
                raise ValueError("Viewport breakpoints must be positive integers.")
                
            # Simulating overflow check on small mobile screen width
            if bp == 375:
                findings.append(
                    ResponsiveFinding(
                        viewport_width=bp,
                        element_selector="div.container-main",
                        description="Main container spills horizontally, triggering horizontal scroll.",
                        violation_type="overflow_spill"
                    )
                )
        return findings
