from datetime import datetime
from typing import Any

from app.core.config import settings
from app.data.sqlite import conn


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


async def list_student_documents(db: Any, student_id: int):
    if settings.db_backend != "sqlite":
        cur = db.student_documents.find({"student_id": student_id}).sort("uploaded_at", -1)
        return [d async for d in cur]

    c = conn()
    try:
        cur = c.execute(
            """
            SELECT id, student_id, doc_type, original_filename, stored_filename, stored_path,
                   size_bytes, uploaded_by_user_id, uploaded_at
            FROM student_documents
            WHERE student_id=?
            ORDER BY uploaded_at DESC
            """,
            (student_id,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        c.close()


async def get_student_document(db: Any, document_id: int):
    if settings.db_backend != "sqlite":
        return await db.student_documents.find_one({"_id": document_id})

    c = conn()
    try:
        cur = c.execute(
            """
            SELECT id, student_id, doc_type, original_filename, stored_filename, stored_path,
                   size_bytes, uploaded_by_user_id, uploaded_at
            FROM student_documents
            WHERE id=?
            LIMIT 1
            """,
            (document_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        c.close()


async def add_student_document(
    db: Any,
    *,
    student_id: int,
    doc_type: str,
    original_filename: str,
    stored_filename: str,
    stored_path: str,
    size_bytes: int,
    uploaded_by_user_id: int | None,
):
    if settings.db_backend != "sqlite":
        result = await db.student_documents.insert_one(
            {
                "student_id": student_id,
                "doc_type": doc_type,
                "original_filename": original_filename,
                "stored_filename": stored_filename,
                "stored_path": stored_path,
                "size_bytes": size_bytes,
                "uploaded_by_user_id": uploaded_by_user_id,
                "uploaded_at": _now_iso(),
            }
        )
        return str(result.inserted_id)

    c = conn()
    try:
        cur = c.execute(
            """
            INSERT INTO student_documents(student_id, doc_type, original_filename, stored_filename, stored_path, size_bytes, uploaded_by_user_id, uploaded_at)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                student_id,
                doc_type.strip(),
                original_filename,
                stored_filename,
                stored_path,
                int(size_bytes),
                uploaded_by_user_id,
                _now_iso(),
            ),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()


async def delete_student_document(db: Any, document_id: int):
    if settings.db_backend != "sqlite":
        await db.student_documents.delete_one({"_id": document_id})
        return

    c = conn()
    try:
        c.execute("DELETE FROM student_documents WHERE id=?", (document_id,))
        c.commit()
    finally:
        c.close()
