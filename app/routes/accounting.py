from fastapi import APIRouter, Depends, Request, HTTPException
from app.deps import db_dep, require_role
from app.data.payments import list_pending_payments, count_pending_payments
from app.data.users import list_users
from app.templating import templates

router = APIRouter(prefix="/accounting", tags=["accounting"])

@router.get("/pending")
async def pending_payments_view(
    request: Request,
    agent_id: int | None = None,
    filter_date: str | None = None,
    user=Depends(require_role("admin", "secretary")),
    db=Depends(db_dep)
):
    users_list = await list_users(db)
    pending = await list_pending_payments(db, agent_id=agent_id, filter_date=filter_date)
    pending_count = await count_pending_payments(db)
    
    return templates.TemplateResponse(
        "accounting/pending.html",
        {
            "request": request,
            "user": user,
            "payments": pending,
            "users_list": users_list,
            "pending_count": pending_count,
            "current_agent_id": agent_id,
            "current_filter_date": filter_date
        }
    )
