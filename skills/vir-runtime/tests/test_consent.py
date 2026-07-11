# File path: tests/unit/test_consent.py
import unittest
from vir_runtime.core.consent import SDLCCheckpointManager, ConsentValidator, ConsentDeniedError

class TestConsent(unittest.TestCase):
    def test_checkpoint_manager(self):
        manager = SDLCCheckpointManager()
        self.assertFalse(manager.verify_gate_block("CP-1"))
        self.assertTrue(manager.verify_gate_block("CP-5")) # Mock block CP-5
        
        self.assertEqual(manager.active_checkpoint, 1)
        manager.advance_checkpoint()
        self.assertEqual(manager.active_checkpoint, 2)

    def test_consent_validator_allowed(self):
        # Default config doesn't deny local or non-openai providers
        validator = ConsentValidator(config_path="nonexistent_config.yaml")
        validator.check_consent_permission("ollama/llama3") # Local provider

    def test_consent_validator_denied(self):
        # OpenAI requires explicit consent
        validator = ConsentValidator(config_path="nonexistent_config.yaml")
        with self.assertRaises(ConsentDeniedError):
            validator.check_consent_permission("openai/gpt-4")

if __name__ == "__main__":
    unittest.main()
