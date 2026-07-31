import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async def migrate():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE daily_routines ADD COLUMN exercises_data JSON DEFAULT '[]'::json;"))
            print("Added exercises_data")
        except Exception as e:
            print("exercises_data might already exist:", e)
            
        try:
            await conn.execute(text("ALTER TABLE daily_routines ADD COLUMN warmup_data JSON DEFAULT '[]'::json;"))
            print("Added warmup_data")
        except Exception as e:
            print("warmup_data might already exist:", e)
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
