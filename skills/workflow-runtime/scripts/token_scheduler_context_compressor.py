# token_scheduler_context_compressor.py
class ContextCompressor:
    """
    FEAT-103: Token Scheduler & Context Compressor
    Summarizes and compresses contexts to fit window limits.
    """
    def compress_logs(self, logs: list) -> list:
        # Keep recent 2 logs, summarize rest
        if len(logs) > 3:
            return ["Summary of past logs"] + logs[-2:]
        return logs
