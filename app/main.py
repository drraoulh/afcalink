from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.routes import auth, students, payments, prospects, reports, admin, logs, pages
from app.core.config import settings
from app.data.users import ensure_bootstrap_admin
from app.data.sqlite import init_sqlite
from app.db import get_db


def create_app() -> FastAPI:
    app = FastAPI(title="AFCALINK TRAVEL - Interne")

    @app.on_event("startup")
    async def _startup():
        init_sqlite()
        db = get_db()
        await ensure_bootstrap_admin(db)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        https_only=settings.cookie_https_only,
        same_site="lax",
    )

    app.include_router(auth.router)
    app.include_router(pages.router)
    app.include_router(students.router)
    app.include_router(payments.router)
    app.include_router(prospects.router)
    app.include_router(reports.router)
    app.include_router(admin.router)
    app.include_router(logs.router)

    return app


app = create_app()
