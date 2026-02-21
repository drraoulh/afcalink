from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from datetime import date
from app.deps import db_dep, get_current_user
from app.data.activity import create_daily_report, list_user_reports
from app.templating import templates

router = APIRouter(prefix="/activity", tags=["activity"])

from app.data.prospects import get_daily_prospect_count
from app.data.payments import get_daily_payment_count

from app.data.activity import create_daily_report, list_user_reports, list_all_reports
from app.data.users import list_users

@router.get("/daily")
async def daily_report_page(
    request: Request, 
    agent_id: str | None = None,
    filter_date: str | None = None,
    user=Depends(get_current_user), 
    db=Depends(db_dep)
):
    is_admin = user.get("role") in ["admin", "admission_director", "operation_director", "secretary"]
    users_list = []
    
    # Safely parse agent_id
    try:
        parsed_agent_id = int(agent_id) if agent_id and agent_id.strip() else None
    except (ValueError, TypeError):
        parsed_agent_id = None

    if is_admin:
        users_list = await list_users(db)
        reports = await list_all_reports(db, user_id=parsed_agent_id, report_date=filter_date)
        today_prospects = 0 
        today_payments = 0   
    else:
        reports = await list_user_reports(db, user["id"])
        agent_name = user.get("full_name", "")
        today_prospects = await get_daily_prospect_count(db, agent_name)
        today_payments = await get_daily_payment_count(db, agent_name)
    
    return templates.TemplateResponse(
        "activity/daily.html",
        {
            "request": request,
            "user": user,
            "reports": reports,
            "is_admin": is_admin,
            "users_list": users_list,
            "current_agent_id": parsed_agent_id,
            "current_filter_date": filter_date,
            "today": date.today().isoformat(),
            "auto_prospects": today_prospects,
            "auto_payments": today_payments
        }
    )

from app.data.notifications import notify_admins

@router.post("/daily")
async def daily_report_post(
    request: Request,
    content: str = Form(...),
    tasks_completed: str = Form(None),
    prospects_met: int = Form(0),
    payments_collected: int = Form(0),
    report_date: str = Form(...),
    user=Depends(get_current_user),
    db=Depends(db_dep),
):
    await create_daily_report(
        db,
        user_id=user["id"],
        report_date=report_date,
        content=content,
        tasks_completed=tasks_completed,
        prospects_met=prospects_met,
        payments_collected=payments_collected,
    )
    
    # Notify Admins
    await notify_admins(
        db,
        title="Nouveau Rapport Journalier",
        message=f"L'agent {user['full_name']} a soumis son rapport pour le {report_date}.",
        type="report",
        link=f"/activity/daily?agent_id={user['id']}&filter_date={report_date}"
    )
    
    flash_success(request, "Rapport soumis avec succès")
    return RedirectResponse(url="/activity/daily", status_code=303)
