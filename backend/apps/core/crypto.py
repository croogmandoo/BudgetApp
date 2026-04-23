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

from dataclasses import dataclass


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

    Implementation deferred. Each method documents the contract callers can
    rely on when implementation lands. Do not call these methods yet; they
    raise ``NotImplementedError`` until the primitives are chosen and
    reviewed against SPEC §7.2.
    """

    def __init__(self, master_key: bytes) -> None:
        """Bind the facade to a master key (raw bytes, 32 bytes / 256 bits)."""
        self._master_key = master_key

    def generate_dek(self) -> bytes:
        """Return a fresh random 32-byte DEK."""
        raise NotImplementedError

    def wrap_dek(self, dek: bytes) -> WrappedDEK:
        """Encrypt ``dek`` with the master key (AES-256-GCM). Returns the wrap."""
        raise NotImplementedError

    def unwrap_dek(self, wrapped: WrappedDEK) -> bytes:
        """Decrypt a previously wrapped DEK. Raises on tampering."""
        raise NotImplementedError

    def encrypt(self, plaintext: bytes, dek: bytes) -> tuple[bytes, bytes]:
        """Encrypt ``plaintext`` with ``dek``. Returns ``(ciphertext, nonce)``."""
        raise NotImplementedError

    def decrypt(self, ciphertext: bytes, nonce: bytes, dek: bytes) -> bytes:
        """Authenticated-decrypt ``ciphertext`` under ``dek`` + ``nonce``."""
        raise NotImplementedError

    def rotate_master_key(self, new_master_key: bytes, wrapped: WrappedDEK) -> WrappedDEK:
        """Re-wrap ``wrapped`` under ``new_master_key`` without touching ciphertext."""
        raise NotImplementedError
