import os
from typing import List

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        from pydantic import BaseModel as BaseSettings


def _resolve_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        env = (os.getenv("ENV") or os.getenv("ENVIRONMENT") or "").lower()
        if env in ["production", "staging"]:
            raise ValueError("JWT_SECRET no configurado en entorno productivo.")
        secret = "insecure-local-testing-secret-only"
    return secret


JWT_SECRET: str = _resolve_jwt_secret()


class Settings(BaseSettings):
    """Configuración centralizada y tipada del sistema con Pydantic Settings."""
    
    # Base de Datos (Supabase PostgreSQL con soporte pgvector)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/seniorvital_db"
    )

    # Inferencia IA (Google AI Studio & OpenRouter)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "google/gemma-4-31b:free")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")

    # Seguridad y JWT
    JWT_SECRET: str = _resolve_jwt_secret()
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    # Web Push Notifications (Claves VAPID)
    VAPID_PUBLIC_KEY: str = os.getenv("VAPID_PUBLIC_KEY", "")
    VAPID_PRIVATE_KEY: str = os.getenv("VAPID_PRIVATE_KEY", "")
    VAPID_CLAIM_EMAIL: str = os.getenv("VAPID_CLAIM_EMAIL", "mailto:soporte@seniorvital.com")

    # Servidor y Puerto (Render.com)
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Orígenes CORS permitidos
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "https://seniorvital-backend.onrender.com",
        "*"
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
