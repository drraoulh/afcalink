from fastapi import APIRouter, Depends, Request
from app.deps import db_dep, require_role
from app.data.logs import list_global_history
from app.templating import templates

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("")
async def logs_list(request: Request, user=Depends(require_role("admin", "agent")), db=Depends(db_dep)):
    history = await list_global_history(db)
    return templates.TemplateResponse(
        "logs/list.html", 
        {"request": request, "user": user, "history": history}
    )
