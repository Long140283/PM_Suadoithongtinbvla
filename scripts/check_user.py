import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Get schema of user table
cursor.execute("PRAGMA table_info(user)")
columns = cursor.fetchall()
print("User table columns:")
for col in columns:
    print(col)

conn.close()
