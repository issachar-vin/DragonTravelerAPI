from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

import repositories.user_repo as user_repo
from config import settings
from models.user import UserCreate, UserResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _user_response(doc: dict) -> UserResponse:
    return UserResponse(id=str(doc["_id"]), email=doc["email"], role=doc.get("role", "user"))


def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be 72 characters or fewer")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.access_token_expire_days)
    return jwt.encode(
        {"sub": user_id, "exp": expire}, settings.secret_key, algorithm=settings.algorithm
    )


def decode_token(token: str) -> str:
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise JWTError("Missing sub")
    return user_id


def register(db: Database, data: UserCreate) -> UserResponse:
    try:
        doc = user_repo.create_user(db, data.email, hash_password(data.password))
    except DuplicateKeyError:
        raise ValueError("Email already registered")
    return _user_response(doc)


def authenticate(db: Database, email: str, password: str) -> str:
    doc = user_repo.find_by_email(db, email.lower())
    if not doc or not verify_password(password, doc["hashed_password"]):
        raise ValueError("Invalid credentials")
    return create_access_token(str(doc["_id"]))


def get_current_user(db: Database, token: str) -> UserResponse:
    from jose import JWTError

    try:
        user_id = decode_token(token)
    except JWTError:
        raise ValueError("Invalid token")
    doc = user_repo.find_by_id(db, user_id)
    if not doc:
        raise ValueError("User not found")
    return _user_response(doc)
