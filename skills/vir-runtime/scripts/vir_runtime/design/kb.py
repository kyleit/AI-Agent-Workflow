# File path: vir_runtime/design/kb.py
import os
import yaml
import json
from typing import Dict, Any

class DesignKnowledgeBase:
    def __init__(self, rules_path: str = "rules.yaml", tokens_path: str = "tokens.json"):
        self.rules_path = rules_path
        self.tokens_path = tokens_path
        self.rules: Dict[str, Any] = {}
        self.tokens: Dict[str, Any] = {}
        self._load_kb()

    def _load_kb(self) -> None:
        # Load rules
        if os.path.exists(self.rules_path):
            with open(self.rules_path, "r", encoding="utf-8") as f:
                self.rules = yaml.safe_load(f) or {}
        else:
            # Default fallback rules
            self.rules = {
                "typography": {
                    "font-size": {
                        "allowed": ["12px", "14px", "16px", "20px", "24px"],
                        "severity": "MUST"
                    }
                },
                "colors": {
                    "primary": {
                        "allowed": ["#3b82f6", "#1d4ed8", "#ffffff", "#000000"],
                        "severity": "MUST"
                    }
                }
            }

        # Load tokens
        if os.path.exists(self.tokens_path):
            with open(self.tokens_path, "r", encoding="utf-8") as f:
                self.tokens = json.load(f) or {}
        else:
            # Default fallback tokens
            self.tokens = {
                "font-size": ["12px", "14px", "16px", "20px", "24px"],
                "color": ["#3b82f6", "#1d4ed8", "#ffffff", "#000000"]
            }

    def lookup_rule(self, category: str, rule_name: str) -> Dict[str, Any]:
        """Expose lookup interfaces to query compliance rules."""
        return self.rules.get(category, {}).get(rule_name, {})

    def check_token_compliance(self, token_type: str, value: Any) -> bool:
        """Check if a CSS style value complies with the design system tokens."""
        allowed_tokens = self.tokens.get(token_type, [])
        return value in allowed_tokens
