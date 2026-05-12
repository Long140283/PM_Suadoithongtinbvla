import os
import shutil

DB_PATH = 'database.db'
MIGRATIONS_PATH = 'migrations'

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"Deleted {DB_PATH}")

if os.path.exists(MIGRATIONS_PATH):
    shutil.rmtree(MIGRATIONS_PATH)
    print(f"Deleted {MIGRATIONS_PATH}")