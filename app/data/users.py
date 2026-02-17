import sqlite3
from typing import Any

from bson import ObjectId

from app.core.config import settings
from app.data.sqlite import conn
from app.security import hash_password


async def count_users(db: Any) -> int:
    if settings.db_backend == "sqlite":
        c = conn()
        try:
            cur = c.execute("SELECT COUNT(1) AS c FROM users")
            row = cur.fetchone()
            return int(row["c"]) if row else 0
        finally:
            c.close()

    return await db.users.count_documents({})


async def create_user(db: Any, *, full_name: str, email: str, password: str, role: str) -> str:
    email_norm = email.lower().strip()

    if settings.db_backend == "sqlite":
        c = conn()
        try:
            cur = c.execute(
                "INSERT INTO users(full_name, email, password_hash, role, active) VALUES(?,?,?,?,1)",
                (full_name.strip(), email_norm, hash_password(password), role),
            )
            c.commit()
            return str(cur.lastrowid)
        finally:
            c.close()

    result = await db.users.insert_one(
        {
            "full_name": full_name.strip(),
            "email": email_norm,
            "password_hash": hash_password(password),
            "role": role,
            "active": True,
        }
    )
    return str(result.inserted_id)


async def get_user_by_email(db: Any, email: str):
    email_norm = email.lower().strip()

    if settings.db_backend == "sqlite":
        c = conn()
        try:
            cur = c.execute(
                "SELECT id, full_name, email, password_hash, role, active FROM users WHERE email=? LIMIT 1",
                (email_norm,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            c.close()

    return await db.users.find_one({"email": email_norm})


async def get_user_by_id(db: Any, user_id: str):
    if settings.db_backend == "sqlite":
        try:
            uid = int(user_id)
        except Exception:
            return None

        c = conn()
        try:
            cur = c.execute(
                "SELECT id, full_name, email, password_hash, role, active FROM users WHERE id=? LIMIT 1",
                (uid,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            c.close()

    try:
        oid = ObjectId(user_id)
    except Exception:
        return None

    return await db.users.find_one({"_id": oid})


async def ensure_bootstrap_admin(db: Any) -> None:
    if settings.db_backend != "sqlite":
        return

    if await count_users(db) > 0:
        return

    await create_user(
        db,
        full_name="Admin",
        email=settings.bootstrap_admin_email,
        password=settings.bootstrap_admin_password,
        role="admin",
    )
