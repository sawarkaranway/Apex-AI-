"""
Production AES-256-GCM Credential Vault for Chaitanya Karya.
Enforces authenticated encryption at rest with randomized 96-bit nonces and AAD binding.
"""

import os
import json
import base64
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag

class CredentialVault:
    """
    AES-256-GCM Credential Vault.
    
    Security Guarantees:
    - 256-bit symmetric encryption key.
    - Unique 96-bit cryptographic nonce (IV) generated per encryption operation.
    - Authenticated Associated Data (AAD) binding secrets to user_id + provider_id.
    - Defensively structured to minimize plaintext lifetime in memory.
    """

    def __init__(self, master_key_bytes: bytes):
        if len(master_key_bytes) != 32:
            raise ValueError("Master key must be exactly 32 bytes (256 bits).")
        self._aesgcm = AESGCM(master_key_bytes)

    @classmethod
    def from_hex(cls, master_key_hex: str) -> "CredentialVault":
        key_bytes = bytes.fromhex(master_key_hex.strip())
        return cls(key_bytes)

    @classmethod
    def from_passphrase(cls, passphrase: str, salt: bytes, iterations: int = 600_000) -> "CredentialVault":
        """Derives a 256-bit master key from passphrase using PBKDF2-HMAC-SHA256."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        derived_key = kdf.derive(passphrase.encode('utf-8'))
        return cls(derived_key)

    @staticmethod
    def construct_aad(user_id: int, provider_id: str) -> str:
        """Constructs canonical Authenticated Associated Data string."""
        return f"user:{user_id}:provider:{provider_id.lower().strip()}"

    def encrypt_secret(self, payload: Dict[str, Any], associated_data: str) -> str:
        """
        Encrypts a secret payload with AES-256-GCM.
        Returns a JSON envelope containing version, base64 nonce, ciphertext with auth tag, and AAD reference.
        """
        nonce = os.urandom(12)  # Standard 96-bit nonce
        plaintext_bytes = json.dumps(payload).encode('utf-8')
        aad_bytes = associated_data.encode('utf-8') if associated_data else None

        ciphertext = self._aesgcm.encrypt(nonce, plaintext_bytes, aad_bytes)

        envelope = {
            "v": 1,
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "aad": associated_data
        }
        return json.dumps(envelope)

    def decrypt_secret(self, envelope_json: str, expected_associated_data: str) -> Dict[str, Any]:
        """
        Decrypts an envelope.
        Raises InvalidTag if ciphertext is tampered or if expected AAD does not match.
        """
        envelope = json.loads(envelope_json)
        recorded_aad = envelope.get("aad", "")
        
        if recorded_aad != expected_associated_data:
            raise InvalidTag(f"AAD mismatch: expected '{expected_associated_data}', recorded '{recorded_aad}'.")

        nonce = base64.b64decode(envelope["nonce"])
        ciphertext = base64.b64decode(envelope["ciphertext"])
        aad_bytes = expected_associated_data.encode('utf-8') if expected_associated_data else None

        decrypted_bytes = self._aesgcm.decrypt(nonce, ciphertext, aad_bytes)
        result = json.loads(decrypted_bytes.decode('utf-8'))
        return result
