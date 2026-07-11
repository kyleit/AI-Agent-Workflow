# secure_cryptographic_token_authorization.py
import hmac
import hashlib

class SecureTokenAuthorizer:
    """
    FEAT-104: Secure Cryptographic Token Authorization
    HMAC verification for safe user confirmations.
    """
    def __init__(self, secret_key: bytes):
        self.secret_key = secret_key

    def generate_token(self, message: str) -> str:
        return hmac.new(self.secret_key, message.encode(), hashlib.sha256).hexdigest()

    def verify_token(self, message: str, token: str) -> bool:
        expected = self.generate_token(message)
        return hmac.compare_digest(expected, token)
