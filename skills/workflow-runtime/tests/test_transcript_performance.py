"""
test_transcript_performance.py — FEAT-048 Phase 5 Task 5.1
Tests: Performance NFR-02 — 50MB parse < 5s, incremental re-read < 200ms
Blueprint test matrix: test_transcript_performance.py
"""
import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def generate_large_jsonl(path: str, num_lines: int) -> int:
    """Write num_lines of realistic JSONL records. Returns actual file size."""
    with open(path, 'w', encoding='utf-8') as f:
        for i in range(num_lines):
            rec = {
                'step_index': i,
                'source': 'MODEL' if i % 2 == 0 else 'USER',
                'type': 'PLANNER_RESPONSE',
                'content': 'x' * 400,  # ~400 bytes per line to hit target size
            }
            f.write(json.dumps(rec) + '\n')
    return os.path.getsize(path)


class TestTranscriptPerformance(unittest.TestCase):
    """NFR-02: Performance targets for transcript parsing."""

    def setUp(self):
        from transcript_engine import IncrementalTranscriptReader
        self.IncrementalTranscriptReader = IncrementalTranscriptReader
        self.tmpdir = tempfile.mkdtemp()
        import db as db_module
        import sqlite3
        db_path = os.path.join(self.tmpdir, 'perf_test.db')
        self.conn = sqlite3.connect(db_path)
        db_module.init_db_schema(self.conn)

    def tearDown(self):
        self.conn.close()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_first_read_1000_lines_under_1s(self):
        """1000-line JSONL read must complete in < 1.0s."""
        path = os.path.join(self.tmpdir, 'transcript_1k.jsonl')
        generate_large_jsonl(path, 1000)

        reader = self.IncrementalTranscriptReader(db_conn=self.conn)
        start = time.perf_counter()
        lines = reader.read_new_lines(path)
        elapsed = time.perf_counter() - start

        self.assertEqual(len(lines), 1000)
        self.assertLess(elapsed, 1.0,
                        f'1000-line read took {elapsed:.3f}s — must be < 1.0s')

    def test_incremental_read_under_200ms(self):
        """Incremental re-read of unchanged file must complete in < 200ms."""
        path = os.path.join(self.tmpdir, 'transcript_cached.jsonl')
        generate_large_jsonl(path, 500)

        reader = self.IncrementalTranscriptReader(db_conn=self.conn)
        reader.read_new_lines(path)  # warm cache

        start = time.perf_counter()
        second = reader.read_new_lines(path)  # incremental — should be near-instant
        elapsed = time.perf_counter() - start

        self.assertEqual(len(second), 0)
        self.assertLess(elapsed, 0.200,
                        f'Incremental re-read took {elapsed*1000:.1f}ms — must be < 200ms')


    def test_100_cost_calculations_under_100ms(self):
        """100× CostEngine.calculate() must complete in < 100ms total."""
        from cost_engine import CostEngine
        pricing_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'pricing.json'
        )
        if not os.path.exists(pricing_path):
            self.skipTest('data/pricing.json not found')

        engine = CostEngine(pricing_path=pricing_path)
        start = time.perf_counter()
        for _ in range(100):
            engine.calculate(
                provider='antigravity',
                model='gemini-2.5-flash',
                input_tokens=100_000,
                output_tokens=50_000,
            )
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.100,
                        f'100 cost calculations took {elapsed*1000:.1f}ms — must be < 100ms')

    def test_large_file_parse_under_5s(self):
        """
        NFR-02: 50MB JSONL parse must complete in < 5s.
        Generates ~50MB of JSONL on-the-fly (approx 100k lines × 500 bytes).
        Skipped if too slow to generate.
        """
        path = os.path.join(self.tmpdir, 'transcript_50mb.jsonl')
        # Generate ~100k lines ≈ 50MB
        gen_start = time.perf_counter()
        actual_size = generate_large_jsonl(path, 100_000)
        gen_elapsed = time.perf_counter() - gen_start
        print(f'\n  Generated {actual_size/1024/1024:.1f}MB in {gen_elapsed:.2f}s')

        reader = self.IncrementalTranscriptReader(db_conn=self.conn)
        start = time.perf_counter()
        lines = reader.read_new_lines(path)
        elapsed = time.perf_counter() - start
        print(f'  Parsed {len(lines)} lines in {elapsed:.3f}s')

        self.assertEqual(len(lines), 100_000)
        self.assertLess(elapsed, 5.0,
                        f'50MB parse took {elapsed:.2f}s — must be < 5.0s (NFR-02)')


if __name__ == '__main__':
    unittest.main(verbosity=2)
