import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

tables_to_drop = ['template', 'audit_log', 'attachment']

for table in tables_to_drop:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"Dropped table {table}")
    except Exception as e:
        print(f"Error dropping table {table}: {e}")

conn.commit()
conn.close()
