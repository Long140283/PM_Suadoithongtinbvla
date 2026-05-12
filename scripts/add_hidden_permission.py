import sqlite3
import os

db_path = 'new_database.db'
if not os.path.exists(db_path):
    print(f"Database file not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(permission)")
        columns = [c[1] for c in cursor.fetchall()]
        if 'hidden' not in columns:
            print("Adding hidden column to permission table...")
            cursor.execute("ALTER TABLE permission ADD COLUMN hidden BOOLEAN DEFAULT 0")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column 'hidden' already exists.")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
