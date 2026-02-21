from typing import Any, List, Dict
from app.core.config import settings
from app.data.sqlite import conn

async def list_global_history(db: Any, limit: int = 50) -> List[Dict[str, Any]]:
    if settings.db_backend != "sqlite":
        # Placeholder for mongo
        return []

    c = conn()
    try:
        # Combined history: Status changes, Payments, and Task completions
        query = """
            SELECT 
                'status' as type,
                h.changed_at as timestamp,
                s.full_name as student_name,
                s.id as student_id,
                st_from.name as from_val,
                st_to.name as to_val,
                u.full_name as user_name
            FROM student_status_history h
            JOIN students s ON s.id = h.student_id
            LEFT JOIN statuses st_from ON st_from.id = h.from_status_id
            LEFT JOIN statuses st_to ON st_to.id = h.to_status_id
            LEFT JOIN users u ON u.id = h.changed_by_user_id
            
            UNION ALL
            
            SELECT 
                'payment' as type,
                p.created_at as timestamp,
                s.full_name as student_name,
                s.id as student_id,
                p.payment_type as from_val,
                CAST(p.amount AS TEXT) || ' ' || p.currency as to_val,
                u.full_name as user_name
            FROM payments p
            JOIN students s ON s.id = p.student_id
            LEFT JOIN users u ON u.id = p.created_by_user_id
            
            UNION ALL
            
            SELECT 
                'task' as type,
                t.completed_at as timestamp,
                COALESCE(s.full_name, 'Système') as student_name,
                t.student_id as student_id,
                t.title as from_val,
                'Terminé' as to_val,
                u.full_name as user_name
            FROM tasks t
            LEFT JOIN students s ON s.id = t.student_id
            LEFT JOIN users u ON u.id = t.assigned_to_user_id
            WHERE t.status = 'completed' AND t.completed_at IS NOT NULL

            ORDER BY timestamp DESC
            LIMIT ?
        """
        cur = c.execute(query, (limit,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        c.close()
