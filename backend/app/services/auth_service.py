from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.models.enums import UserStatus


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Validate credentials and return the User on success.

    Raises:
        ValueError: with a generic message on any authentication failure.
                    The message is intentionally non-specific to avoid
                    leaking whether the email or password was wrong.
    """
    user = db.query(User).filter(User.email == email).first()

    # Use verify_password even when user is not found to prevent timing attacks
    # Valid bcrypt hash used as timing-safe dummy when user is not found
    dummy_hash = "$2b$12$c8JMpfoOlvGKNXNFwwRxrOaFFVTfMyEWxIUsZyOLPMHeTcQ8JBFRy"
    candidate_hash = user.password_hash if user else dummy_hash

    if not verify_password(password, candidate_hash) or user is None:
        raise ValueError("Invalid credentials")

    if user.status == UserStatus.INACTIVE:
        raise ValueError("Account is inactive")

    return user
