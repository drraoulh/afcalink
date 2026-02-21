from typing import Any, List, Optional
from datetime import datetime
from app.core.config import settings
from app.data.sqlite import conn

def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")

async def list_prospects(db: Any, *, agent_name: Optional[str] = None, search: Optional[str] = None):
    if settings.db_backend != "sqlite":
        # Placeholder for mongo
        return []

    c = conn()
    try:
        query = "SELECT * FROM prospects WHERE 1=1"
        params = []
        if agent_name:
            query += " AND (agent_name = ? OR agent_name IS NULL)"
            params.append(agent_name)
        if search:
            query += " AND (full_name LIKE ? OR phone LIKE ? OR email LIKE ?)"
            s_val = f"%{search}%"
            params.extend([s_val, s_val, s_val])
        
        query += " ORDER BY created_at DESC"
        cur = c.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        c.close()

async def get_prospect(db: Any, prospect_id: int):
    if settings.db_backend != "sqlite": return None
    c = conn()
    try:
        cur = c.execute("SELECT * FROM prospects WHERE id=?", (prospect_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        c.close()

async def create_prospect(
    db: Any,
    *,
    full_name: str,
    phone: str,
    email: Optional[str] = None,
    country_interest: Optional[str] = None,
    source: Optional[str] = None,
    agent_name: Optional[str] = None,
    notes: Optional[str] = None
):
    if settings.db_backend != "sqlite": return None
    now = _now_iso()
    c = conn()
    try:
        cur = c.execute(
            """
            INSERT INTO prospects (full_name, phone, email, country_interest, source, agent_name, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (full_name.strip(), phone.strip(), email, country_interest, source, agent_name, notes, now, now)
        )
        c.commit()
        return cur.lastrowid
    finally:
        c.close()

async def update_prospect_status(db: Any, prospect_id: int, status: str):
    if settings.db_backend != "sqlite": return
    now = _now_iso()
    c = conn()
    try:
        c.execute("UPDATE prospects SET status=?, updated_at=? WHERE id=?", (status, now, prospect_id))
        c.commit()
    finally:
        c.close()

async def delete_prospect(db: Any, prospect_id: int):
    if settings.db_backend != "sqlite": return
    c = conn()
    try:
        c.execute("DELETE FROM prospects WHERE id=?", (prospect_id,))
        c.commit()
    finally:
        c.close()

async def get_daily_prospect_count(db: Any, agent_name: str) -> int:
    if settings.db_backend != "sqlite": return 0
    today = datetime.utcnow().strftime("%Y-%m-%d")
    c = conn()
    try:
        cur = c.execute(
            "SELECT COUNT(*) as count FROM prospects WHERE agent_name = ? AND created_at LIKE ?",
            (agent_name, f"{today}%")
        )
        return cur.fetchone()["count"]
    finally:
        c.close()
