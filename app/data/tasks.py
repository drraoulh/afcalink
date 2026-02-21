from typing import Any, List, Optional
from datetime import datetime
from app.core.config import settings
from app.data.sqlite import conn

def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")

async def list_tasks(db: Any, *, user_id: Optional[int] = None, status: Optional[str] = None):
    if settings.db_backend != "sqlite":
        # Mongo placeholder
        return []

    c = conn()
    try:
        query = """
            SELECT t.*, u.full_name as assigned_to_name, s.full_name as student_name
            FROM tasks t
            LEFT JOIN users u ON u.id = t.assigned_to_user_id
            LEFT JOIN students s ON s.id = t.student_id
            WHERE 1=1
        """
        params = []
        if user_id:
            query += " AND t.assigned_to_user_id = ?"
            params.append(user_id)
        if status:
            query += " AND t.status = ?"
            params.append(status)
            
        query += " ORDER BY t.due_date ASC, t.priority DESC"
        cur = c.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        c.close()

async def create_task(
    db: Any,
    *,
    title: str,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: str = "medium",
    status: str = "pending",
    assigned_to_user_id: Optional[int] = None,
    student_id: Optional[int] = None
):
    if settings.db_backend != "sqlite":
        return None

    now = _now_iso()
    c = conn()
    try:
        cur = c.execute(
            """
            INSERT INTO tasks(title, description, due_date, priority, status, assigned_to_user_id, student_id, created_at)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (title.strip(), (description or "").strip(), due_date, priority, status, assigned_to_user_id, student_id, now)
        )
        c.commit()
        return cur.lastrowid
    finally:
        c.close()

async def update_task_status(db: Any, task_id: int, status: str):
    if settings.db_backend != "sqlite":
        return

    now = _now_iso()
    c = conn()
    try:
        if status == "completed":
            c.execute("UPDATE tasks SET status=?, completed_at=? WHERE id=?", (status, now, task_id))
        else:
            c.execute("UPDATE tasks SET status=?, completed_at=NULL WHERE id=?", (status, task_id))
        c.commit()
    finally:
        c.close()

async def delete_task(db: Any, task_id: int):
    if settings.db_backend != "sqlite":
        return

    c = conn()
    try:
        c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        c.commit()
    finally:
        c.close()
