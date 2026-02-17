from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from app.deps import db_dep, get_current_user
from app.data.users import count_users, create_user, get_user_by_email
from app.security import verify_password
from app.templating import templates

router = APIRouter()


@router.get("/login")
async def login_get(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/setup")
async def setup_get(request: Request, db=Depends(db_dep)):
    users_count = await count_users(db)
    if users_count > 0:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("auth/setup.html", {"request": request})


@router.post("/setup")
async def setup_post(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db=Depends(db_dep),
):
    users_count = await count_users(db)
    if users_count > 0:
        return RedirectResponse(url="/login", status_code=303)

    user_id = await create_user(db, full_name=full_name, email=email, password=password, role="admin")
    request.session["user_id"] = user_id
    return RedirectResponse(url="/", status_code=303)


@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db=Depends(db_dep),
):
    user = await get_user_by_email(db, email)
    if user and user.get("active") in (0, False):
        user = None
    if not user or not verify_password(password, user.get("password_hash", "")):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Email ou mot de passe incorrect"},
            status_code=400,
        )

    request.session["user_id"] = str(user.get("_id") or user.get("id"))
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@router.get("/me")
async def me(user=Depends(get_current_user)):
    user = dict(user)
    if "_id" in user:
        user["_id"] = str(user["_id"])
    if "id" in user:
        user["id"] = str(user["id"])
    user.pop("password_hash", None)
    return user
