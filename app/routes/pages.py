from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.deps import db_dep, get_current_user
from app.data.dashboard import dashboard_stats
from app.templating import templates

router = APIRouter()


from app.data.payments import count_pending_payments

@router.get("/")
async def home(request: Request, user=Depends(get_current_user), db=Depends(db_dep)):
    stats = await dashboard_stats(db, user)
    pending_count = await count_pending_payments(db)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "stats": stats, "pending_count": pending_count},
    )
