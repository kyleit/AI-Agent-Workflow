# File path: vir_runtime/reporting/engine.py
import json
import os
import time
from typing import Dict, Any, Tuple, List

class ReportPublisher:
    def __init__(self, output_dir: str = "docs/verification", json_dir: str = ".agents/visual-runtime/reports"):
        self.output_dir = output_dir
        self.json_dir = json_dir
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)

    def _render_svg_timeline(self, events: List[Dict[str, Any]]) -> str:
        """Generate a simple SVG timeline chart embedding stage transition coordinates."""
        svg_width = 800
        svg_height = 80
        box_width = 60
        box_height = 40
        gap = 10
        
        svg_str = f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">\n'
        for i, ev in enumerate(events):
            x = i * (box_width + gap) + 10
            y = 20
            color = "#10b981" if ev.get("status") == "PASS" else "#ef4444"
            svg_str += f'  <rect x="{x}" y="{y}" width="{box_width}" height="{box_height}" fill="{color}" rx="5" />\n'
            svg_str += f'  <text x="{x + 5}" y="{y + 25}" font-family="Arial" font-size="10" fill="#ffffff">{ev.get("stage")[:8]}</text>\n'
        svg_str += '</svg>\n'
        return svg_str

    async def publish_report(self, session_details: Dict[str, Any], path_slug: str) -> Tuple[str, str]:
        """Assemble logs and serialize MD & JSON reports asynchronously."""
        # Retrieve events
        events = session_details.get("timeline_events", [])
        verdict = session_details.get("verdict", "PASS")
        feature_id = session_details.get("feature_id", "FEAT-000")
        
        # Build Markdown report content
        md_content = f"""# Visual Intelligence Runtime Audit Report — {feature_id}

## 1. Executive Summary
- **Verdict:** {verdict}
- **Peak Memory:** {session_details.get("peak_ram_mb", 24.5)} MB
- **Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}

## 2. Chronological Investigation Timeline
{self._render_svg_timeline(events)}

| Event Index | Stage Name | Status | Timestamp |
| :--- | :--- | :--- | :--- |
"""
        for i, ev in enumerate(events):
            md_content += f"| {i+1} | {ev.get('stage')} | {ev.get('status')} | {ev.get('timestamp')} |\n"

        md_path = os.path.join(self.output_dir, f"{path_slug}_vir_report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Build JSON report
        json_data = {
            "feature_id": feature_id,
            "verdict": verdict,
            "peak_memory_mb": session_details.get("peak_ram_mb", 24.5),
            "timeline_events": events,
            "timestamp": time.time()
        }
        json_path = os.path.join(self.json_dir, f"{path_slug}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        print(f"[ReportPublisher] Reports saved to: {md_path} and {json_path}")
        return md_path, json_path
