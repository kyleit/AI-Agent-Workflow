import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from validation_runtime_engine import ValidationEngine

def test_validation_engine_ac():
    engine = ValidationEngine()
    engine.register_criteria("REQ-01", "tests/test_foo.py")
    
    assert engine.verify_ac("REQ-01", True) is True
    evidence = engine.compile_evidence()
    assert evidence["compliant"] is True
