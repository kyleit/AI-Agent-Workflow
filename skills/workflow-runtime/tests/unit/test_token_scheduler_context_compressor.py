import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from token_scheduler_context_compressor import ContextCompressor

def test_context_compressor():
    compressor = ContextCompressor()
    logs = ["log1", "log2", "log3", "log4"]
    res = compressor.compress_logs(logs)
    assert res[0] == "Summary of past logs"
    assert len(res) == 3
