from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.deps import db_dep, get_current_user
from app.data.dashboard import dashboard_stats
from app.templating import templates

router = APIRouter()


@router.get("/")
async def home(request: Request, user=Depends(get_current_user), db=Depends(db_dep)):
    stats = await dashboard_stats(db)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "stats": stats},
    )
