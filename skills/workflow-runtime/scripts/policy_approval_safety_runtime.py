# policy_approval_safety_runtime.py
import os
import re

class PolicyEnforcementEngine:
    """
    FEAT-091: Policy & Safe Autonomy Runtime
    Intercepts commands and workspace access to guarantee sandbox boundaries.
    """
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)

    def is_path_safe(self, target_path: str) -> bool:
        target_abs = os.path.abspath(target_path)
        # Block write actions outside workspace root
        return target_abs.startswith(self.workspace_root)

    def is_command_safe(self, command: str) -> bool:
        # Block destructive command patterns and absolute path escapes
        forbidden_patterns = [
            r"rm\s+-rf\s+/",
            r"format\s+c:",
            r"mkfs",
            r">\s*/etc",
            r"del\s+/f\s+/q\s+c:\\"
        ]
        for pattern in forbidden_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False
        return True
