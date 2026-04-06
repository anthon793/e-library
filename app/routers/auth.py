from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.schemas.user import UserCreate, UserLogin, Token
from app.services.auth_service import authenticate_user, create_user, create_access_token
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/api", tags=["Authentication"])


@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    role = user_data.role if user_data.role in ("student", "lecturer") else "student"
    user = create_user(
        db,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        password=user_data.password,
        role=role,
    )
    return {"message": "Registration successful", "user_id": user.id}


@router.post("/login")
def login(response: Response, user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    is_admin = user.role.value == "admin"
    session_hours = settings.ADMIN_ACCESS_TOKEN_EXPIRE_HOURS if is_admin else settings.ACCESS_TOKEN_EXPIRE_HOURS
    token = create_access_token({"sub": user.username, "role": user.role.value}, expires_hours=session_hours)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=session_hours * 3600,
        samesite="lax",
    )
    return {
        "message": "Login successful",
        "access_token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value,
        },
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me")
def get_me(request: Request, db: Session = Depends(get_db)):
    from app.dependencies import get_current_user_optional
    user = get_current_user_optional(request, db)
    if not user:
        return {"user": None}
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role.value,
        }
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    from app.models.book import Book
    from app.models.download import Download
    from app.models.category import Category
    from app.models.book import BookType
    from app.config import ALLOWED_CATEGORY_SLUGS
    total_books = (
        db.query(Book)
        .join(Category)
        .filter(
            Category.slug.in_(ALLOWED_CATEGORY_SLUGS),
            Book.book_type == BookType.archive,
            Book.source == "Internet Archive",
        )
        .count()
    )
    total_downloads = (
        db.query(Download)
        .join(Book)
        .join(Category)
        .filter(
            Category.slug.in_(ALLOWED_CATEGORY_SLUGS),
            Book.book_type == BookType.archive,
            Book.source == "Internet Archive",
        )
        .count()
    )
    total_users = db.query(User).count()
    return {
        "total_books": total_books,
        "total_downloads": total_downloads,
        "total_users": total_users,
    }
