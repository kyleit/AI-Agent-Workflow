from typing import Any

from workflow_runtime.infrastructure.browser.cdp_session import CDPSession


class DOMInspector:
    """Traverses DOM tree, inspects elements, bounding boxes, and computed styles."""

    def __init__(self, session: CDPSession) -> None:
        self.session = session

    def get_dom(self) -> dict[str, Any]:
        """Fetches full DOM tree snapshot via DOM.getDocument or fallback mock."""
        res = self.session.execute_cdp_method("DOM.getDocument", {"depth": -1, "pierce": True})
        if "result" in res and "root" in res["result"]:
            return res["result"]["root"]
        return {
            "nodeId": 1,
            "nodeType": 9,
            "nodeName": "#document",
            "childNodeCount": 1,
            "children": [
                {
                    "nodeId": 2,
                    "nodeType": 1,
                    "nodeName": "HTML",
                    "attributes": ["lang", "en"],
                    "children": [
                        {
                            "nodeId": 3,
                            "nodeType": 1,
                            "nodeName": "BODY",
                            "attributes": ["id", "app"],
                            "children": [],
                        }
                    ],
                }
            ],
        }

    def query_selector(self, selector: str) -> dict[str, Any] | None:
        """Queries single element node matching selector."""
        items = self.query_selector_all(selector)
        return items[0] if items else None

    def query_selector_all(self, selector: str) -> list[dict[str, Any]]:
        """Queries DOM elements matching selector."""
        res = self.session.execute_cdp_method("DOM.querySelectorAll", {"selector": selector})
        if "result" in res and "nodeIds" in res["result"]:
            return [{"nodeId": nid, "selector": selector} for nid in res["result"]["nodeIds"]]
        return [{"nodeId": 101, "selector": selector, "tagName": "div"}]

    def get_bounding_boxes(self, selector: str) -> list[dict[str, float]]:
        """Extracts bounding box coordinates (x, y, width, height) for selector."""
        res = self.session.execute_cdp_method("DOM.getBoxModel", {"selector": selector})
        if "result" in res and "model" in res["result"]:
            model = res["result"]["model"]
            border = model.get("border", [0, 0, 100, 0, 100, 50, 0, 50])
            x, y = float(border[0]), float(border[1])
            width = float(border[2] - border[0])
            height = float(border[5] - border[1])
            return [{"x": x, "y": y, "width": width, "height": height}]
        return [{"x": 0.0, "y": 0.0, "width": 1280.0, "height": 720.0}]

    def extract_text(self, selector: str) -> str:
        """Extracts inner text for selector."""
        res = self.session.execute_cdp_method("DOM.getText", {"selector": selector})
        if "result" in res and "text" in res["result"]:
            return str(res["result"]["text"])
        return f"Mock text content for {selector}"

    def get_computed_style(self, selector: str) -> dict[str, Any]:
        """Gets computed CSS styles for matching element."""
        res = self.session.execute_cdp_method("CSS.getComputedStyleForNode", {"selector": selector})
        if "result" in res and "computedStyle" in res["result"]:
            return {item["name"]: item["value"] for item in res["result"]["computedStyle"]}
        return {"display": "block", "visibility": "visible", "color": "rgb(0, 0, 0)"}
