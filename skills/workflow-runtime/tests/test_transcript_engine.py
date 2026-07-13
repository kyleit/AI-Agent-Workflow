"""
test_transcript_engine.py — FEAT-048 Phase 5 Task 5.1
Tests: IncrementalTranscriptReader (FR-03, FR-14)
Blueprint test matrix: test_transcript_engine.py
"""
import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def make_db_conn(tmpdir, name='test.db'):
    """Create a SQLite connection and initialize the FEAT-048 schema."""
    import db as db_module
    db_path = os.path.join(tmpdir, name)
    conn = sqlite3.connect(db_path)
    db_module.init_db_schema(conn)
    return conn


class TestIncrementalTranscriptReader(unittest.TestCase):
    """FR-03, FR-14: IncrementalTranscriptReader — incremental JSONL with cursor tracking."""

    def setUp(self):
        from transcript_engine import IncrementalTranscriptReader
        self.IncrementalTranscriptReader = IncrementalTranscriptReader
        self.tmpdir = tempfile.mkdtemp()
        self.conn = make_db_conn(self.tmpdir)

    def tearDown(self):
        self.conn.close()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_jsonl(self, filename, records):
        """Write JSONL file with given records, return path."""
        path = os.path.join(self.tmpdir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            for rec in records:
                f.write(json.dumps(rec) + '\n')
        return path

    def test_read_new_lines_returns_all_on_first_call(self):
        """FR-03: First read_new_lines() returns all lines from file."""
        records = [{'step_index': i, 'type': 'USER_INPUT', 'source': 'USER'} for i in range(5)]
        path = self._make_jsonl('transcript.jsonl', records)
        reader = self.IncrementalTranscriptReader(db_conn=self.conn)
        lines = reader.read_new_lines(path)
        self.assertEqual(len(lines), 5)

    def test_second_read_returns_empty_on_unchanged_file(self):
        """FR-14: Second read_new_lines() on unchanged file returns []."""
        records = [{'step_index': 0, 'type': 'USER_INPUT'}]
        path = self._make_jsonl('transcript2.jsonl', records)
        reader = self.IncrementalTranscriptReader(db_conn=self.conn)
        reader.read_new_lines(path)  # first read
        second = reader.read_new_lines(path)  # second read — unchanged
        self.assertEqual(len(second), 0)

    def test_second_read_returns_only_new_lines(self):
        """FR-03: Appending lines after first read returns only the new ones."""
        path = os.path.join(self.tmpdir, 'incremental.jsonl')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'step_index': 0}) + '\n')
            f.write(json.dumps({'step_index': 1}) + '\n')

        reader = self.IncrementalTranscriptReader(db_conn=self.conn)
        first = reader.read_new_lines(path)
        self.assertEqual(len(first), 2)

        # Append two more lines
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'step_index': 2}) + '\n')
            f.write(json.dumps({'step_index': 3}) + '\n')

        second = reader.read_new_lines(path)
        self.assertEqual(len(second), 2)
        self.assertEqual(second[0][0].get('step_index'), 2)
        self.assertEqual(second[1][0].get('step_index'), 3)

    def test_skips_malformed_json_lines(self):
        """FR-03: Malformed JSON lines are skipped without raising."""
        path = os.path.join(self.tmpdir, 'malformed.jsonl')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('{"valid": true}\n')
            f.write('NOT VALID JSON {{{{\n')
            f.write('{"also_valid": 1}\n')

        reader = self.IncrementalTranscriptReader(db_conn=self.conn)
        lines = reader.read_new_lines(path)
        # Only 2 valid lines should be returned
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0][0].get('valid'), True)
        self.assertEqual(lines[1][0].get('also_valid'), 1)

    def test_reset_clears_cursor(self):
        """reset() forces full re-read on next call."""
        records = [{'step_index': 0}, {'step_index': 1}]
        path = self._make_jsonl('reset.jsonl', records)

        reader = self.IncrementalTranscriptReader(db_conn=self.conn)
        reader.read_new_lines(path)  # read all
        reader.reset(path)           # reset cursor
        lines = reader.read_new_lines(path)  # should read all again
        self.assertEqual(len(lines), 2)

    def test_nonexistent_file_returns_empty(self):
        """read_new_lines() on non-existent file returns [] without raising."""
        reader = self.IncrementalTranscriptReader(db_conn=self.conn)
        result = reader.read_new_lines('/nonexistent/path/transcript.jsonl')
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_get_file_hash_returns_string(self):
        """get_file_hash() returns a non-empty string for a valid file."""
        path = self._make_jsonl('hash_test.jsonl', [{'x': 1}])
        reader = self.IncrementalTranscriptReader(db_conn=self.conn)
        h = reader.get_file_hash(path)
        self.assertIsInstance(h, str)
        self.assertGreater(len(h), 0)

    def test_offsets_are_correct(self):
        """Offsets returned by read_new_lines must match exact line start byte positions."""
        path = os.path.join(self.tmpdir, 'offsets.jsonl')
        line1 = json.dumps({'line': 1}) + '\n'
        line2 = json.dumps({'line': 2, 'extra': 'some text data'}) + '\n'
        
        with open(path, 'wb') as f:
            f.write(line1.encode('utf-8'))
            f.write(line2.encode('utf-8'))
            
        reader = self.IncrementalTranscriptReader(db_conn=self.conn)
        lines = reader.read_new_lines(path)
        
        self.assertEqual(len(lines), 2)
        # Line 1 should start at 0
        self.assertEqual(lines[0][1], 0)
        # Line 2 should start at length of line 1
        self.assertEqual(lines[1][1], len(line1.encode('utf-8')))


if __name__ == '__main__':
    unittest.main(verbosity=2)
