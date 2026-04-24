"""Tests for ``apps.core.crypto`` — AES-256-GCM envelope-encryption facade.

Coverage:
    - Round-trip encrypt/decrypt.
    - Wrap/unwrap DEK round-trip.
    - Tamper detection (wrong key or modified ciphertext raises).
    - Master key rotation preserves plaintext after re-wrap.
"""

from __future__ import annotations

import os

import pytest
from cryptography.exceptions import InvalidTag

from apps.core.crypto import (
    Cipher,
    WrappedDEK,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def master_key() -> bytes:
    """32-byte random master key for tests."""
    return os.urandom(32)


@pytest.fixture()
def cipher(master_key: bytes) -> Cipher:
    """Cipher bound to a fresh random master key."""
    return Cipher(master_key)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_cipher_rejects_short_master_key() -> None:
    """Master key shorter than 32 bytes must raise ValueError."""
    with pytest.raises(ValueError, match="32 bytes"):
        Cipher(b"too-short")


def test_cipher_rejects_long_master_key() -> None:
    """Master key longer than 32 bytes must raise ValueError."""
    with pytest.raises(ValueError, match="32 bytes"):
        Cipher(os.urandom(64))


# ---------------------------------------------------------------------------
# DEK generation
# ---------------------------------------------------------------------------


def test_generate_dek_is_32_bytes(cipher: Cipher) -> None:
    dek = cipher.generate_dek()
    assert len(dek) == 32


def test_generate_dek_is_random(cipher: Cipher) -> None:
    """Two freshly generated DEKs must not be equal."""
    assert cipher.generate_dek() != cipher.generate_dek()


# ---------------------------------------------------------------------------
# Wrap / unwrap DEK round-trip
# ---------------------------------------------------------------------------


def test_wrap_unwrap_dek_round_trip(cipher: Cipher) -> None:
    """Wrapping then unwrapping a DEK must return the original bytes."""
    dek = cipher.generate_dek()
    wrapped = cipher.wrap_dek(dek)

    assert isinstance(wrapped, WrappedDEK)
    assert len(wrapped.nonce) == 12  # 96-bit nonce per SPEC §7.2
    assert wrapped.ciphertext != dek  # must actually be encrypted

    recovered = cipher.unwrap_dek(wrapped)
    assert recovered == dek


def test_wrap_produces_unique_nonces(cipher: Cipher) -> None:
    """Each wrap operation must use a fresh nonce."""
    dek = cipher.generate_dek()
    wrapped1 = cipher.wrap_dek(dek)
    wrapped2 = cipher.wrap_dek(dek)
    assert wrapped1.nonce != wrapped2.nonce


# ---------------------------------------------------------------------------
# Tamper detection — DEK unwrap
# ---------------------------------------------------------------------------


def test_unwrap_wrong_master_key_raises(cipher: Cipher) -> None:
    """Unwrapping with a different master key must raise InvalidTag."""
    dek = cipher.generate_dek()
    wrapped = cipher.wrap_dek(dek)

    different_cipher = Cipher(os.urandom(32))
    with pytest.raises(InvalidTag):
        different_cipher.unwrap_dek(wrapped)


def test_unwrap_tampered_ciphertext_raises(cipher: Cipher) -> None:
    """Flipping a bit in the wrapped ciphertext must raise InvalidTag."""
    dek = cipher.generate_dek()
    wrapped = cipher.wrap_dek(dek)

    tampered_ct = bytes([wrapped.ciphertext[0] ^ 0xFF]) + wrapped.ciphertext[1:]
    tampered = WrappedDEK(ciphertext=tampered_ct, nonce=wrapped.nonce)

    with pytest.raises(InvalidTag):
        cipher.unwrap_dek(tampered)


def test_unwrap_tampered_nonce_raises(cipher: Cipher) -> None:
    """Using the wrong nonce for unwrap must raise InvalidTag."""
    dek = cipher.generate_dek()
    wrapped = cipher.wrap_dek(dek)

    wrong_nonce = os.urandom(12)
    tampered = WrappedDEK(ciphertext=wrapped.ciphertext, nonce=wrong_nonce)

    with pytest.raises(InvalidTag):
        cipher.unwrap_dek(tampered)


# ---------------------------------------------------------------------------
# Encrypt / decrypt round-trip
# ---------------------------------------------------------------------------


def test_encrypt_decrypt_round_trip(cipher: Cipher) -> None:
    """Encrypting then decrypting must recover the original plaintext."""
    dek = cipher.generate_dek()
    plaintext = b"super secret household data"

    ciphertext, nonce = cipher.encrypt(plaintext, dek)

    assert ciphertext != plaintext
    assert len(nonce) == 12  # 96-bit per SPEC §7.2

    recovered = cipher.decrypt(ciphertext, nonce, dek)
    assert recovered == plaintext


def test_encrypt_empty_plaintext(cipher: Cipher) -> None:
    """Empty plaintext must round-trip cleanly (GCM is auth-only in that case)."""
    dek = cipher.generate_dek()
    ciphertext, nonce = cipher.encrypt(b"", dek)
    assert cipher.decrypt(ciphertext, nonce, dek) == b""


def test_encrypt_produces_unique_nonces(cipher: Cipher) -> None:
    """Each encrypt call must use a fresh nonce."""
    dek = cipher.generate_dek()
    _, nonce1 = cipher.encrypt(b"hello", dek)
    _, nonce2 = cipher.encrypt(b"hello", dek)
    assert nonce1 != nonce2


# ---------------------------------------------------------------------------
# Tamper detection — data decrypt
# ---------------------------------------------------------------------------


def test_decrypt_wrong_dek_raises(cipher: Cipher) -> None:
    """Decrypting with the wrong DEK must raise InvalidTag."""
    dek = cipher.generate_dek()
    ciphertext, nonce = cipher.encrypt(b"secret", dek)

    wrong_dek = cipher.generate_dek()
    with pytest.raises(InvalidTag):
        cipher.decrypt(ciphertext, nonce, wrong_dek)


def test_decrypt_tampered_ciphertext_raises(cipher: Cipher) -> None:
    """Flipping a bit in the ciphertext must raise InvalidTag."""
    dek = cipher.generate_dek()
    ciphertext, nonce = cipher.encrypt(b"secret", dek)

    tampered = bytes([ciphertext[0] ^ 0xFF]) + ciphertext[1:]
    with pytest.raises(InvalidTag):
        cipher.decrypt(tampered, nonce, dek)


def test_decrypt_wrong_nonce_raises(cipher: Cipher) -> None:
    """Using the wrong nonce for decrypt must raise InvalidTag."""
    dek = cipher.generate_dek()
    ciphertext, _nonce = cipher.encrypt(b"secret", dek)

    wrong_nonce = os.urandom(12)
    with pytest.raises(InvalidTag):
        cipher.decrypt(ciphertext, wrong_nonce, dek)


# ---------------------------------------------------------------------------
# Master key rotation
# ---------------------------------------------------------------------------


def test_rotate_master_key_preserves_plaintext(cipher: Cipher) -> None:
    """After rotation the plaintext must still be recoverable.

    The rotation changes only the DEK envelope; data ciphertext is untouched.
    The new Cipher (with the new master key) must be able to unwrap the
    rotated DEK and decrypt the original ciphertext.
    """
    # Encrypt some data with a DEK wrapped under the original master key.
    dek = cipher.generate_dek()
    wrapped = cipher.wrap_dek(dek)
    plaintext = b"household budget data"
    ciphertext, nonce = cipher.encrypt(plaintext, dek)

    # Rotate to a new master key.
    new_master_key = os.urandom(32)
    new_wrapped = cipher.rotate_master_key(new_master_key, wrapped)

    # Original Cipher can no longer unwrap new_wrapped.
    with pytest.raises(InvalidTag):
        cipher.unwrap_dek(new_wrapped)

    # New Cipher can unwrap and decrypt.
    new_cipher = Cipher(new_master_key)
    recovered_dek = new_cipher.unwrap_dek(new_wrapped)
    assert recovered_dek == dek

    recovered_plaintext = new_cipher.decrypt(ciphertext, nonce, recovered_dek)
    assert recovered_plaintext == plaintext


def test_rotate_master_key_invalid_new_key_raises(cipher: Cipher) -> None:
    """Rotating to a key of invalid length must raise ValueError."""
    dek = cipher.generate_dek()
    wrapped = cipher.wrap_dek(dek)

    with pytest.raises(ValueError, match="32 bytes"):
        cipher.rotate_master_key(b"short", wrapped)


def test_rotate_master_key_wrong_current_key_raises() -> None:
    """Rotating when the current master key is wrong must raise InvalidTag."""
    original_cipher = Cipher(os.urandom(32))
    wrong_cipher = Cipher(os.urandom(32))

    dek = original_cipher.generate_dek()
    wrapped = original_cipher.wrap_dek(dek)

    new_master_key = os.urandom(32)
    with pytest.raises(InvalidTag):
        wrong_cipher.rotate_master_key(new_master_key, wrapped)


# ---------------------------------------------------------------------------
# WrappedDEK serialization (to_bytes / from_bytes)
# ---------------------------------------------------------------------------


def test_wrapped_dek_round_trip_serialization(cipher: Cipher) -> None:
    """to_bytes() then from_bytes() must reconstruct the original WrappedDEK."""
    dek = cipher.generate_dek()
    wrapped = cipher.wrap_dek(dek)

    blob = wrapped.to_bytes()
    restored = WrappedDEK.from_bytes(blob)

    assert restored.nonce == wrapped.nonce
    assert restored.ciphertext == wrapped.ciphertext


def test_wrapped_dek_to_bytes_wire_format(cipher: Cipher) -> None:
    """Wire format must be nonce (12 B) concatenated with ciphertext."""
    dek = cipher.generate_dek()
    wrapped = cipher.wrap_dek(dek)

    blob = wrapped.to_bytes()
    assert blob[:12] == wrapped.nonce
    assert blob[12:] == wrapped.ciphertext


def test_wrapped_dek_from_bytes_too_short_raises() -> None:
    """from_bytes() with fewer than 12 bytes must raise ValueError."""
    with pytest.raises(ValueError, match="too short"):
        WrappedDEK.from_bytes(b"short")


def test_wrapped_dek_from_bytes_exactly_12_bytes() -> None:
    """from_bytes() with exactly 12 bytes is valid (nonce only, empty ciphertext)."""
    blob = b"\x00" * 12
    restored = WrappedDEK.from_bytes(blob)
    assert restored.nonce == b"\x00" * 12
    assert restored.ciphertext == b""


def test_wrapped_dek_serialized_can_unwrap(cipher: Cipher) -> None:
    """A WrappedDEK round-tripped through to_bytes/from_bytes must still unwrap correctly."""
    dek = cipher.generate_dek()
    wrapped = cipher.wrap_dek(dek)

    restored = WrappedDEK.from_bytes(wrapped.to_bytes())
    assert cipher.unwrap_dek(restored) == dek


# ---------------------------------------------------------------------------
# Nonce-length validation — unwrap_dek and decrypt
# ---------------------------------------------------------------------------


def test_unwrap_dek_wrong_length_nonce_raises(cipher: Cipher) -> None:
    """unwrap_dek() must raise ValueError when nonce is not 12 bytes."""
    dek = cipher.generate_dek()
    wrapped = cipher.wrap_dek(dek)

    bad_nonce_short = WrappedDEK(ciphertext=wrapped.ciphertext, nonce=b"\x00" * 8)
    with pytest.raises(ValueError, match="nonce must be 12 bytes"):
        cipher.unwrap_dek(bad_nonce_short)

    bad_nonce_long = WrappedDEK(ciphertext=wrapped.ciphertext, nonce=b"\x00" * 16)
    with pytest.raises(ValueError, match="nonce must be 12 bytes"):
        cipher.unwrap_dek(bad_nonce_long)


def test_decrypt_wrong_length_nonce_raises(cipher: Cipher) -> None:
    """decrypt() must raise ValueError when nonce is not 12 bytes."""
    dek = cipher.generate_dek()
    ciphertext, _nonce = cipher.encrypt(b"test payload", dek)

    with pytest.raises(ValueError, match="nonce must be 12 bytes"):
        cipher.decrypt(ciphertext, b"\x00" * 8, dek)

    with pytest.raises(ValueError, match="nonce must be 12 bytes"):
        cipher.decrypt(ciphertext, b"\x00" * 16, dek)
