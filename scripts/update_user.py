import asyncio
import os
import sys
import json
import bcrypt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from seniorvital_shared import init_pool, get_pool, close_pool

async def main():
    await init_pool(owner="script")
    pool = await get_pool()
    
    hashed = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
    
    profile_json = json.dumps({
        "age": 70,
        "weight_kg": 65,
        "height_cm": 158,
        "fitness_level": "principiante",
        "goals": ["movilidad"],
        "medical_restrictions": ["artrosis_rodilla"],
        "equipment": ["silla"],
        "preferred_schedule": "10:00"
    })
    
    async with pool.acquire() as conn:
        # Check if senior user exists
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", "senior@seniorvital.com")
        if user:
            print("User senior@seniorvital.com exists. Updating password and profile...")
            await conn.execute(
                "UPDATE users SET password = $1, profile = $2 WHERE email = $3",
                hashed,
                profile_json,
                "senior@seniorvital.com"
            )
        else:
            print("User senior@seniorvital.com does not exist. Inserting...")
            await conn.execute(
                "INSERT INTO users (email, role, profile, password) VALUES ($1, $2, $3, $4)",
                "senior@seniorvital.com",
                "senior",
                profile_json,
                hashed
            )
            
        # Verify the updated password can be checked with checkpw
        updated_user = await conn.fetchrow("SELECT password FROM users WHERE email = $1", "senior@seniorvital.com")
        db_hash = updated_user["password"]
        correct = bcrypt.checkpw(b"password123", db_hash.encode("utf-8"))
        print(f"Password in DB verification result: {correct}")
        
    await close_pool(owner="script")

if __name__ == "__main__":
    asyncio.run(main())
