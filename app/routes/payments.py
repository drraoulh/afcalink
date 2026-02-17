from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from pathlib import Path

from app.deps import db_dep, require_role
from app.data.payments import create_payment, list_payments, list_payments_by_student, totals_by_student
from app.data.students import get_student, set_student_financial
from app.storage import save_upload
from app.templating import templates

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("")
async def payments_list(request: Request, user=Depends(require_role("admin", "agent", "accountant")), db=Depends(db_dep)):
    payments = await list_payments(db)
    return templates.TemplateResponse(
        "payments/list.html",
        {"request": request, "user": user, "payments": payments},
    )


@router.get("/student/{student_id}")
async def payments_by_student(request: Request, student_id: int, user=Depends(require_role("admin", "agent", "accountant")), db=Depends(db_dep)):
    student = await get_student(db, student_id)
    if not student:
        return RedirectResponse(url="/students", status_code=303)
    payments = await list_payments_by_student(db, student_id)
    totals = await totals_by_student(db, student_id)
    total_amount = int(student.get("total_amount") or 0)
    paid = int(totals.get("paid") or 0)
    balance = total_amount - paid
    return templates.TemplateResponse(
        "payments/student.html",
        {
            "request": request,
            "user": user,
            "student": student,
            "payments": payments,
            "paid": paid,
            "total_amount": total_amount,
            "balance": balance,
        },
    )


@router.get("/student/{student_id}/new")
async def payment_new_get(request: Request, student_id: int, user=Depends(require_role("admin", "agent", "accountant")), db=Depends(db_dep)):
    student = await get_student(db, student_id)
    if not student:
        return RedirectResponse(url="/students", status_code=303)
    return templates.TemplateResponse(
        "payments/form.html",
        {"request": request, "user": user, "student": student},
    )


@router.post("/student/{student_id}/new")
async def payment_new_post(
    request: Request,
    student_id: int,
    user=Depends(require_role("admin", "agent", "accountant")),
    payment_type: str = Form(...),
    amount: int = Form(...),
    currency: str = Form(...),
    payment_mode: str = Form(...),
    payment_date: str = Form(...),
    payment_status: str = Form(...),
    total_amount: int = Form(0),
    receipt: UploadFile | None = File(None),
    db=Depends(db_dep),
):
    student = await get_student(db, student_id)
    if not student:
        return RedirectResponse(url="/students", status_code=303)

    receipt_original = None
    receipt_path = None
    if receipt is not None and receipt.filename:
        allowed_exts = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"}
        ext = Path((receipt.filename or "").lower()).suffix
        if ext not in allowed_exts:
            raise HTTPException(status_code=400, detail="Type de fichier non autorisé")

        allowed_ct = {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "image/png",
            "image/jpeg",
        }
        if receipt.content_type and receipt.content_type not in allowed_ct:
            raise HTTPException(status_code=400, detail="Type de fichier non autorisé")

        receipt_original, stored, size = await save_upload(receipt)
        if size > 10 * 1024 * 1024:
            Path("uploads").joinpath(stored).unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        receipt_path = str(Path("uploads") / stored)

    created_by = user.get("id") if "id" in user else None
    await create_payment(
        db,
        student_id=student_id,
        payment_type=payment_type,
        amount=amount,
        currency=currency,
        payment_mode=payment_mode,
        payment_date=payment_date,
        payment_status=payment_status,
        receipt_original_filename=receipt_original,
        receipt_stored_path=receipt_path,
        created_by_user_id=created_by,
    )

    # update student's total amount/currency if provided
    try:
        total_amount_int = int(total_amount)
    except Exception:
        total_amount_int = 0
    if total_amount_int is not None and total_amount_int >= 0:
        await set_student_financial(db, student_id=student_id, total_amount=total_amount_int, currency=currency)

    return RedirectResponse(url=f"/payments/student/{student_id}", status_code=303)
