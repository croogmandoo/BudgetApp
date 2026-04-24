"""Envelope-encryption helpers.

Design (SPEC §7.2):

    - The master key comes from the ``APP_MASTER_KEY`` environment variable
      and is held in-process as bytes. It never leaves the server and is
      never persisted to the database.
    - Every encrypted row / file gets its own random data-encryption key
      (DEK). Plaintext is encrypted with the DEK; the DEK is then wrapped
      (encrypted) with the master key and stored alongside the ciphertext.
    - Key rotation re-wraps DEKs without touching ciphertext, so rotating
      ``APP_MASTER_KEY`` is cheap.

This module exposes the interface every caller should go through so we can
centralise algorithm choice (AES-256-GCM planned) and ship a single audited
implementation. The concrete cryptography lives behind
``cryptography.hazmat`` APIs; the public surface below is intentionally
narrow.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True)
class WrappedDEK:
    """A data-encryption key wrapped by the master key.

    ``ciphertext`` is the DEK encrypted with the master key (AES-256-GCM).
    ``nonce`` is the 96-bit GCM nonce used for that wrap.
    """

    ciphertext: bytes
    nonce: bytes


class Cipher:
    """Facade over the envelope-encryption scheme.

    Uses AES-256-GCM (SPEC §7.2) for all encryption operations.

    The master key must be exactly 32 bytes (256 bits). It is bound at
    construction time and never stored outside memory.
    """

    _NONCE_SIZE = 12  # 96-bit GCM nonce as per SPEC §7.2
    _DEK_SIZE = 32  # 256-bit DEK

    def __init__(self, master_key: bytes) -> None:
        """Bind the facade to a master key (raw bytes, 32 bytes / 256 bits)."""
        if len(master_key) != self._DEK_SIZE:
            raise ValueError(
                f"Master key must be exactly {self._DEK_SIZE} bytes; got {len(master_key)}"
            )
        self._master_key = master_key
        self._master_aesgcm = AESGCM(master_key)

    def generate_dek(self) -> bytes:
        """Return a fresh random 32-byte DEK."""
        return os.urandom(self._DEK_SIZE)

    def wrap_dek(self, dek: bytes) -> WrappedDEK:
        """Encrypt ``dek`` with the master key (AES-256-GCM). Returns the wrap."""
        nonce = os.urandom(self._NONCE_SIZE)
        ciphertext = self._master_aesgcm.encrypt(nonce, dek, None)
        return WrappedDEK(ciphertext=ciphertext, nonce=nonce)

    def unwrap_dek(self, wrapped: WrappedDEK) -> bytes:
        """Decrypt a previously wrapped DEK.

        Raises ``cryptography.exceptions.InvalidTag`` if the ciphertext or
        nonce has been tampered with (authentication tag mismatch).
        """
        return self._master_aesgcm.decrypt(wrapped.nonce, wrapped.ciphertext, None)

    def encrypt(self, plaintext: bytes, dek: bytes) -> tuple[bytes, bytes]:
        """Encrypt ``plaintext`` with ``dek`` (AES-256-GCM).

        Returns ``(ciphertext, nonce)`` where nonce is 12 random bytes.
        The caller is responsible for persisting both alongside the wrapped DEK.
        """
        aesgcm = AESGCM(dek)
        nonce = os.urandom(self._NONCE_SIZE)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return ciphertext, nonce

    def decrypt(self, ciphertext: bytes, nonce: bytes, dek: bytes) -> bytes:
        """Authenticated-decrypt ``ciphertext`` under ``dek`` + ``nonce``.

        Raises ``cryptography.exceptions.InvalidTag`` on authentication
        failure (tampered ciphertext, wrong key, or wrong nonce).
        """
        aesgcm = AESGCM(dek)
        return aesgcm.decrypt(nonce, ciphertext, None)

    def rotate_master_key(self, new_master_key: bytes, wrapped: WrappedDEK) -> WrappedDEK:
        """Re-wrap ``wrapped`` under ``new_master_key`` without touching ciphertext.

        This is the cheap path for master-key rotation: only the DEK envelope
        is re-encrypted; row/file ciphertext is unchanged.

        Raises ``ValueError`` if ``new_master_key`` is not 32 bytes.
        Raises ``cryptography.exceptions.InvalidTag`` if the current wrap is
        invalid under the current master key.
        """
        dek = self.unwrap_dek(wrapped)
        new_cipher = Cipher(new_master_key)
        return new_cipher.wrap_dek(dek)
