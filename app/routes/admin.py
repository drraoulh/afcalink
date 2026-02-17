from fastapi import APIRouter, Depends, Request

from app.deps import require_role
from app.templating import templates

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("")
async def admin_home(request: Request, user=Depends(require_role("admin"))):
    return templates.TemplateResponse("admin/index.html", {"request": request, "user": user})
