from datetime import datetime
from typing import Any

from app.core.config import settings
from app.data.sqlite import conn


def _seed_default_statuses() -> None:
    defaults = [
        ("Prospect", 1, 10),
        ("Dossier en préparation", 1, 20),
        ("Envoyé", 1, 30),
        ("Accepté", 1, 40),
        ("Refusé", 1, 50),
        ("Visa obtenu", 1, 60),
        ("Voyage effectué", 1, 70),
    ]

    c = conn()
    try:
        cur = c.execute("SELECT COUNT(1) AS c FROM statuses")
        row = cur.fetchone()
        if row and int(row["c"]) > 0:
            return

        for name, active, sort_order in defaults:
            c.execute(
                "INSERT INTO statuses(name, active, sort_order) VALUES(?,?,?)",
                (name, active, sort_order),
            )
        c.commit()
    finally:
        c.close()


async def list_statuses(db: Any):
    if settings.db_backend != "sqlite":
        cur = db.statuses.find({"active": True}).sort("sort_order", 1)
        return [s async for s in cur]

    _seed_default_statuses()
    c = conn()
    try:
        cur = c.execute(
            "SELECT id, name, active, sort_order FROM statuses WHERE active=1 ORDER BY sort_order ASC, name ASC"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        c.close()


async def get_status_by_id(db: Any, status_id: int):
    if settings.db_backend != "sqlite":
        return await db.statuses.find_one({"_id": status_id})

    c = conn()
    try:
        cur = c.execute(
            "SELECT id, name, active, sort_order FROM statuses WHERE id=? LIMIT 1",
            (status_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        c.close()
