from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from app.deps import db_dep, require_role, get_current_user
from app.data.tasks import list_tasks, create_task, update_task_status, delete_task
from app.data.students import list_students
from app.data.users import list_users
from app.templating import templates
from app.flash import flash_success

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("")
async def tasks_list(request: Request, user=Depends(require_role("admin", "agent", "operation_director")), db=Depends(db_dep)):
    user_id = user.get("id") if user.get("role") == "agent" else None
    tasks = await list_tasks(db, user_id=user_id)
    students = await list_students(db)
    users = await list_users(db)
    
    return templates.TemplateResponse(
        "tasks/list.html", 
        {"request": request, "user": user, "tasks": tasks, "students": students, "users": users}
    )

@router.post("/new")
async def task_new(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    due_date: str = Form(None),
    priority: str = Form("medium"),
    assigned_to_user_id: int = Form(None),
    student_id: int = Form(None),
    user=Depends(require_role("admin", "agent", "operation_director")),
    db=Depends(db_dep)
):
    await create_task(
        db,
        title=title,
        description=description,
        due_date=due_date,
        priority=priority,
        assigned_to_user_id=assigned_to_user_id,
        student_id=student_id
    )
    flash_success(request, "Tâche créée avec succès")
    return RedirectResponse(url="/tasks", status_code=303)

@router.post("/{task_id}/status")
async def task_status_update(
    task_id: int,
    status: str = Form(...),
    user=Depends(require_role("admin", "agent", "operation_director")),
    db=Depends(db_dep)
):
    await update_task_status(db, task_id, status)
    return RedirectResponse(url="/tasks", status_code=303)

@router.post("/{task_id}/delete")
async def task_delete(
    task_id: int,
    user=Depends(require_role("admin", "agent", "operation_director")),
    db=Depends(db_dep)
):
    await delete_task(db, task_id)
    return RedirectResponse(url="/tasks", status_code=303)
