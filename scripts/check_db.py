import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

# Check alembic_version
try:
    cursor.execute("SELECT * FROM alembic_version")
    version = cursor.fetchall()
    print("Alembic version:", version)
except sqlite3.OperationalError as e:
    print("Alembic version table error:", e)

conn.close()
