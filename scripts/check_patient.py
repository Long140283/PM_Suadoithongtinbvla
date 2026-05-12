import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Get schema of patient table
cursor.execute("PRAGMA table_info(patient)")
columns = cursor.fetchall()
print("Patient table columns:")
for col in columns:
    print(col)

conn.close()
