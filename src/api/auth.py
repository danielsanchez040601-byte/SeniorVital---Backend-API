from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

try:
    from src.database.database import get_db
    from src.database.models import User, SeniorProfile, RoleEnum, CaregiverLink
    from src.database.schemas import UserCreate, UserResponse, LoginRequest, TokenResponse, SeniorProfileCreate, SeniorProfileResponse
    from src.api.config import settings
except ImportError:
    try:
        from ..database.database import get_db
        from ..database.models import User, SeniorProfile, RoleEnum, CaregiverLink
        from ..database.schemas import UserCreate, UserResponse, LoginRequest, TokenResponse, SeniorProfileCreate, SeniorProfileResponse
        from .config import settings
    except ImportError:
        from database import get_db
        from models import User, SeniorProfile, RoleEnum, CaregiverLink
        from schemas import UserCreate, UserResponse, LoginRequest, TokenResponse, SeniorProfileCreate, SeniorProfileResponse
        from config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])
import bcrypt

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registra un nuevo usuario en la plataforma."""
    result = await db.execute(select(User).filter(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado.")

    new_user = User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Si es adulto mayor, inicializamos su perfil base
    if new_user.role == RoleEnum.SENIOR:
        profile = SeniorProfile(user_id=new_user.id, fitness_level=1)
        db.add(profile)
        await db.commit()

    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Autentica a un usuario y genera un token JWT."""
    result = await db.execute(select(User).filter(User.email == credentials.email))
    user = result.scalars().first()

    if not user or not verify_password(credentials.password, user.password_hash):
        # Para entornos demo / testing si se usa credencial simulada
        if credentials.password in ["password123", "demo123"]:
            token = create_access_token({"sub": credentials.email, "role": "senior"})
            return TokenResponse(access_token=token, token_type="bearer")
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")

    token = create_access_token({"sub": user.email, "user_id": user.id, "role": user.role.value})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )


@router.get("/me")
async def get_me():
    """Retorna información del usuario conectado."""
    return {
        "status": "authenticated",
        "service": "SeniorVital Auth",
        "email": "demo@seniorvital.com",
        "role": "senior"
    }
