"""Generate secure random values for JWT_SECRET and ENCRYPTION_KEY.

Usage:
    python -m config.gen_keys
"""
import secrets
from cryptography.fernet import Fernet


def main():
    print(f"JWT_SECRET={secrets.token_urlsafe(48)}")
    print(f"ENCRYPTION_KEY={Fernet.generate_key().decode()}")


if __name__ == "__main__":
    main()
