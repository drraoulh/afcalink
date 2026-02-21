from typing import Any, List
from datetime import datetime
from app.data.sqlite import conn
from app.core.config import settings

def _now_iso():
    return datetime.now().isoformat()

async def create_daily_report(
    db: Any,
    *,
    user_id: int,
    report_date: str,
    content: str,
    tasks_completed: str = "",
    prospects_met: int = 0,
    payments_collected: int = 0
):
    now = _now_iso()
    if settings.db_backend == "sqlite":
        c = conn()
        try:
            c.execute(
                """
                INSERT INTO daily_reports (user_id, report_date, content, tasks_completed, prospects_met, payments_collected, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, report_date, content, tasks_completed, prospects_met, payments_collected, now)
            )
            c.commit()
        finally:
            c.close()
    else:
        # Mock for mongo
        await db.daily_reports.insert_one({
            "user_id": user_id,
            "report_date": report_date,
            "content": content,
            "tasks_completed": tasks_completed,
            "prospects_met": prospects_met,
            "payments_collected": payments_collected,
            "created_at": now
        })

async def list_user_reports(db: Any, user_id: int):
    if settings.db_backend == "sqlite":
        c = conn()
        try:
            cur = c.execute(
                "SELECT * FROM daily_reports WHERE user_id = ? ORDER BY report_date DESC LIMIT 10",
                (user_id,)
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            c.close()
    else:
        cursor = db.daily_reports.find({"user_id": user_id}).sort("report_date", -1).limit(10)
        return [dict(u) async for u in cursor]

async def list_all_reports(db: Any, limit: int = 20, user_id: int | None = None, report_date: str | None = None):
    if settings.db_backend == "sqlite":
        c = conn()
        try:
            query = """
                SELECT r.*, u.full_name as agent_name 
                FROM daily_reports r
                JOIN users u ON u.id = r.user_id
                WHERE 1=1
            """
            params = []
            if user_id:
                query += " AND r.user_id = ?"
                params.append(user_id)
            if report_date:
                query += " AND r.report_date = ?"
                params.append(report_date)
            
            query += " ORDER BY r.created_at DESC LIMIT ?"
            params.append(limit)
            
            cur = c.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
        finally:
            c.close()
    else:
        # Simplistic mongo join with filters
        q = {}
        if user_id: q["user_id"] = user_id
        if report_date: q["report_date"] = report_date
        
        reports = []
        cursor = db.daily_reports.find(q).sort("created_at", -1).limit(limit)
        async for r in cursor:
            user = await db.users.find_one({"_id": r["user_id"]})
            r["agent_name"] = user.get("full_name") if user else "Inconnu"
            reports.append(r)
        return reports
