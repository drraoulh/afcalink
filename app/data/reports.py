from typing import Any, Dict, List
from datetime import datetime
from app.core.config import settings
from app.data.sqlite import conn

async def daily_report_data(db: Any, date_str: str | None = None) -> Dict[str, Any]:
    if not date_str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
    if settings.db_backend != "sqlite":
        # Placeholder for mongo
        return {"date": date_str, "students": [], "payments": [], "status_changes": []}

    c = conn()
    try:
        # 1. New Students
        cur_students = c.execute(
            "SELECT * FROM students WHERE substr(created_at, 1, 10) = ? ORDER BY created_at DESC",
            (date_str,)
        )
        students = [dict(r) for r in cur_students.fetchall()]

        # 2. Payments
        cur_payments = c.execute(
            """
            SELECT p.*, s.full_name as student_name
            FROM payments p
            JOIN students s ON s.id = p.student_id
            WHERE substr(p.payment_date, 1, 10) = ? AND p.payment_status = 'received'
            ORDER BY p.id DESC
            """,
            (date_str,)
        )
        payments = [dict(r) for r in cur_payments.fetchall()]

        # 3. Status Changes
        cur_history = c.execute(
            """
            SELECT h.*, s.full_name as student_name, st_from.name as from_name, st_to.name as to_name
            FROM student_status_history h
            JOIN students s ON s.id = h.student_id
            LEFT JOIN statuses st_from ON st_from.id = h.from_status_id
            LEFT JOIN statuses st_to ON st_to.id = h.to_status_id
            WHERE substr(h.changed_at, 1, 10) = ?
            ORDER BY h.changed_at DESC
            """,
            (date_str,)
        )
        status_changes = [dict(r) for r in cur_history.fetchall()]

        total_received = sum(int(p["amount"]) for p in payments)

        return {
            "date": date_str,
            "students": students,
            "payments": payments,
            "status_changes": status_changes,
            "total_received": total_received
        }
    finally:
        c.close()
