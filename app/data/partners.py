from typing import Any, List, Dict, Optional
from datetime import datetime
from app.core.config import settings
from app.data.sqlite import conn

async def list_partners(db: Any, search: Optional[str] = None) -> List[Dict[str, Any]]:
    if settings.db_backend != "sqlite": return []
    c = conn()
    try:
        query = "SELECT * FROM partners"
        params = []
        if search:
            query += " WHERE name LIKE ? OR country LIKE ? OR contact_person LIKE ?"
            s = f"%{search}%"
            params = [s, s, s]
        query += " ORDER BY name ASC"
        cur = c.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        c.close()

async def create_partner(
    db: Any,
    name: str,
    country: str,
    contact_person: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    website: Optional[str] = None,
    notes: Optional[str] = None
):
    if settings.db_backend != "sqlite": return None
    c = conn()
    try:
        cur = c.execute(
            """
            INSERT INTO partners (name, country, contact_person, email, phone, website, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, country, contact_person, email, phone, website, notes, datetime.utcnow().isoformat())
        )
        c.commit()
        return cur.lastrowid
    finally:
        c.close()

async def delete_partner(db: Any, partner_id: int):
    if settings.db_backend != "sqlite": return
    c = conn()
    try:
        c.execute("DELETE FROM partners WHERE id = ?", (partner_id,))
        c.commit()
    finally:
        c.close()
