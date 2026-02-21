from datetime import datetime
from typing import Any

from app.core.config import settings
from app.data.sqlite import conn


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


async def list_payments(db: Any, *, agent_name: str | None = None):
    if settings.db_backend != "sqlite":
        if not agent_name:
            cur = db.payments.find({}).sort("payment_date", -1)
            return [p async for p in cur]

        student_ids = []
        async for s in db.students.find({"agent_name": agent_name}, {"_id": 1}):
            student_ids.append(s.get("_id"))
        if not student_ids:
            return []
        cur = db.payments.find({"student_id": {"$in": student_ids}}).sort("payment_date", -1)
        return [p async for p in cur]

    c = conn()
    try:
        if not agent_name:
            cur = c.execute(
                """
                SELECT p.*, s.full_name AS student_name
                FROM payments p
                JOIN students s ON s.id = p.student_id
                ORDER BY p.payment_date DESC, p.id DESC
                """
            )
        else:
            cur = c.execute(
                """
                SELECT p.*, s.full_name AS student_name
                FROM payments p
                JOIN students s ON s.id = p.student_id
                WHERE s.agent_name = ?
                ORDER BY p.payment_date DESC, p.id DESC
                """,
                (agent_name,),
            )
        return [dict(r) for r in cur.fetchall()]
    finally:
        c.close()


async def get_payment(db: Any, payment_id: int):
    if settings.db_backend != "sqlite":
        doc = await db.payments.find_one({"_id": payment_id})
        return doc

    c = conn()
    try:
        cur = c.execute("SELECT p.* FROM payments p WHERE p.id=? LIMIT 1", (payment_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        c.close()


async def list_payments_by_student(db: Any, student_id: int):
    if settings.db_backend != "sqlite":
        cur = db.payments.find({"student_id": student_id}).sort("payment_date", -1)
        return [p async for p in cur]

    c = conn()
    try:
        cur = c.execute(
            """
            SELECT p.*
            FROM payments p
            WHERE p.student_id=?
            ORDER BY p.payment_date DESC, p.id DESC
            """,
            (student_id,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        c.close()


async def create_payment(
    db: Any,
    *,
    student_id: int,
    payment_type: str,
    amount: int,
    currency: str,
    payment_mode: str,
    payment_date: str,
    payment_status: str,
    receipt_original_filename: str | None,
    receipt_stored_path: str | None,
    created_by_user_id: int | None,
):
    if settings.db_backend != "sqlite":
        result = await db.payments.insert_one(
            {
                "student_id": student_id,
                "payment_type": payment_type,
                "amount": amount,
                "currency": currency,
                "payment_mode": payment_mode,
                "payment_date": payment_date,
                "payment_status": payment_status,
                "receipt_original_filename": receipt_original_filename,
                "receipt_stored_path": receipt_stored_path,
                "created_by_user_id": created_by_user_id,
                "created_at": _now_iso(),
            }
        )
        return str(result.inserted_id)

    c = conn()
    try:
        cur = c.execute(
            """
            INSERT INTO payments(student_id, payment_type, amount, currency, payment_mode, payment_date, payment_status,
                                 receipt_original_filename, receipt_stored_path, created_by_user_id, created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                student_id,
                payment_type.strip(),
                int(amount),
                currency.strip(),
                payment_mode.strip(),
                payment_date.strip(),
                payment_status.strip(),
                receipt_original_filename,
                receipt_stored_path,
                created_by_user_id,
                _now_iso(),
            ),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()


async def totals_by_student(db: Any, student_id: int):
    if settings.db_backend != "sqlite":
        # simplistic placeholder for mongo mode
        paid = 0
        async for p in db.payments.find({"student_id": student_id, "payment_status": "received"}):
            paid += int(p.get("amount", 0) or 0)
        return {"paid": paid}

    c = conn()
    try:
        cur = c.execute(
            "SELECT COALESCE(SUM(amount),0) AS paid FROM payments WHERE student_id=? AND payment_status='received'",
            (student_id,),
        )
        paid = int(cur.fetchone()["paid"])
        return {"paid": paid}
    finally:
        c.close()

async def get_daily_payment_count(db: Any, agent_name: str) -> int:
    if settings.db_backend != "sqlite": return 0
    today = datetime.utcnow().strftime("%Y-%m-%d")
    c = conn()
    try:
        cur = c.execute(
            """
            SELECT COUNT(*) as count 
            FROM payments p
            JOIN students s ON s.id = p.student_id
            WHERE s.agent_name = ? AND p.created_at LIKE ?
            """,
            (agent_name, f"{today}%")
        )
        return cur.fetchone()["count"]
    finally:
        c.close()

async def confirm_payment(db: Any, payment_id: int):
    if settings.db_backend != "sqlite": return
    c = conn()
    try:
        c.execute("UPDATE payments SET payment_status = 'received' WHERE id = ?", (payment_id,))
        c.commit()
    finally:
        c.close()

async def list_pending_payments(db: Any, agent_id: int | None = None, filter_date: str | None = None):
    if settings.db_backend != "sqlite": return []
    c = conn()
    try:
        query = """
            SELECT p.*, s.full_name as student_name, s.agent_name
            FROM payments p
            JOIN students s ON s.id = p.student_id
            WHERE p.payment_status = 'pending'
        """
        params = []
        if agent_id:
            query += " AND s.agent_name IN (SELECT full_name FROM users WHERE id = ?)"
            params.append(agent_id)
        if filter_date:
            query += " AND p.payment_date = ?"
            params.append(filter_date)
            
        query += " ORDER BY p.payment_date DESC"
        cur = c.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        c.close()

async def count_pending_payments(db: Any) -> int:
    if settings.db_backend != "sqlite": return 0
    c = conn()
    try:
        cur = c.execute("SELECT COUNT(*) as count FROM payments WHERE payment_status = 'pending'")
        return cur.fetchone()["count"]
    finally:
        c.close()
