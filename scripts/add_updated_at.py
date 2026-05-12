import sqlite3
import os
from datetime import datetime

db_path = 'new_database.db'
if not os.path.exists(db_path):
    print(f"Database file not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(form_submission)")
        columns = [c[1] for c in cursor.fetchall()]
        if 'updated_at' not in columns:
            print("Adding updated_at column to form_submission...")
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
            cursor.execute(f"ALTER TABLE form_submission ADD COLUMN updated_at DATETIME DEFAULT '{now}'")
            cursor.execute("UPDATE form_submission SET updated_at = submitted_at WHERE updated_at IS NULL OR updated_at = ''")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column updated_at already exists.")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
