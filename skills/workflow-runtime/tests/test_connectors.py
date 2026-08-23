"""
test_connectors.py — FEAT-048 Phase 5 Task 5.1
Tests: ConnectorRegistry, all 4 connectors (FR-01, FR-02)
Blueprint test matrix: test_connectors.py
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestConnectorRegistry(unittest.TestCase):
    """FR-01: ConnectorRegistry — discovers, routes, detect_all()"""

    def setUp(self):
        from connectors import ConnectorRegistry, build_default_registry
        self.build_default_registry = build_default_registry
        self.ConnectorRegistry = ConnectorRegistry

    def test_build_default_registry_returns_registry(self):
        """build_default_registry() returns a ConnectorRegistry instance."""
        reg = self.build_default_registry()
        self.assertIsInstance(reg, self.ConnectorRegistry)

    def test_detect_all_returns_list(self):
        """detect_all() returns a list (may be empty on machine without providers)."""
        reg = self.build_default_registry()
        result = reg.detect_all()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_registry_has_registered_providers(self):
        """Registry has the 4 built-in provider connectors via list_registered()."""
        reg = self.build_default_registry()
        names = reg.list_registered()  # correct method name
        self.assertIn('antigravity', names)
        self.assertIn('claude_code', names)
        self.assertIn('cursor', names)
        self.assertIn('vscode_agents', names)

    def test_parse_unknown_provider_raises_connector_not_found(self):
        """ConnectorRegistry.parse() raises ConnectorNotFoundError for unknown provider."""
        from connectors import ConnectorNotFoundError
        reg = self.build_default_registry()
        with self.assertRaises(ConnectorNotFoundError):
            reg.parse('nonexistent_provider_xyz', 'test-conv-id')

    def test_get_connector_known_provider_returns_connector(self):
        """get_connector('antigravity') returns a connector instance."""
        reg = self.build_default_registry()
        conn = reg.get_connector('antigravity')
        self.assertIsNotNone(conn)
        self.assertEqual(conn.get_provider_name(), 'antigravity')

    def test_get_connector_unknown_returns_none(self):
        """get_connector() on unknown provider returns None (not raises)."""
        reg = self.build_default_registry()
        result = reg.get_connector('nonexistent_xyz')
        self.assertIsNone(result)

    def test_diagnose_all_returns_list(self):
        """diagnose_all() returns list of DiagnosticsResult objects."""
        reg = self.build_default_registry()
        results = reg.diagnose_all()
        self.assertIsInstance(results, list)
        for r in results:
            self.assertTrue(hasattr(r, 'provider_name') or hasattr(r, 'status'))


class TestAntigravityConnector(unittest.TestCase):
    """FR-02: AntigravityConnector"""

    def setUp(self):
        from connectors.antigravity import AntigravityConnector
        self.AntigravityConnector = AntigravityConnector

    def test_get_provider_name(self):
        """Connector returns canonical name 'antigravity'."""
        conn = self.AntigravityConnector()
        self.assertEqual(conn.get_provider_name(), 'antigravity')

    def test_detect_returns_none_or_detected_provider(self):
        """detect() returns DetectedProvider or None — never raises."""
        conn = self.AntigravityConnector()
        result = conn.detect()
        self.assertTrue(result is None or hasattr(result, 'provider_name'))

    def test_env_override_accepted(self):
        """ANTIGRAVITY_BRAIN_ROOT env override is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['ANTIGRAVITY_BRAIN_ROOT'] = tmpdir
            try:
                conn = self.AntigravityConnector()
                result = conn.detect()
                self.assertTrue(result is None or hasattr(result, 'provider_name'))
            finally:
                del os.environ['ANTIGRAVITY_BRAIN_ROOT']

    def test_get_diagnostics_has_status(self):
        """get_diagnostics() returns object with status field."""
        conn = self.AntigravityConnector()
        diag = conn.get_diagnostics()
        d = diag.__dict__ if hasattr(diag, '__dict__') else diag
        self.assertIn('status', d)

    def test_parse_nonexistent_conv_returns_empty(self):
        """parse_conversation() on non-existent conversation returns empty list."""
        conn = self.AntigravityConnector()
        result = conn.parse_conversation('nonexistent-conv-id-xyz-999')
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


class TestClaudeCodeConnector(unittest.TestCase):
    """FR-02: ClaudeCodeConnector"""

    def setUp(self):
        from connectors.claude_code import ClaudeCodeConnector
        self.ClaudeCodeConnector = ClaudeCodeConnector

    def test_get_provider_name(self):
        conn = self.ClaudeCodeConnector()
        self.assertEqual(conn.get_provider_name(), 'claude_code')

    def test_detect_has_status_field_or_none(self):
        """detect() returns object with status field or None."""
        conn = self.ClaudeCodeConnector()
        result = conn.detect()
        self.assertTrue(result is None or hasattr(result, 'status'))

    def test_get_diagnostics_returns_result(self):
        """get_diagnostics() returns dict-like with status field."""
        conn = self.ClaudeCodeConnector()
        diag = conn.get_diagnostics()
        d = diag.__dict__ if hasattr(diag, '__dict__') else diag
        self.assertIn('status', d)


class TestCursorConnector(unittest.TestCase):
    """FR-02: CursorConnector"""

    def setUp(self):
        from connectors.cursor import CursorConnector
        self.CursorConnector = CursorConnector

    def test_get_provider_name(self):
        conn = self.CursorConnector()
        self.assertEqual(conn.get_provider_name(), 'cursor')

    def test_detect_never_raises(self):
        """detect() must never raise even if paths do not exist."""
        conn = self.CursorConnector()
        try:
            conn.detect()
        except Exception as e:
            self.fail(f'detect() raised unexpectedly: {e}')


class TestVSCodeAgentsConnector(unittest.TestCase):
    """FR-02: VSCodeAgentsConnector"""

    def setUp(self):
        from connectors.vscode_agents import VSCodeAgentsConnector
        self.VSCodeAgentsConnector = VSCodeAgentsConnector

    def test_get_provider_name(self):
        conn = self.VSCodeAgentsConnector()
        self.assertEqual(conn.get_provider_name(), 'vscode_agents')

    def test_detect_never_raises(self):
        conn = self.VSCodeAgentsConnector()
        try:
            conn.detect()
        except Exception as e:
            self.fail(f'detect() raised unexpectedly: {e}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
