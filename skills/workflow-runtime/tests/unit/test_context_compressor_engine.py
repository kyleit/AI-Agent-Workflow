import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from context_compressor_engine import ContextCompressorEngine

def test_context_compressor_engine_trimming():
    engine = ContextCompressorEngine()
    logs = [
        "info: normal log line 1",
        "error: critical database connection failed",
        "info: normal log line 2",
        "info: final log line 3",
        "info: final log line 4"
    ]
    
    res = engine.compress_logs(logs)
    
    # Assert last two entries remain untouched
    assert res[-2] == "info: final log line 3"
    assert res[-1] == "info: final log line 4"
    
    # Assert informational old logs are removed, but critical error logs are preserved
    assert "info: normal log line 1" not in res
    assert "error: critical database connection failed" in res
    assert res[0] == "[Context Compressed Summary]"
