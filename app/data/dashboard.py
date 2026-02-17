from typing import Any

from app.core.config import settings
from app.data.sqlite import conn


async def dashboard_stats(db: Any):
    if settings.db_backend != "sqlite":
        total_students = await db.students.count_documents({})
        accepted = await db.students.count_documents({"status_name": "Accepté"})
        return {"total_students": total_students, "accepted_students": accepted}

    c = conn()
    try:
        cur = c.execute("SELECT COUNT(1) AS c FROM students")
        total = int(cur.fetchone()["c"])

        cur2 = c.execute(
            """
            SELECT COUNT(1) AS c
            FROM students s
            JOIN statuses st ON st.id = s.status_id
            WHERE st.name = ?
            """,
            ("Accepté",),
        )
        accepted = int(cur2.fetchone()["c"])

        return {"total_students": total, "accepted_students": accepted}
    finally:
        c.close()
