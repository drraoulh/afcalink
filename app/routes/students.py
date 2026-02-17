from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from app.deps import db_dep
from app.deps import require_role
from app.data.documents import (
    add_student_document,
    delete_student_document,
    get_student_document,
    list_student_documents,
)
from app.data.statuses import list_statuses
from app.data.students import (
    create_student,
    delete_student,
    get_student,
    list_student_history,
    list_students,
    update_student,
)
from app.storage import save_upload
from app.templating import templates

router = APIRouter(prefix="/students", tags=["students"])


@router.get("")
async def students_list(request: Request, user=Depends(require_role("admin", "agent", "accountant")), db=Depends(db_dep)):
    students = await list_students(db)
    return templates.TemplateResponse(
        "students/list.html",
        {"request": request, "user": user, "students": students},
    )


@router.get("/new")
async def student_new_get(request: Request, user=Depends(require_role("admin", "agent")), db=Depends(db_dep)):
    statuses = await list_statuses(db)
    return templates.TemplateResponse(
        "students/form.html",
        {"request": request, "user": user, "student": None, "statuses": statuses},
    )


@router.post("/new")
async def student_new_post(
    request: Request,
    user=Depends(require_role("admin", "agent")),
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    country: str = Form(...),
    study_level: str = Form(...),
    program_choice: str = Form(...),
    university: str = Form(...),
    status_id: str = Form(""),
    agent_name: str = Form(...),
    notes: str = Form(""),
    db=Depends(db_dep),
):
    sid = int(status_id) if status_id else None
    changed_by = user.get("id") if "id" in user else None
    await create_student(
        db,
        full_name=full_name,
        phone=phone,
        email=email,
        country=country,
        study_level=study_level,
        program_choice=program_choice,
        university=university,
        status_id=sid,
        agent_name=agent_name,
        notes=notes,
        changed_by_user_id=changed_by,
    )
    return RedirectResponse(url="/students", status_code=303)


@router.get("/{student_id}")
async def student_view(request: Request, student_id: int, user=Depends(require_role("admin", "agent", "accountant")), db=Depends(db_dep)):
    student = await get_student(db, student_id)
    if not student:
        return RedirectResponse(url="/students", status_code=303)
    history = await list_student_history(db, student_id)
    documents = await list_student_documents(db, student_id)
    return templates.TemplateResponse(
        "students/view.html",
        {"request": request, "user": user, "student": student, "history": history, "documents": documents},
    )


@router.post("/{student_id}/documents")
async def student_document_upload(
    request: Request,
    student_id: int,
    user=Depends(require_role("admin", "agent", "accountant")),
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db=Depends(db_dep),
):
    if not file:
        raise HTTPException(status_code=400, detail="Missing file")

    allowed_exts = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"}
    filename = (file.filename or "").lower()
    ext = Path(filename).suffix
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Type de fichier non autorisé (PDF/DOC/DOCX/PNG/JPG)")

    allowed_ct = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/png",
        "image/jpeg",
    }
    if file.content_type and file.content_type not in allowed_ct:
        raise HTTPException(status_code=400, detail="Type de fichier non autorisé (PDF/DOC/DOCX/PNG/JPG)")

    original, stored, size = await save_upload(file)
    if size > 10 * 1024 * 1024:
        try:
            Path("uploads").joinpath(stored).unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    uploaded_by = user.get("id") if "id" in user else None
    await add_student_document(
        db,
        student_id=student_id,
        doc_type=doc_type,
        original_filename=original,
        stored_filename=stored,
        stored_path=str(Path("uploads") / stored),
        size_bytes=size,
        uploaded_by_user_id=uploaded_by,
    )
    return RedirectResponse(url=f"/students/{student_id}", status_code=303)


@router.get("/documents/{document_id}/download")
async def student_document_download(document_id: int, user=Depends(require_role("admin", "agent", "accountant")), db=Depends(db_dep)):
    doc = await get_student_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    path = Path(doc["stored_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing")
    return FileResponse(path, filename=doc["original_filename"], media_type="application/octet-stream")


@router.post("/documents/{document_id}/delete")
async def student_document_delete(document_id: int, user=Depends(require_role("admin", "agent")), db=Depends(db_dep)):
    doc = await get_student_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        Path(doc["stored_path"]).unlink(missing_ok=True)
    except Exception:
        pass
    await delete_student_document(db, document_id)
    return RedirectResponse(url=f"/students/{doc['student_id']}", status_code=303)


@router.get("/{student_id}/edit")
async def student_edit_get(request: Request, student_id: int, user=Depends(require_role("admin", "agent")), db=Depends(db_dep)):
    student = await get_student(db, student_id)
    if not student:
        return RedirectResponse(url="/students", status_code=303)
    statuses = await list_statuses(db)
    return templates.TemplateResponse(
        "students/form.html",
        {"request": request, "user": user, "student": student, "statuses": statuses},
    )


@router.post("/{student_id}/edit")
async def student_edit_post(
    request: Request,
    student_id: int,
    user=Depends(require_role("admin", "agent")),
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    country: str = Form(...),
    study_level: str = Form(...),
    program_choice: str = Form(...),
    university: str = Form(...),
    status_id: str = Form(""),
    agent_name: str = Form(...),
    notes: str = Form(""),
    db=Depends(db_dep),
):
    sid = int(status_id) if status_id else None
    changed_by = user.get("id") if "id" in user else None
    await update_student(
        db,
        student_id=student_id,
        full_name=full_name,
        phone=phone,
        email=email,
        country=country,
        study_level=study_level,
        program_choice=program_choice,
        university=university,
        status_id=sid,
        agent_name=agent_name,
        notes=notes,
        changed_by_user_id=changed_by,
    )
    return RedirectResponse(url=f"/students/{student_id}", status_code=303)


@router.post("/{student_id}/delete")
async def student_delete_post(request: Request, student_id: int, user=Depends(require_role("admin", "agent")), db=Depends(db_dep)):
    await delete_student(db, student_id)
    return RedirectResponse(url="/students", status_code=303)
