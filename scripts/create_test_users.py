import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.users import create_user
from app.db import get_db

async def main():
    db = get_db()
    
    # Direct SQLite connection to cleanup and ensure consistency
    from app.data.sqlite import conn
    c = conn()
    try:
        # Delete existing test accounts to avoid "email already exists" errors
        emails = ["admin@afcalink.com", "agent@afcalink.com", "compta@afcalink.com"]
        for email in emails:
            c.execute("DELETE FROM users WHERE email=?", (email.lower(),))
        c.commit()
    finally:
        c.close()

    print("Creating test users...")
    
    # 1. Admin
    try:
        await create_user(db, full_name="Admin Principal", email="admin@afcalink.com", password="password123", role="admin")
        print("Admin created: admin@afcalink.com / password123")
    except Exception as e:
        print(f"Admin error: {e}")

    # 2. Agent
    try:
        await create_user(db, full_name="Agent Commercial", email="agent@afcalink.com", password="password123", role="agent")
        print("Agent created: agent@afcalink.com / password123")
    except Exception as e:
        print(f"Agent error: {e}")

    # 3. Accountant
    try:
        await create_user(db, full_name="Comptable Interne", email="compta@afcalink.com", password="password123", role="accountant")
        print("Accountant created: compta@afcalink.com / password123")
    except Exception as e:
        print(f"Accountant error: {e}")

    print("Test users creation sequence finished.")

if __name__ == "__main__":
    asyncio.run(main())
