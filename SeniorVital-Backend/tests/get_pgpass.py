"""Ayudante para extraer la contraseña de PostgreSQL de la base de datos SQLite de pgAdmin."""
import os
import sqlite3

db_path = os.path.expanduser("~/AppData/Roaming/pgadmin/pgadmin4.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])

# Try common table names
for tbl in ["server", "servers", "pgadmin_servers"]:
    try:
        rows = cursor.execute(f"SELECT * FROM {tbl}").fetchall()
        print(f"\n{tbl} table:")
        desc = [d[0] for d in cursor.description]
        print("Columns:", desc)
        for row in rows:
            print(dict(zip(desc, row)))
    except Exception as e:
        print(f"{tbl}: {e}")

conn.close()
