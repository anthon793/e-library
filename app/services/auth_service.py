from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_hours: int | None = None) -> str:
    to_encode = data.copy()
    ttl_hours = expires_hours if expires_hours is not None else settings.ACCESS_TOKEN_EXPIRE_HOURS
    expire = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, username: str, email: str, full_name: str, password: str, role: str = "student") -> User:
    hashed = hash_password(password)
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed,
        role=UserRole(role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
