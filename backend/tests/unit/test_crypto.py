"""Unit tests for the Fernet-backed crypto module."""


def test_encrypt_roundtrip(src_on_path):
    from auth import crypto
    crypto.reset_cache()
    ciphertext = crypto.encrypt("salla_access_token_abc")
    assert ciphertext is not None and ciphertext != "salla_access_token_abc"
    assert crypto.decrypt(ciphertext) == "salla_access_token_abc"


def test_encrypt_preserves_none_and_empty(src_on_path):
    from auth import crypto
    crypto.reset_cache()
    assert crypto.encrypt(None) is None
    assert crypto.encrypt("") == ""
    assert crypto.decrypt(None) is None
    assert crypto.decrypt("") == ""


def test_decrypt_tolerates_legacy_plaintext(src_on_path):
    """A value from before the encryption feature shipped must be readable."""
    from auth import crypto
    crypto.reset_cache()
    assert crypto.decrypt("legacy-plaintext-token") == "legacy-plaintext-token"


def test_encrypt_rejects_missing_key(monkeypatch, tmp_path):
    import sys
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parent.parent.parent / "src"))
    for m in list(sys.modules):
        if m.startswith(("config", "auth")):
            del sys.modules[m]
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)

    from auth import crypto
    crypto.reset_cache()
    import pytest
    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
        crypto.encrypt("x")
