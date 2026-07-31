from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).filter(models.User.email == user.email))
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Simulación de hashing
    fake_hashed_password = user.password + "notreallyhashed"
    
    new_user = models.User(
        email=user.email,
        password_hash=fake_hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/{user_id}/senior-profile", response_model=schemas.SeniorProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_senior_profile(user_id: int, profile: schemas.SeniorProfileBase, db: AsyncSession = Depends(get_db)):
    # Verify user exists and is a senior
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.role != models.RoleEnum.SENIOR:
        raise HTTPException(status_code=400, detail="User is not a senior")

    # Check if profile already exists
    profile_result = await db.execute(select(models.SeniorProfile).filter(models.SeniorProfile.user_id == user_id))
    db_profile = profile_result.scalars().first()
    if db_profile:
        raise HTTPException(status_code=400, detail="Profile already exists for this user")

    new_profile = models.SeniorProfile(
        user_id=user_id,
        **profile.model_dump()
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    return new_profile

@router.get("/{user_id}/senior-profile", response_model=schemas.SeniorProfileResponse)
async def get_senior_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.SeniorProfile).filter(models.SeniorProfile.user_id == user_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
