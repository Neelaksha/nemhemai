# Authentication Utilities
import hashlib
import binascii
import hmac
import os
import datetime
from typing import Optional
from fastapi import HTTPException, status, Security, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.hash import pbkdf2_sha256, bcrypt
from models import User

# Configuration
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if pbkdf2_sha256 is not None:
            try:
                if isinstance(hashed_password, str) and pbkdf2_sha256.identify(hashed_password):
                    return pbkdf2_sha256.verify(plain_password, hashed_password)
            except Exception:
                pass
        if bcrypt is not None:
            try:
                if isinstance(hashed_password, str) and bcrypt.identify(hashed_password):
                    return bcrypt.verify(plain_password, hashed_password)
            except Exception:
                pass

        if isinstance(hashed_password, str) and hashed_password.startswith("pbkdf2_sha256$"):
            parts = hashed_password.split("$")
            if len(parts) == 4:
                iterations = int(parts[1])
                salt = binascii.unhexlify(parts[2])
                dk = binascii.unhexlify(parts[3])
                newdk = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, iterations)
                return hmac.compare_digest(newdk, dk)
        return False
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    if pbkdf2_sha256 is not None:
        try:
            return pbkdf2_sha256.hash(password)
        except Exception:
            pass

    iterations = 120000
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return f"pbkdf2_sha256${iterations}${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, db=None):
    """Resolve current user from Authorization header or HttpOnly cookie `access_token`.

    This allows browser clients to use cookie-based auth while retaining support for
    Authorization headers (e.g., API clients and tests).
    """
    from fastapi import Depends
    from models import get_db

    if db is None:
        db = next(get_db())

    # Extract token from Authorization header first
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    else:
        # Fall back to cookie (HttpOnly cookie set by login)
        token = request.cookies.get("access_token")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if not isinstance(username, str) or username is None:
            raise credentials_exception
        from pydantic import BaseModel
        class TokenData(BaseModel):
            username: Optional[str] = None
            role: Optional[str] = None
        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

def require_role(required_role: str):
    """Dependency that checks if user has the required role"""
    def role_checker(user: User = Depends(get_current_user)):
        if getattr(user, 'role', None) != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Access denied. Required role: {required_role}"
            )
        return user
    return role_checker