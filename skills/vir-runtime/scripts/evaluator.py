"""Legacy wrapper script for quality evaluation."""

import os
import sys
import warnings
import asyncio
from typing import Dict, Any

# Ensure script directory is in sys.path for vir_runtime package imports
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from vir_runtime.varbc.application.verifier import VARVerifier


def evaluate_quality(score_diff: float, score_layout: float, score_text: float) -> Dict[str, Any]:
    """Legacy function wrapper forwarding quality checks to VARVerifier."""
    warnings.warn(
        "evaluator.py is deprecated; please use 'python var_dispatch.py check' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    verifier = VARVerifier()
    weighted = verifier.compute_weighted_score(score_diff, score_layout, score_text)
    return {"weighted_score": weighted, "passed": weighted >= 85.0}
