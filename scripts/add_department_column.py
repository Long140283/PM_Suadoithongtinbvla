import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE patient ADD COLUMN department VARCHAR(128);")
    print("Column 'department' added to 'patient' table.")
except sqlite3.OperationalError as e:
    print(f"Error adding column: {e}")

conn.commit()
conn.close()
