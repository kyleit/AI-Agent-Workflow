# test_transcript_parsers.py
# Unit tests for ITranscriptParser interface across all 4 connectors (FEAT-049 Task 1.3 / Task 4.2)
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from connectors.antigravity import AntigravityConnector
from connectors.claude_code import ClaudeCodeConnector
from connectors.cursor import CursorConnector
from connectors.vscode_agents import VSCodeAgentsConnector
from fingerprint_engine import FingerprintEngine
from db import init_db_schema


class TestTranscriptParsers(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_parsers.db")
        self.conn = sqlite3.connect(self.db_path)
        init_db_schema(self.conn)
        self.fp_engine = FingerprintEngine(self.conn)

    def tearDown(self):
        self.conn.close()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_claude_code_parser(self):
        """ClaudeCodeConnector implements ITranscriptParser correctly."""
        conn = ClaudeCodeConnector()
        raw_line = {
            "type": "message",
            "conversation_id": "conv-claude",
            "request_id": "req-1",
            "model": "claude-3-5-sonnet",
            "timestamp": "2026-07-10T12:00:00Z",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "tool_tokens": 25,
                "thinking_tokens": 10
            }
        }

        # 1. Compute fingerprint
        fp = conn.compute_fingerprint(raw_line)
        self.assertEqual(len(fp), 64)

        # 2. Extract tool tokens
        self.assertEqual(conn.extract_tool_tokens(raw_line), 25)

        # 3. Parse with fingerprint
        record = conn.parse_with_fingerprint(raw_line, 120, self.fp_engine)
        self.assertIsNotNone(record)
        self.assertEqual(record.fingerprint, fp)
        self.assertEqual(record.tool_tokens, 25)
        self.assertEqual(record.transcript_offset, 120)
        # Verify tool_tokens is NOT added to total_tokens (total = input + output = 150)
        self.assertEqual(record.total_tokens, 150)

        # 4. Duplicate check should return None
        duplicate_record = conn.parse_with_fingerprint(raw_line, 120, self.fp_engine)
        self.assertIsNone(duplicate_record)

    def test_cursor_parser(self):
        """CursorConnector implements ITranscriptParser correctly."""
        conn = CursorConnector()
        raw_line = {
            "conversation_id": "conv-cursor",
            "request_id": "req-2",
            "model": "gpt-4o",
            "timestamp": "2026-07-10T12:05:00Z",
            "usage": {
                "input_tokens": 80,
                "output_tokens": 40,
                "tool_tokens": 10
            }
        }

        fp = conn.compute_fingerprint(raw_line)
        self.assertEqual(len(fp), 64)
        self.assertEqual(conn.extract_tool_tokens(raw_line), 10)

        record = conn.parse_with_fingerprint(raw_line, 240, self.fp_engine)
        self.assertIsNotNone(record)
        self.assertEqual(record.fingerprint, fp)
        self.assertEqual(record.tool_tokens, 10)
        self.assertEqual(record.total_tokens, 120)

        duplicate_record = conn.parse_with_fingerprint(raw_line, 240, self.fp_engine)
        self.assertIsNone(duplicate_record)

    def test_vscode_agents_parser(self):
        """VSCodeAgentsConnector implements ITranscriptParser correctly."""
        conn = VSCodeAgentsConnector()
        raw_line = {
            "conversation_id": "conv-vscode",
            "request_id": "req-3",
            "model": "copilot-gpt-4",
            "timestamp": "2026-07-10T12:10:00Z",
            "usage": {
                "promptTokens": 150,
                "completionTokens": 75,
                "tool_tokens": 5
            }
        }

        fp = conn.compute_fingerprint(raw_line)
        self.assertEqual(len(fp), 64)
        self.assertEqual(conn.extract_tool_tokens(raw_line), 5)

        record = conn.parse_with_fingerprint(raw_line, 360, self.fp_engine)
        self.assertIsNotNone(record)
        self.assertEqual(record.fingerprint, fp)
        self.assertEqual(record.tool_tokens, 5)
        self.assertEqual(record.total_tokens, 225)

        duplicate_record = conn.parse_with_fingerprint(raw_line, 360, self.fp_engine)
        self.assertIsNone(duplicate_record)

    def test_antigravity_parser(self):
        """AntigravityConnector implements ITranscriptParser correctly with state tracking."""
        conn = AntigravityConnector()
        
        # 1. USER_INPUT step (accumulates history chars)
        user_line = {
            "conversation_id": "conv-anti",
            "type": "USER_INPUT",
            "source": "USER",
            "content": "write code",
            "step_index": 0
        }
        res1 = conn.parse_with_fingerprint(user_line, 0, self.fp_engine)
        self.assertIsNone(res1)
        self.assertEqual(conn._accumulated_history_chars, 10)

        # 2. PLANNER_RESPONSE step (trigger record)
        model_line = {
            "conversation_id": "conv-anti",
            "type": "PLANNER_RESPONSE",
            "source": "MODEL",
            "content": "completed!",
            "thinking": "thought",
            "step_index": 1
        }
        res2 = conn.parse_with_fingerprint(model_line, 50, self.fp_engine)
        self.assertIsNotNone(res2)
        # input chars = 10 -> input tokens = 10 // 3 = 3
        # output chars = len("completed!") + len("thought") = 10 + 7 = 17 -> output tokens = 17 // 3 = 5
        self.assertEqual(res2.input_tokens, 3)
        self.assertEqual(res2.output_tokens, 5)
        self.assertEqual(res2.transcript_offset, 50)
        self.assertEqual(res2.accuracy_source, "estimated")

        # 3. Duplicate should return None
        res3 = conn.parse_with_fingerprint(model_line, 50, self.fp_engine)
        self.assertIsNone(res3)


if __name__ == '__main__':
    unittest.main()
