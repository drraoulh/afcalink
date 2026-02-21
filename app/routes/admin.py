from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.deps import db_dep, require_role
from app.templating import templates
from app.data.users import list_users, create_user, get_user_by_email
from app.flash import flash_success, flash_error

router = APIRouter(prefix="/admin", tags=["admin"])

from app.data.payments import list_pending_payments, count_pending_payments

@router.get("")
async def admin_home(request: Request, user=Depends(require_role("admin")), db=Depends(db_dep)):
    pending_count = await count_pending_payments(db)
    return templates.TemplateResponse("admin/index.html", {"request": request, "user": user, "pending_count": pending_count})

@router.get("/users")
async def admin_users_list(request: Request, user=Depends(require_role("admin")), db=Depends(db_dep)):
    users = await list_users(db)
    pending_count = await count_pending_payments(db)
    return templates.TemplateResponse("admin/users.html", {"request": request, "user": user, "users": users, "pending_count": pending_count})

@router.post("/users/new")
async def admin_user_create(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    user=Depends(require_role("admin")),
    db=Depends(db_dep)
):
    existing = await get_user_by_email(db, email)
    if existing:
        flash_error(request, "Cet email est déjà utilisé")
        return RedirectResponse(url="/admin/users", status_code=303)
    
    await create_user(db, full_name=full_name, email=email, password=password, role=role)
    flash_success(request, f"Utilisateur {full_name} créé avec succès")
    return RedirectResponse(url="/admin/users", status_code=303)
