import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Password hashing  (bcrypt direct — passlib 1.7.4 incompatible with bcrypt 4+)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Return True if plain_password matches the stored hash."""
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def create_access_token(subject: int | str, extra_claims: dict[str, Any] | None = None) -> str:
    """
    Create a signed JWT.

    Args:
        subject: The user identifier (user.id) stored in the 'sub' claim.
        extra_claims: Optional additional claims to include.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    """
    Decode and validate a JWT, returning the user ID from the 'sub' claim.

    Raises:
        ValueError: for any invalid/expired/malformed token condition.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        logger.debug("JWT decode failed: %s", exc)
        raise ValueError("Invalid or expired token") from exc

    sub = payload.get("sub")
    if sub is None:
        raise ValueError("Token missing subject claim")

    try:
        return int(sub)
    except (TypeError, ValueError) as exc:
        raise ValueError("Token subject is not a valid user identifier") from exc
