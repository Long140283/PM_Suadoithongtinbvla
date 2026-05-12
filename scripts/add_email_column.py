import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Add email column to user table
try:
    cursor.execute("ALTER TABLE user ADD COLUMN email VARCHAR(120) NOT NULL DEFAULT ''")
    print("Email column added successfully.")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")

# Create unique index on email
try:
    cursor.execute("CREATE UNIQUE INDEX ix_user_email ON user (email)")
    print("Unique constraint on email added.")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")

conn.commit()
conn.close()
