from datetime import datetime
from typing import Any, Optional

from app.core.config import settings
from app.data.sqlite import conn


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


async def list_students(db: Any, *, status_id: Optional[int] = None, agent_name: Optional[str] = None, search: Optional[str] = None):
    if settings.db_backend != "sqlite":
        q = {}
        if status_id is not None:
            q["status_id"] = status_id
        if agent_name:
            q["agent_name"] = agent_name
        if search:
            q["$or"] = [
                {"full_name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}}
            ]
        cur = db.students.find(q).sort("created_at", -1)
        return [s async for s in cur]

    c = conn()
    try:
        query = """
            SELECT s.*, st.name AS status_name
            FROM students s
            LEFT JOIN statuses st ON st.id = s.status_id
            WHERE 1=1
        """
        params = []
        
        if status_id is not None:
            query += " AND s.status_id = ?"
            params.append(status_id)
            
        if agent_name:
            query += " AND s.agent_name = ?"
            params.append(agent_name)
            
        if search:
            query += " AND (s.full_name LIKE ? OR s.email LIKE ? OR s.phone LIKE ?)"
            s_val = f"%{search}%"
            params.extend([s_val, s_val, s_val])
            
        query += " ORDER BY s.created_at DESC"
        cur = c.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        c.close()


async def set_student_status(
    db: Any,
    *,
    student_id: int,
    to_status_id: Optional[int],
    changed_by_user_id: Optional[int],
):
    now = _now_iso()

    if settings.db_backend != "sqlite":
        student = await db.students.find_one({"_id": student_id})
        if not student:
            return
        from_status_id = student.get("status_id")
        await db.students.update_one({"_id": student_id}, {"$set": {"status_id": to_status_id, "updated_at": now}})
        await db.student_status_history.insert_one(
            {
                "student_id": student_id,
                "from_status_id": from_status_id,
                "to_status_id": to_status_id,
                "changed_by_user_id": changed_by_user_id,
                "changed_at": now,
            }
        )
        return

    c = conn()
    try:
        cur = c.execute("SELECT status_id FROM students WHERE id=? LIMIT 1", (student_id,))
        row = cur.fetchone()
        if not row:
            return
        from_status_id = row["status_id"]

        c.execute("UPDATE students SET status_id=?, updated_at=? WHERE id=?", (to_status_id, now, student_id))
        c.execute(
            """
            INSERT INTO student_status_history(student_id, from_status_id, to_status_id, changed_by_user_id, changed_at)
            VALUES(?,?,?,?,?)
            """,
            (student_id, from_status_id, to_status_id, changed_by_user_id, now),
        )
        c.commit()
    finally:
        c.close()


async def set_student_financial(db: Any, *, student_id: int, total_amount: int, currency: str):
    if settings.db_backend != "sqlite":
        await db.students.update_one(
            {"_id": student_id},
            {"$set": {"total_amount": int(total_amount or 0), "currency": (currency or "FCFA").strip(), "updated_at": _now_iso()}},
        )
        return

    c = conn()
    try:
        c.execute(
            "UPDATE students SET total_amount=?, currency=?, updated_at=? WHERE id=?",
            (int(total_amount or 0), (currency or "FCFA").strip(), _now_iso(), student_id),
        )
        c.commit()
    finally:
        c.close()


async def get_student(db: Any, student_id: int):
    if settings.db_backend != "sqlite":
        return await db.students.find_one({"_id": student_id})

    c = conn()
    try:
        cur = c.execute(
            """
            SELECT s.*, st.name AS status_name
            FROM students s
            LEFT JOIN statuses st ON st.id = s.status_id
            WHERE s.id=?
            LIMIT 1
            """,
            (student_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        c.close()


async def create_student(
    db: Any,
    *,
    full_name: str,
    phone: str,
    email: str,
    country: str,
    study_level: str,
    program_choice: str,
    university: str,
    status_id: Optional[int],
    agent_name: str,
    notes: Optional[str],
    changed_by_user_id: Optional[int],
    total_amount: int = 0,
    currency: str = "FCFA",
):
    if settings.db_backend != "sqlite":
        doc = {
            "full_name": full_name.strip(),
            "phone": phone.strip(),
            "email": email.lower().strip(),
            "country": country.strip(),
            "study_level": study_level.strip(),
            "program_choice": program_choice.strip(),
            "university": university.strip(),
            "status_id": status_id,
            "agent_name": agent_name.strip(),
            "total_amount": int(total_amount or 0),
            "currency": currency.strip() if currency else "FCFA",
            "notes": (notes or "").strip(),
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        result = await db.students.insert_one(doc)
        return str(result.inserted_id)

    now = _now_iso()
    c = conn()
    try:
        cur = c.execute(
            """
            INSERT INTO students(full_name, phone, email, country, study_level, program_choice, university, status_id, agent_name, total_amount, currency, notes, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                full_name.strip(),
                phone.strip(),
                email.lower().strip(),
                country.strip(),
                study_level.strip(),
                program_choice.strip(),
                university.strip(),
                status_id,
                agent_name.strip(),
                int(total_amount or 0),
                (currency or "FCFA").strip(),
                (notes or "").strip(),
                now,
                now,
            ),
        )
        student_id = int(cur.lastrowid)

        if status_id is not None:
            c.execute(
                """
                INSERT INTO student_status_history(student_id, from_status_id, to_status_id, changed_by_user_id, changed_at)
                VALUES(?,?,?,?,?)
                """,
                (student_id, None, status_id, changed_by_user_id, now),
            )

        c.commit()
        return student_id
    finally:
        c.close()


async def update_student(
    db: Any,
    *,
    student_id: int,
    full_name: str,
    phone: str,
    email: str,
    country: str,
    study_level: str,
    program_choice: str,
    university: str,
    status_id: Optional[int],
    agent_name: str,
    notes: Optional[str],
    changed_by_user_id: Optional[int],
):
    if settings.db_backend != "sqlite":
        await db.students.update_one(
            {"_id": student_id},
            {
                "$set": {
                    "full_name": full_name.strip(),
                    "phone": phone.strip(),
                    "email": email.lower().strip(),
                    "country": country.strip(),
                    "study_level": study_level.strip(),
                    "program_choice": program_choice.strip(),
                    "university": university.strip(),
                    "status_id": status_id,
                    "agent_name": agent_name.strip(),
                    "notes": (notes or "").strip(),
                    "updated_at": _now_iso(),
                }
            },
        )
        return

    now = _now_iso()
    c = conn()
    try:
        cur = c.execute("SELECT status_id FROM students WHERE id=? LIMIT 1", (student_id,))
        row = cur.fetchone()
        if not row:
            return
        old_status_id = row["status_id"]

        c.execute(
            """
            UPDATE students
            SET full_name=?, phone=?, email=?, country=?, study_level=?, program_choice=?, university=?, status_id=?, agent_name=?, notes=?, updated_at=?
            WHERE id=?
            """,
            (
                full_name.strip(),
                phone.strip(),
                email.lower().strip(),
                country.strip(),
                study_level.strip(),
                program_choice.strip(),
                university.strip(),
                status_id,
                agent_name.strip(),
                (notes or "").strip(),
                now,
                student_id,
            ),
        )

        if old_status_id != status_id:
            c.execute(
                """
                INSERT INTO student_status_history(student_id, from_status_id, to_status_id, changed_by_user_id, changed_at)
                VALUES(?,?,?,?,?)
                """,
                (student_id, old_status_id, status_id, changed_by_user_id, now),
            )

        c.commit()
    finally:
        c.close()


async def delete_student(db: Any, student_id: int):
    if settings.db_backend != "sqlite":
        await db.students.delete_one({"_id": student_id})
        return

    c = conn()
    try:
        c.execute("DELETE FROM student_status_history WHERE student_id=?", (student_id,))
        c.execute("DELETE FROM students WHERE id=?", (student_id,))
        c.commit()
    finally:
        c.close()


async def list_student_history(db: Any, student_id: int):
    if settings.db_backend != "sqlite":
        cur = db.student_status_history.find({"student_id": student_id}).sort("changed_at", -1)
        return [h async for h in cur]

    c = conn()
    try:
        cur = c.execute(
            """
            SELECT h.id, h.student_id, h.from_status_id, h.to_status_id, h.changed_by_user_id, h.changed_at,
                   s_from.name AS from_status_name,
                   s_to.name AS to_status_name
            FROM student_status_history h
            LEFT JOIN statuses s_from ON s_from.id = h.from_status_id
            LEFT JOIN statuses s_to ON s_to.id = h.to_status_id
            WHERE h.student_id=?
            ORDER BY h.changed_at DESC
            """,
            (student_id,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        c.close()
