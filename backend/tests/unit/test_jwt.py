"""Unit tests for JWT token creation + verification."""


def test_create_and_verify_roundtrip(src_on_path):
    from auth.jwt import create_jwt_token, verify_jwt_token
    token = create_jwt_token("merchant-123")
    payload = verify_jwt_token(token)
    assert payload is not None
    assert payload["merchant_id"] == "merchant-123"


def test_verify_rejects_tampered_token(src_on_path):
    from auth.jwt import create_jwt_token, verify_jwt_token
    token = create_jwt_token("merchant-abc")
    tampered = token[:-4] + "xxxx"
    assert verify_jwt_token(tampered) is None


def test_verify_rejects_token_signed_with_other_secret(monkeypatch, tmp_path):
    import sys
    from pathlib import Path
    src = Path(__file__).resolve().parent.parent.parent / "src"
    monkeypatch.syspath_prepend(str(src))

    # First secret: sign
    monkeypatch.setenv("SALLA_API_KEY", "x"); monkeypatch.setenv("SALLA_WEBHOOK_SECRET", "y")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("ENCRYPTION_KEY", "k")
    monkeypatch.setenv("JWT_SECRET", "secret-one-aaaaaaaaaaaaaaaaaaaa")
    for m in list(sys.modules):
        if m.startswith(("config", "auth")):
            del sys.modules[m]
    from auth.jwt import create_jwt_token
    token = create_jwt_token("m")

    # Rotate secret, reload module, verify fails
    monkeypatch.setenv("JWT_SECRET", "secret-two-bbbbbbbbbbbbbbbbbbbb")
    for m in list(sys.modules):
        if m.startswith(("config", "auth")):
            del sys.modules[m]
    from auth.jwt import verify_jwt_token
    assert verify_jwt_token(token) is None
