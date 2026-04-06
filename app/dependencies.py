from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.auth_service import decode_access_token
from app.models.user import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Get current user from JWT cookie, returns None if not authenticated."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    # Strip 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    payload = decode_access_token(token)
    if not payload:
        return None
    username = payload.get("sub")
    if not username:
        return None
    user = db.query(User).filter(User.username == username).first()
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user from JWT cookie. Raises 401 if not authenticated."""
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


def require_lecturer(current_user: User = Depends(get_current_user)) -> User:
    """Require lecturer or admin role."""
    if current_user.role.value not in ("lecturer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lecturer or admin access required",
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
