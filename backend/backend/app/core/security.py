from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import jwt, JWTError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from app.core.config import settings


def _password_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_password_bytes(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_access_expire_minutes))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.jwt_refresh_expire_days))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise ValueError("Invalid token")


def get_token_type(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm], options={"verify_exp": False})
        return payload.get("type")
    except JWTError:
        return None


class EnvelopeEncryption:
    def __init__(self, master_key: str):
        if not master_key:
            raise ValueError("MASTER_KEY must be set")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"aios-salt-v1",
            iterations=100_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        return self.fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.fernet.decrypt(ciphertext.encode()).decode()


def get_encryption() -> EnvelopeEncryption:
    return EnvelopeEncryption(settings.master_key)


def mask_key(key: str, visible: int = 4) -> str:
    if len(key) <= visible:
        return "•" * len(key)
    return key[:visible] + "•" * (len(key) - visible * 2) + key[-visible:]