import sqlite3
import os

db_path = 'database.db'
if not os.path.exists(db_path):
    print(f"Database file not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting database schema migration for 'user' table to make email nullable...")
        
        cursor.execute("PRAGMA foreign_keys=off;")
        cursor.execute("BEGIN TRANSACTION;")

        cursor.execute("PRAGMA table_info(user);")
        columns = cursor.fetchall()
        email_column_info = next((c for c in columns if c[1] == 'email'), None)
        
        if email_column_info and email_column_info[3] == 0:
            print("Email column is already nullable. No migration needed.")
            cursor.execute("ROLLBACK;")
        else:
            print("Email column is NOT nullable. Proceeding with migration.")
            cursor.execute("ALTER TABLE user RENAME TO user_old;")
            print("Renamed 'user' to 'user_old'.")

            create_table_sql = """
            CREATE TABLE user (
                id INTEGER NOT NULL PRIMARY KEY,
                username VARCHAR(64) NOT NULL,
                full_name VARCHAR(128),
                department VARCHAR(128),
                email VARCHAR(120),
                password_hash VARCHAR(128) NOT NULL,
                role VARCHAR(20) NOT NULL,
                parent_id INTEGER,
                CONSTRAINT uq_user_username UNIQUE (username),
                CONSTRAINT uq_user_email UNIQUE (email),
                FOREIGN KEY(parent_id) REFERENCES user (id)
            )
            """
            cursor.execute(create_table_sql)
            print("Created new 'user' table with nullable email column.")

            copy_data_sql = """
            INSERT INTO user (id, username, full_name, department, email, password_hash, role, parent_id)
            SELECT id, username, full_name, department, CASE WHEN email = '' THEN NULL ELSE email END, password_hash, role, parent_id
            FROM user_old;
            """
            cursor.execute(copy_data_sql)
            print(f"{cursor.rowcount} rows copied from 'user_old' to 'user'.")

            cursor.execute("DROP TABLE user_old;")
            print("Dropped 'user_old' table.")

            cursor.execute("COMMIT;")
            print("Schema migration committed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Rolling back transaction.")
        # In case of error, try to rollback
        try:
            conn.rollback()
        except:
            pass
    finally:
        try:
            cursor.execute("PRAGMA foreign_keys=on;")
        except:
            pass
        conn.close()
        print("Database connection closed.")