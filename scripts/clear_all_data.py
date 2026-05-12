import sqlite3
import os

# Connect to the new database directly
db_path = 'new_database.db'

if not os.path.exists(db_path):
    print(f"Database file not found at: {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Tables to exclude from deletion (keep schema)
    exclude_tables = ['sqlite_sequence']  # SQLite internal table

    print(f"Clearing all data from tables in {db_path}...")

    for table in tables:
        table_name = table[0]
        if table_name not in exclude_tables:
            try:
                cursor.execute(f"DELETE FROM {table_name}")
                print(f"Cleared data from table: {table_name}")
            except Exception as e:
                print(f"Error clearing table {table_name}: {e}")

    # Reset auto-increment counters safely
    try:
        cursor.execute("DELETE FROM sqlite_sequence")
        print("Reset auto-increment counters.")
    except sqlite3.OperationalError:
        # This can happen if there are no auto-increment tables
        print("Could not reset auto-increment counters (sqlite_sequence table might not exist).")


    conn.commit()
    conn.close()

    print("\nAll data has been cleared from the database.")
    print("The database schema is preserved, but all records have been deleted.")
    print("You can now hand over the software with a clean database.")