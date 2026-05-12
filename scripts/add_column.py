import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Add role column to user table
cursor.execute("ALTER TABLE user ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'staff'")

# Update existing admin user to have role 'admin'
cursor.execute("UPDATE user SET role = 'admin' WHERE username = 'admin'")

conn.commit()
conn.close()

print("Database updated: added role column and set admin role.")
