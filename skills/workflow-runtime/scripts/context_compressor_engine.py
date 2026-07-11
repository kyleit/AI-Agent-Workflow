# context_compressor_engine.py
import re

class ContextCompressorEngine:
    """
    FEAT-110: Cognitive Intelligence & Optimization
    Compresses prompt contexts and error logs prior to LLM dispatch.
    """
    def compress_logs(self, logs: list[str]) -> list[str]:
        # Leave last 2 logs unchanged, summarize or trim earlier ones
        if len(logs) <= 2:
            return logs
            
        compressed = ["[Context Compressed Summary]"]
        # Keep only lines containing error details or traceback markers in older logs
        for log in logs[:-2]:
            if "error" in log.lower() or "exception" in log.lower() or "fail" in log.lower():
                compressed.append(log)
                
        # Append the last two entries intact
        compressed.extend(logs[-2:])
        return compressed
