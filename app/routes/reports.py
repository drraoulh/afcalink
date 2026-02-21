from fastapi import APIRouter, Depends, Request
from app.deps import db_dep, require_role
from app.data.reports import daily_report_data
from app.templating import templates
from datetime import datetime

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("")
async def reports_list(request: Request, date: str | None = None, user=Depends(require_role("admin", "agent", "admission_director", "operation_director")), db=Depends(db_dep)):
    if not date:
        date = datetime.utcnow().strftime("%Y-%m-%d")
    
    report = await daily_report_data(db, date)
    return templates.TemplateResponse(
        "reports/list.html", 
        {"request": request, "user": user, "report": report, "current_date": date}
    )
