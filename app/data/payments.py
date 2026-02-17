from datetime import datetime
from typing import Any

from app.core.config import settings
from app.data.sqlite import conn


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


async def list_payments(db: Any):
    if settings.db_backend != "sqlite":
        cur = db.payments.find({}).sort("payment_date", -1)
        return [p async for p in cur]

    c = conn()
    try:
        cur = c.execute(
            """
            SELECT p.*, s.full_name AS student_name
            FROM payments p
            JOIN students s ON s.id = p.student_id
            ORDER BY p.payment_date DESC, p.id DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]
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
        async for p in db.payments.find({"student_id": student_id}):
            paid += int(p.get("amount", 0) or 0)
        return {"paid": paid}

    c = conn()
    try:
        cur = c.execute("SELECT COALESCE(SUM(amount),0) AS paid FROM payments WHERE student_id=?", (student_id,))
        paid = int(cur.fetchone()["paid"])
        return {"paid": paid}
    finally:
        c.close()
