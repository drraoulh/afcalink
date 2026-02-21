from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from app.deps import db_dep, require_role
from app.data.partners import list_partners, create_partner, delete_partner
from app.templating import templates
from app.flash import flash_success

router = APIRouter(prefix="/partners", tags=["partners"])

@router.get("")
async def partners_list(request: Request, search: str | None = None, user=Depends(require_role("admin", "agent")), db=Depends(db_dep)):
    partners = await list_partners(db, search=search)
    return templates.TemplateResponse("partners/list.html", {"request": request, "user": user, "partners": partners, "current_search": search or ""})

@router.post("/new")
async def partner_new(
    request: Request,
    name: str = Form(...),
    country: str = Form(...),
    contact_person: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
    website: str = Form(None),
    notes: str = Form(None),
    user=Depends(require_role("admin")),
    db=Depends(db_dep)
):
    await create_partner(db, name, country, contact_person, email, phone, website, notes)
    flash_success(request, "Partenaire ajouté avec succès")
    return RedirectResponse(url="/partners", status_code=303)

@router.post("/{partner_id}/delete")
async def partner_delete(partner_id: int, user=Depends(require_role("admin")), db=Depends(db_dep)):
    await delete_partner(db, partner_id)
    return RedirectResponse(url="/partners", status_code=303)
