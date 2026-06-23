from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings
from app.core.routers import auth, invites, oauth


def create_app() -> FastAPI:
    app = FastAPI(title="CRM + HR Platform")
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret or settings.jwt_secret)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(invites.router)
    app.include_router(oauth.router)

    from app.crm.routers import stages, leads, deals, activities, crm_tasks, custom_views
    from app.crm.routers import ws as crm_ws
    app.include_router(stages.router)
    app.include_router(leads.router)
    app.include_router(deals.router)
    app.include_router(activities.router)
    app.include_router(crm_tasks.router)
    app.include_router(custom_views.router)
    app.include_router(crm_ws.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
