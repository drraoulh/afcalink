from fastapi import Depends, HTTPException, Request
from app.db import get_db
from app.data.users import get_user_by_id


def db_dep():
    return get_db()


async def get_current_user(request: Request, db=Depends(db_dep)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await get_user_by_id(db, user_id)
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Not authenticated")

    if user.get("active") in (0, False):
        request.session.clear()
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_role(*roles: str):
    async def _dep(user=Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return _dep
