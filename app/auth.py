"""
Authentication and authorization module.
Encapsulates cryptographic functions and dependency injection for protected API routes.
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, UTC
import app.models as models
from app.database import get_db


# Cryptographic context: Definition of Argon2 as the default hashing algorithm
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Schema definition for extracting the Bearer token from the HTTP header
security = HTTPBearer()


def get_password_hash(password):
    """
    Generates a cryptographic hash from a plaintext password.

    :param password: Plaintext password as string.
    :return: Hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """
    Verifies a plaintext password against a stored hash.

    :param plain_password: The plaintext password to check.
    :param hashed_password: The hash persisted in the database.
    :return: True if matched, otherwise False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """
    FastAPI dependency for token validation and identification of the current user.

    :param credentials: HTTP authentication object provided by the client.
    :param db: Isolated database session of the current request.
    :raises HTTPException: On missing/invalid token (401) or inactive user (401).
    :return: The authenticated user object.
    """
    token = credentials.credentials

    # Database query to retrieve the corresponding session
    session = db.query(models.Session).filter(models.Session.token == token).first()

    # Session existence check (prevents AttributeError in subsequent steps)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expiry = session.expires_at

    # Ensure timezone consistency (UTC) for time comparison
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=UTC)

    # Validation of the cryptographic expiration date
    if not session or expiry < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Authorization check: Verification of the double opt-in status
    if not session.user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive."
            )

    return session.user