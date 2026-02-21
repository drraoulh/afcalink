import sqlite3
import os

db_path = "dev.db"

if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
try:
    cur = conn.execute("SELECT id, full_name, email, role FROM users")
    rows = cur.fetchall()
    print("Users found in database:")
    for row in rows:
        print(f"ID: {row['id']} | Name: {row['full_name']} | Email: {row['email']} | Role: {row['role']}")
finally:
    conn.close()
