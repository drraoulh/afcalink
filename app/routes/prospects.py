from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from app.deps import db_dep, require_role
from app.data.prospects import list_prospects, create_prospect, update_prospect_status, delete_prospect, get_prospect
from app.templating import templates
from app.flash import flash_success

router = APIRouter(prefix="/prospects", tags=["prospects"])

@router.get("")
async def prospects_list(
    request: Request, 
    user=Depends(require_role("admin", "agent", "secretary", "admission_director", "operation_director")), 
    db=Depends(db_dep),
    search: str | None = None
):
    # Admins and Secretaries see everything (agent_name=None fetches all)
    # Agents see their own + NULL prospects
    agent_filter = user.get("full_name") if user.get("role") == "agent" else None
    prospects = await list_prospects(db, agent_name=agent_filter, search=search)
    return templates.TemplateResponse(
        "prospects/list.html", 
        {"request": request, "user": user, "prospects": prospects, "current_search": search or ""}
    )

from app.data.notifications import notify_role

@router.post("/new")
async def prospect_new(
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(None),
    country_interest: str = Form(None),
    source: str = Form(None),
    notes: str = Form(None),
    user=Depends(require_role("admin", "agent", "secretary", "admission_director", "operation_director")),
    db=Depends(db_dep)
):
    # If secretary or admin registers, agent_name is None (Global)
    # If agent registers, it's assigned to them
    agent_name = user.get("full_name") if user.get("role") == "agent" else None
    
    await create_prospect(
        db,
        full_name=full_name,
        phone=phone,
        email=email,
        country_interest=country_interest,
        source=source or ("Visite Bureau" if user.get("role") == "secretary" else None),
        agent_name=agent_name,
        notes=notes
    )
    
    # Notify Agents if it's a global prospect
    if not agent_name:
        await notify_role(
            db, 
            "agent", 
            "Nouveau Prospect Disponible", 
            f"Un nouveau prospect ({full_name}) a été enregistré par le secrétariat et est disponible pour traitement.",
            "info",
            "/prospects"
        )
    
    flash_success(request, "Prospect enregistré" + (" (Global)" if not agent_name else ""))
    return RedirectResponse(url="/prospects", status_code=303)

@router.post("/{prospect_id}/status")
async def prospect_status_update(
    prospect_id: int,
    status: str = Form(...),
    user=Depends(require_role("admin", "agent", "secretary", "admission_director", "operation_director")),
    db=Depends(db_dep)
):
    await update_prospect_status(db, prospect_id, status)
    return RedirectResponse(url="/prospects", status_code=303)

@router.post("/{prospect_id}/delete")
async def prospect_delete(
    prospect_id: int,
    user=Depends(require_role("admin")),
    db=Depends(db_dep)
):
    await delete_prospect(db, prospect_id)
    return RedirectResponse(url="/prospects", status_code=303)


@router.post("/{prospect_id}/convert")
async def prospect_convert(
    request: Request,
    prospect_id: int,
    user=Depends(require_role("admin", "agent", "secretary", "admission_director", "operation_director")),
    db=Depends(db_dep)
):
    from app.data.students import create_student
    from app.data.prospects import update_prospect_status
    
    p = await get_prospect(db, prospect_id)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")
        
    # Create student from prospect data
    await create_student(
        db,
        full_name=p["full_name"],
        phone=p["phone"],
        email=p.get("email") or "",
        country=p.get("country_interest") or "Inconnu",
        study_level="À préciser",
        program_choice="À préciser",
        university="À préciser",
        agent_name=p["agent_name"] or user.get("full_name"),
        status_id=2, # Dossier en préparation
        notes=p.get("notes"),
        changed_by_user_id=user.get("id")
    )
    
    # Update prospect status to converted
    await update_prospect_status(db, prospect_id, "converted")
    
    from app.flash import flash_success
    flash_success(request, f"Le prospect {p['full_name']} a été converti en étudiant avec succès.")
    
    return RedirectResponse(url="/students", status_code=303)
