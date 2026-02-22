from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.deps import db_dep, get_current_user
from app.data.dashboard import dashboard_stats
from app.templating import templates
from app.core.config import settings
from app.db import ping_mongo

router = APIRouter()


from app.data.payments import count_pending_payments


@router.get("/health/db")
async def health_db():
    if settings.db_backend == "sqlite":
        return {"ok": True, "backend": "sqlite"}

    try:
        await ping_mongo()
        return {"ok": True, "backend": "mongo"}
    except Exception as e:
        return {"ok": False, "backend": "mongo", "error": str(e)}

@router.get("/")
async def home(request: Request, user=Depends(get_current_user), db=Depends(db_dep)):
    stats = await dashboard_stats(db, user)
    pending_count = await count_pending_payments(db)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "stats": stats, "pending_count": pending_count},
    )
