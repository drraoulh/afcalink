from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path

from app.deps import db_dep, require_role
from app.data.payments import create_payment, get_payment, list_payments, list_payments_by_student, totals_by_student, confirm_payment
from app.data.notifications import notify_admins, notify_role, create_notification
from app.data.students import get_student, set_student_financial
from app.flash import flash_success
from app.storage import save_upload
from app.templating import templates

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("")
async def payments_list(request: Request, user=Depends(require_role("admin", "agent", "secretary")), db=Depends(db_dep)):
    agent_name = user.get("full_name") if user.get("role") == "agent" else None
    payments = await list_payments(db, agent_name=agent_name)
    return templates.TemplateResponse(
        "payments/list.html",
        {"request": request, "user": user, "payments": payments},
    )


@router.get("/student/{student_id}")
async def payments_by_student(request: Request, student_id: int, user=Depends(require_role("admin", "agent", "secretary")), db=Depends(db_dep)):
    student = await get_student(db, student_id)
    if not student:
        return RedirectResponse(url="/students", status_code=303)
    if user.get("role") == "agent" and student.get("agent_name") != user.get("full_name"):
        raise HTTPException(status_code=403, detail="Forbidden")
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
async def payment_new_get(request: Request, student_id: int, user=Depends(require_role("admin", "agent", "secretary")), db=Depends(db_dep)):
    student = await get_student(db, student_id)
    if not student:
        return RedirectResponse(url="/students", status_code=303)
    if user.get("role") == "agent" and student.get("agent_name") != user.get("full_name"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return templates.TemplateResponse(
        "payments/form.html",
        {"request": request, "user": user, "student": student},
    )


@router.get("/receipts/{payment_id}")
async def payment_receipt_download(payment_id: int, user=Depends(require_role("admin", "agent", "secretary")), db=Depends(db_dep)):
    payment = await get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if user.get("role") == "agent":
        student = await get_student(db, int(payment.get("student_id") or 0))
        if not student:
            raise HTTPException(status_code=404, detail="Not found")
        if student.get("agent_name") != user.get("full_name"):
            raise HTTPException(status_code=403, detail="Forbidden")

    stored_path = payment.get("receipt_stored_path")
    original_filename = payment.get("receipt_original_filename") or "receipt"
    if not stored_path:
        raise HTTPException(status_code=404, detail="Receipt not found")

    path = Path(stored_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing")
    return FileResponse(path, filename=original_filename, media_type="application/octet-stream")


@router.post("/student/{student_id}/new")
async def payment_new_post(
    request: Request,
    student_id: int,
    user=Depends(require_role("admin", "agent", "secretary")),
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
    if user.get("role") == "agent" and student.get("agent_name") != user.get("full_name"):
        raise HTTPException(status_code=403, detail="Forbidden")

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

    # Notifications
    await notify_role(db, "secretary", "Nouveau Paiement à Valider", 
                     f"Un versement de {amount} {currency} a été enregistré pour {student['full_name']}.", 
                     "payment", f"/accounting/pending")
    await notify_admins(db, "Encaissement Enregistré", 
                      f"{user['full_name']} a enregistré {amount} {currency} pour {student['full_name']}.", 
                      "payment", f"/payments/student/{student_id}")

    flash_success(request, "Paiement enregistré avec succès")
    return RedirectResponse(url=f"/payments/student/{student_id}", status_code=303)


@router.post("/confirm/{payment_id}")
async def payment_confirm(request: Request, payment_id: int, user=Depends(require_role("admin", "secretary")), db=Depends(db_dep)):
    payment = await get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    await confirm_payment(db, payment_id)
    
    # Notify creator of the payment
    if payment.get("created_by_user_id"):
        await create_notification(
            db, 
            user_id=payment["created_by_user_id"],
            title="Paiement Confirmé",
            message=f"Le versement de {payment['amount']} {payment['currency']} pour {payment.get('student_name', 'étudiant')} a été validé par la comptabilité.",
            type="success",
            link=f"/payments/student/{payment['student_id']}"
        )

    flash_success(request, "Paiement confirmé par le comptable")
    return RedirectResponse(url=f"/payments/student/{payment['student_id']}", status_code=303)
