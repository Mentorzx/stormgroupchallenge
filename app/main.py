from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes import breaches, health, sync
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Breach Radar",
        version="0.1.0",
        description=(
            "API backend para sincronizar e consultar o catálogo público de breaches da HIBP."
        ),
    )
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(sync.router)
    app.include_router(breaches.router)
    return app


app = create_app()
