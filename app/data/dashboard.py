from typing import Any, Dict, List
from datetime import datetime, timedelta
from app.core.config import settings
from app.data.sqlite import conn

async def dashboard_stats(db: Any, user: dict | None = None) -> Dict[str, Any]:
    role = (user or {}).get("role")
    agent_name = (user or {}).get("full_name")
    user_id = (user or {}).get("id")
    is_agent = role == "agent" and bool(agent_name)
    
    now = datetime.utcnow()
    today_str = now.strftime("%Y-%m-%d")

    if settings.db_backend != "sqlite":
        # Simplified MongoDB implementation for Phase 2
        total_students = await db.students.count_documents({})
        if is_agent:
            total_students = await db.students.count_documents({"agent_name": agent_name})
            
        return {
            "scope_label": "Mes données" if is_agent else "Global",
            "total_students": total_students,
            "accepted_students": 0,
            "revenue_month": 0,
            "overdue_tasks": 0,
            "students_by_status_labels": [],
            "students_by_status_data": [],
            "revenue_labels": [],
            "revenue_data": []
        }

    c = conn()
    try:
        # 1. Basic Stats
        if not is_agent:
            cur = c.execute("SELECT COUNT(1) AS c FROM students")
            total = int(cur.fetchone()["c"])

            cur2 = c.execute(
                "SELECT COUNT(1) AS c FROM students s JOIN statuses st ON st.id = s.status_id WHERE st.name = ?",
                ("Accepté",)
            )
            accepted = int(cur2.fetchone()["c"])

            cur3 = c.execute(
                "SELECT COALESCE(SUM(amount),0) AS total FROM payments WHERE payment_status='received' AND substr(payment_date, 1, 7) = ?",
                (now.strftime("%Y-%m"),)
            )
            revenue_month = int(cur3.fetchone()["total"])
            
            # Overdue Tasks
            cur4 = c.execute("SELECT COUNT(1) AS c FROM tasks WHERE status != 'completed' AND due_date < ?", (today_str,))
            overdue_tasks = int(cur4.fetchone()["c"])
        else:
            cur = c.execute("SELECT COUNT(1) AS c FROM students WHERE agent_name=?", (agent_name,))
            total = int(cur.fetchone()["c"])

            cur2 = c.execute(
                "SELECT COUNT(1) AS c FROM students s JOIN statuses st ON st.id = s.status_id WHERE st.name = ? AND s.agent_name = ?",
                ("Accepté", agent_name)
            )
            accepted = int(cur2.fetchone()["c"])

            cur3 = c.execute(
                """
                SELECT COALESCE(SUM(p.amount),0) AS total
                FROM payments p
                JOIN students s ON s.id = p.student_id
                WHERE p.payment_status='received' AND substr(p.payment_date, 1, 7) = ? AND s.agent_name = ?
                """,
                (now.strftime("%Y-%m"), agent_name)
            )
            revenue_month = int(cur3.fetchone()["total"])
            
            cur4 = c.execute(
                "SELECT COUNT(1) AS c FROM tasks WHERE status != 'completed' AND due_date < ? AND assigned_to_user_id = ?",
                (today_str, user_id)
            )
            overdue_tasks = int(cur4.fetchone()["c"])

        # 2. Charts Data: Students by Status
        status_query = """
            SELECT st.name, COUNT(s.id) as count
            FROM statuses st
            LEFT JOIN students s ON s.status_id = st.id
        """
        if is_agent:
            status_query += " AND s.agent_name = ?"
            status_query += " GROUP BY st.id ORDER BY st.sort_order"
            cur_status = c.execute(status_query, (agent_name,))
        else:
            status_query += " GROUP BY st.id ORDER BY st.sort_order"
            cur_status = c.execute(status_query)
            
        status_rows = cur_status.fetchall()
        status_labels = [r["name"] for r in status_rows]
        status_data = [r["count"] for r in status_rows]

        # 3. Charts Data: Revenue Last 6 Months
        revenue_labels = []
        revenue_data = []
        for i in range(5, -1, -1):
            target_date = now - timedelta(days=i*30)
            ym = target_date.strftime("%Y-%m")
            revenue_labels.append(target_date.strftime("%b %Y"))
            
            if is_agent:
                cur_rev = c.execute(
                    """
                    SELECT COALESCE(SUM(p.amount),0) as total
                    FROM payments p
                    JOIN students s ON s.id = p.student_id
                    WHERE p.payment_status='received' AND substr(p.payment_date, 1, 7) = ? AND s.agent_name = ?
                    """,
                    (ym, agent_name)
                )
            else:
                cur_rev = c.execute(
                    "SELECT COALESCE(SUM(amount),0) as total FROM payments WHERE payment_status='received' AND substr(payment_date, 1, 7) = ?",
                    (ym,)
                )
            revenue_data.append(int(cur_rev.fetchone()["total"]))

        # 4. Agent Ranking (Admin Only)
        agent_ranking = []
        if not is_agent:
            cur_ranking = c.execute(
                """
                SELECT agent_name, COUNT(id) as total
                FROM students 
                GROUP BY agent_name 
                ORDER BY total DESC 
                LIMIT 5
                """
            )
            agent_ranking = [dict(r) for r in cur_ranking.fetchall()]

        # 5. Recent Activity Reports (Admin Only)
        recent_reports = []
        if not is_agent:
            cur_reports = c.execute(
                """
                SELECT r.*, u.full_name as agent_name 
                FROM daily_reports r
                JOIN users u ON u.id = r.user_id
                ORDER BY r.created_at DESC LIMIT 5
                """
            )
            recent_reports = [dict(r) for r in cur_reports.fetchall()]

        return {
            "scope_label": "Mes données" if is_agent else "Global",
            "total_students": total,
            "accepted_students": accepted,
            "revenue_month": revenue_month,
            "overdue_tasks": overdue_tasks,
            "students_by_status_labels": status_labels,
            "students_by_status_data": status_data,
            "revenue_labels": revenue_labels,
            "revenue_data": revenue_data,
            "agent_ranking": agent_ranking,
            "recent_reports": recent_reports
        }
    finally:
        c.close()
