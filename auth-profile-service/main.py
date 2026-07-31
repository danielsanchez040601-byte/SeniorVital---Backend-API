import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import asyncpg
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from contextlib import asynccontextmanager
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta

from seniorvital_shared import get_pool, HealthProfile, init_pool, close_pool

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
JWT_ALG = "HS256"
JWT_EXPIRY = timedelta(days=7)

security = HTTPBearer()


def create_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.utcnow() + JWT_EXPIRY}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        return jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(payload: dict = Depends(verify_token)) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", payload["sub"])
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(row)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool(owner="auth")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS password TEXT
        """)
    yield
    await close_pool(owner="auth")


app = FastAPI(
    title="Auth Profile Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "senior"
    profile: Optional[dict] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdate(BaseModel):
    profile: dict


class LinkCaregiverRequest(BaseModel):
    caregiver_email: EmailStr


@app.post("/auth/register")
async def register(req: RegisterRequest):
    if req.role not in ("senior", "caregiver", "admin"):
        raise HTTPException(status_code=400, detail="Rol no permitido")
    if req.profile:
        HealthProfile(**req.profile)
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", req.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email ya registrado")
        hashed = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        row = await conn.fetchrow(
            "INSERT INTO users (email, role, profile, password) VALUES ($1, $2, $3, $4) RETURNING id",
            req.email,
            req.role,
            json.dumps(req.profile or {}),
            hashed,
        )
    return {"id": str(row["id"]), "email": req.email, "role": req.role}


@app.post("/auth/login")
async def login(req: LoginRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", req.email)
        if not row or not bcrypt.checkpw(req.password.encode('utf-8'), row["password"].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        token = create_token(str(row["id"]))
        return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "id": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "profile": user["profile"],
        "linked_senior_id": str(user["linked_senior_id"]) if user.get("linked_senior_id") else None,
    }


@app.get("/auth/users")
async def list_users():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, email, role, profile, linked_senior_id, created_at FROM users")
        return [
            {
                "id": str(r["id"]),
                "email": r["email"],
                "role": r["role"],
                "profile": json.loads(r["profile"]) if isinstance(r["profile"], str) else (r["profile"] or {}),
                "linked_senior_id": str(r["linked_senior_id"]) if r.get("linked_senior_id") else None,
                "created_at": r["created_at"].isoformat() if r["created_at"] else None
            }
            for r in rows
        ]


@app.put("/auth/profile")
async def update_profile(req: ProfileUpdate, user: dict = Depends(get_current_user)):
    if user["role"] not in ("senior", "admin"):
        raise HTTPException(status_code=403, detail="Only senior or admin can update profile")
    HealthProfile(**req.profile)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET profile = $1 WHERE id = $2",
            json.dumps(req.profile),
            user["id"],
        )
    return {"detail": "Profile updated"}


@app.post("/auth/link-caregiver")
async def link_caregiver(req: LinkCaregiverRequest, user: dict = Depends(get_current_user)):
    if user["role"] != "senior":
        raise HTTPException(status_code=403, detail="Only seniors can link caregivers")
    pool = await get_pool()
    async with pool.acquire() as conn:
        caregiver = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1 AND role = 'caregiver'", req.caregiver_email
        )
        if not caregiver:
            raise HTTPException(status_code=404, detail="Caregiver not found")
        linked_count = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE linked_senior_id = $1 AND role = 'caregiver'",
            user["id"],
        )
        if linked_count >= 3:
            raise HTTPException(status_code=400, detail="Senior already linked to max 3 caregivers")
        existing_link = await conn.fetchval(
            "SELECT linked_senior_id FROM users WHERE id = $1", caregiver["id"]
        )
        if existing_link:
            raise HTTPException(status_code=400, detail="Caregiver already linked to a senior")
        await conn.execute(
            "UPDATE users SET linked_senior_id = $1 WHERE id = $2",
            user["id"],
            caregiver["id"],
        )
    return {"detail": "Caregiver linked successfully"}
