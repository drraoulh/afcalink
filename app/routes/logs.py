from fastapi import APIRouter, Depends, Request

from app.deps import require_role
from app.templating import templates

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
async def logs_list(request: Request, user=Depends(require_role("admin"))):
    return templates.TemplateResponse("logs/list.html", {"request": request, "user": user})
