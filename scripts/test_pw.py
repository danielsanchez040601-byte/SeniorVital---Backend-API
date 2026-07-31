import bcrypt
hashed = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
print("New Hash:", hashed)
