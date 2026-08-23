"""E2EE content cipher.

Standard library only (no AES/AEAD in stdlib), so this is a well-understood
Encrypt-then-MAC construction:

  KDF     scrypt(passphrase, salt) -> enc_key || mac_key
  cipher  SHA256 counter-mode keystream (HMAC-SHA256(enc_key, nonce||i)) XOR plaintext
  auth    tag = HMAC-SHA256(mac_key, nonce || ciphertext), verified constant-time

Honest limitations (see SKILL.md / blueprint §6b): pre-shared passphrase, no
forward secrecy, metadata (from/to/seq/size) not hidden. LAN dev tool, not a
secure-messaging product.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from ..domain.ports import MessageCipher
from . import envelope

_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1


def _b64e(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def _keystream(enc_key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        out.extend(hmac.new(enc_key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest())
        counter += 1
    return bytes(out[:length])


class NullCipher(MessageCipher):
    """No E2EE key configured: pass plaintext through, flag foreign envelopes."""

    def encrypt(self, plaintext: str) -> str:
        return plaintext

    def decrypt(self, text: str) -> str:
        return "[encrypted]" if envelope.is_envelope(text) else text


class PskCipher(MessageCipher):
    def __init__(self, passphrase: str) -> None:
        self._passphrase = passphrase.encode("utf-8")

    def _derive(self, salt: bytes) -> tuple[bytes, bytes]:
        dk = hashlib.scrypt(
            self._passphrase, salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=64
        )
        return dk[:32], dk[32:]

    def encrypt(self, plaintext: str) -> str:
        salt = secrets.token_bytes(16)
        nonce = secrets.token_bytes(16)
        enc_key, mac_key = self._derive(salt)
        data = plaintext.encode("utf-8")
        keystream = _keystream(enc_key, nonce, len(data))
        ciphertext = bytes(a ^ b for a, b in zip(data, keystream))
        tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
        return envelope.pack(_b64e(salt), _b64e(nonce), _b64e(ciphertext), _b64e(tag))

    def decrypt(self, text: str) -> str:
        if not envelope.is_envelope(text):
            return text
        try:
            obj = envelope.unpack(text)
            salt = _b64d(obj["salt"])
            nonce = _b64d(obj["nonce"])
            ciphertext = _b64d(obj["ct"])
            tag = _b64d(obj["tag"])
        except (KeyError, ValueError):
            return "[encrypted: malformed]"
        enc_key, mac_key = self._derive(salt)
        expected = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, tag):
            return "[encrypted: auth failed]"
        keystream = _keystream(enc_key, nonce, len(ciphertext))
        return bytes(a ^ b for a, b in zip(ciphertext, keystream)).decode("utf-8", errors="replace")
