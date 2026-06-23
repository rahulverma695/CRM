from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.routers import auth, invites


def create_app() -> FastAPI:
    app = FastAPI(title="CRM + HR Platform")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(invites.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
