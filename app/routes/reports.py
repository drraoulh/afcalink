from fastapi import APIRouter, Depends, Request

from app.deps import require_role
from app.templating import templates

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
async def reports_list(request: Request, user=Depends(require_role("admin", "agent"))):
    return templates.TemplateResponse("reports/list.html", {"request": request, "user": user})
