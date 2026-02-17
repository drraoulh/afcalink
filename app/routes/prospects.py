from fastapi import APIRouter, Depends, Request

from app.deps import require_role
from app.templating import templates

router = APIRouter(prefix="/prospects", tags=["prospects"])


@router.get("")
async def prospects_list(request: Request, user=Depends(require_role("admin", "agent"))):
    return templates.TemplateResponse("prospects/list.html", {"request": request, "user": user})
