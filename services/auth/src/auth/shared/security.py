"""Security implementations for password hashing and JWT token management."""

import asyncio
import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import bcrypt
import jwt

from auth.shared.config import Settings
from auth.shared.domain import PasswordService


class BcryptPasswordService(PasswordService):
    """PasswordService implementation using bcrypt for hashing."""

    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds

    def hash(self, password: str) -> str:
        """Hash a plaintext password using bcrypt."""
        salt = bcrypt.gensalt(rounds=self._rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify(self, password: str, hashed: str) -> bool:
        """Verify a plaintext password against a bcrypt hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    async def hash_async(self, password: str) -> str:
        return await asyncio.to_thread(self.hash, password)

    async def verify_async(self, password: str, hashed: str) -> bool:
        return await asyncio.to_thread(self.verify, password, hashed)


class JWTService:
    """Manages RS256 JWT token creation, decoding, and JWKS endpoint data."""

    def __init__(self, settings: Settings) -> None:
        self._private_key = settings.rsa_private_key
        self._public_key = settings.rsa_public_key
        self._algorithm = settings.jwt_algorithm
        self._access_expire_minutes = settings.jwt_access_token_expire_minutes
        self._refresh_expire_days = settings.jwt_refresh_token_expire_days

    def create_access_token(
        self,
        user_id: UUID,
        tenant_id: UUID,
        roles: list[str],
    ) -> str:
        """Create a short-lived JWT access token."""
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "roles": roles,
            "type": "access",
            "exp": now + timedelta(minutes=self._access_expire_minutes),
            "iat": now,
            "jti": str(uuid4()),
        }
        return jwt.encode(payload, self._private_key, algorithm=self._algorithm)

    def create_refresh_token(
        self,
        user_id: UUID,
        tenant_id: UUID,
    ) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "type": "refresh",
            "exp": now + timedelta(days=self._refresh_expire_days),
            "iat": now,
            "jti": str(uuid4()),
        }
        return jwt.encode(payload, self._private_key, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict:
        return jwt.decode(token, self._public_key, algorithms=[self._algorithm])

    @property
    def access_expire_minutes(self) -> int:
        return self._access_expire_minutes

    @property
    def public_key_pem(self) -> str:
        return self._public_key

    def get_jwks(self) -> dict:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key

        public_key = load_pem_public_key(self._public_key.encode())
        numbers = public_key.public_numbers()

        def _int_to_base64url(value: int) -> str:
            import base64

            byte_length = (value.bit_length() + 7) // 8
            value_bytes = value.to_bytes(byte_length, byteorder="big")
            return base64.urlsafe_b64encode(value_bytes).rstrip(b"=").decode("ascii")

        kid = hashlib.sha256(self._public_key.encode()).hexdigest()[:16]

        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "kid": kid,
                    "n": _int_to_base64url(numbers.n),
                    "e": _int_to_base64url(numbers.e),
                }
            ]
        }
