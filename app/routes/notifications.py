from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from app.deps import db_dep, get_current_user
from app.data.notifications import list_notifications, mark_as_read, mark_all_as_read
from app.templating import templates

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("")
async def notifications_page(request: Request, user=Depends(get_current_user), db=Depends(db_dep)):
    notifications = await list_notifications(db, user["id"], limit=50)
    return templates.TemplateResponse(
        "notifications.html",
        {"request": request, "user": user, "notifications": notifications}
    )

@router.post("/read/{notification_id}")
async def notification_read(notification_id: int, user=Depends(get_current_user), db=Depends(db_dep)):
    await mark_as_read(db, notification_id)
    return RedirectResponse(url="/notifications", status_code=303)

@router.post("/read-all")
async def notifications_read_all(request: Request, user=Depends(get_current_user), db=Depends(db_dep)):
    await mark_all_as_read(db, user["id"])
    return RedirectResponse(url="/notifications", status_code=303)
