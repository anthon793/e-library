import os
from dotenv import load_dotenv

load_dotenv()

ALLOWED_CATEGORY_SLUGS = ("cybersecurity", "data-science", "artificial-intelligence", "information-systems", "computer-science")


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret-key-change-me")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./elibrary.db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", 52428800))  # 50MB
    ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", 24))
    ADMIN_ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("ADMIN_ACCESS_TOKEN_EXPIRE_HOURS", 168))
    ALGORITHM: str = "HS256"
    OPEN_LIBRARY_BASE_URL: str = "https://openlibrary.org"
    GOOGLE_BOOKS_API_KEY: str = os.getenv("GOOGLE_BOOKS_API_KEY", "")
    HYBRID_IMPORT_MAX_RESULTS_PER_SOURCE: int = int(os.getenv("HYBRID_IMPORT_MAX_RESULTS_PER_SOURCE", 8))
    HYBRID_PDF_VALIDATION_TIMEOUT: int = int(os.getenv("HYBRID_PDF_VALIDATION_TIMEOUT", 20))
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://localhost:8000",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
