from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from app.routes import auth, students, payments, prospects, reports, admin, logs, pages
from app.core.config import settings
from app.data.users import ensure_bootstrap_admin
from app.data.sqlite import init_sqlite
from app.db import close_client, get_db, ping_mongo


def create_app() -> FastAPI:
    app = FastAPI(title="AFCALINK TRAVEL - Interne")

    @app.exception_handler(HTTPException)
    async def auth_exception_handler(request: Request, exc: HTTPException):
        if exc.status_code == 401:
            return RedirectResponse(url="/login", status_code=303)
        raise exc

    @app.on_event("startup")
    async def _startup():
        init_sqlite()
        db = get_db()
        # Skip ping for Atlas M0 free tier (ReplicaSetNoPrimary on startup)
        # if settings.db_backend != "sqlite":
        #     await ping_mongo()
        # Skip bootstrap admin on startup for Atlas; will be created lazily on first login if needed
        # await ensure_bootstrap_admin(db)

    @app.on_event("shutdown")
    async def _shutdown():
        if settings.db_backend != "sqlite":
            close_client()

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        https_only=settings.cookie_https_only,
        same_site="lax",
    )

    from app.routes import auth, pages, students, payments, prospects, logs, reports, admin, tasks, partners, activity, accounting, notifications

    from fastapi.staticfiles import StaticFiles
    import os
    
    current_dir = os.path.dirname(os.path.realpath(__file__))
    static_dir = os.path.join(current_dir, "static")
    
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    app.include_router(auth.router)
    app.include_router(pages.router)
    app.include_router(students.router)
    app.include_router(payments.router)
    app.include_router(prospects.router)
    app.include_router(reports.router)
    app.include_router(admin.router)
    app.include_router(logs.router)
    app.include_router(tasks.router)
    app.include_router(partners.router)
    app.include_router(activity.router)
    app.include_router(accounting.router)
    app.include_router(notifications.router)

    return app


app = create_app()
