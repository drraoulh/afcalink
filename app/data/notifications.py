from typing import Any, List, Dict
from datetime import datetime
from app.core.config import settings
from app.data.sqlite import conn

async def create_notification(
    db: Any, 
    user_id: int, 
    title: str, 
    message: str, 
    type: str = "info", 
    link: str = None
):
    now = datetime.utcnow().isoformat()
    if settings.db_backend == "sqlite":
        c = conn()
        try:
            c.execute(
                """
                INSERT INTO notifications (user_id, title, message, type, link, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, title, message, type, link, now)
            )
            c.commit()
        finally:
            c.close()
    else:
        # Mongo placeholder
        await db.notifications.insert_one({
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": type,
            "link": link,
            "is_read": False,
            "created_at": now
        })

async def list_notifications(db: Any, user_id: int, limit: int = 10, unread_only: bool = False):
    if settings.db_backend == "sqlite":
        c = conn()
        try:
            query = "SELECT * FROM notifications WHERE user_id = ?"
            params = [user_id]
            if unread_only:
                query += " AND is_read = 0"
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cur = c.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
        finally:
            c.close()
    else:
        q = {"user_id": user_id}
        if unread_only: q["is_read"] = False
        cursor = db.notifications.find(q).sort("created_at", -1).limit(limit)
        return [dict(n) async for n in cursor]

async def mark_as_read(db: Any, notification_id: int):
    if settings.db_backend == "sqlite":
        c = conn()
        try:
            c.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
            c.commit()
        finally:
            c.close()
    else:
        await db.notifications.update_one({"_id": notification_id}, {"$set": {"is_read": True}})

async def mark_all_as_read(db: Any, user_id: int):
    if settings.db_backend == "sqlite":
        c = conn()
        try:
            c.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
            c.commit()
        finally:
            c.close()
    else:
        await db.notifications.update_many({"user_id": user_id}, {"$set": {"is_read": True}})

async def count_unread(db: Any, user_id: int) -> int:
    if settings.db_backend == "sqlite":
        c = conn()
        try:
            cur = c.execute("SELECT COUNT(*) as c FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,))
            row = cur.fetchone()
            return row["c"] if row else 0
        finally:
            c.close()
    else:
        return await db.notifications.count_documents({"user_id": user_id, "is_read": False})

async def notify_admins(db: Any, title: str, message: str, type: str = "info", link: str = None):
    # Get all admins
    if settings.db_backend == "sqlite":
        c = conn()
        try:
            cur = c.execute("SELECT id FROM users WHERE role = 'admin' AND active = 1")
            admin_ids = [r["id"] for r in cur.fetchall()]
        finally:
            c.close()
    else:
        cursor = db.users.find({"role": "admin", "active": True})
        admin_ids = [u["_id"] async for u in cursor]
        
    for aid in admin_ids:
        await create_notification(db, aid, title, message, type, link)

async def notify_role(db: Any, role: str, title: str, message: str, type: str = "info", link: str = None):
    if settings.db_backend == "sqlite":
        c = conn()
        try:
            cur = c.execute("SELECT id FROM users WHERE role = ? AND active = 1", (role,))
            uids = [r["id"] for r in cur.fetchall()]
        finally:
            c.close()
    else:
        cursor = db.users.find({"role": role, "active": True})
        uids = [u["_id"] async for u in cursor]
        
    for uid in uids:
        await create_notification(db, uid, title, message, type, link)
