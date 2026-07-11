import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from secure_cryptographic_token_authorization import SecureTokenAuthorizer

def test_token_authorizer():
    auth = SecureTokenAuthorizer(b"secret")
    token = auth.generate_token("action_approve")
    assert auth.verify_token("action_approve", token) is True
    assert auth.verify_token("action_deny", token) is False
