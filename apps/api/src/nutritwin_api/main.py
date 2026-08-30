"""Application factory with safe defaults, request IDs, and central errors."""

import json
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from nutritwin_api.config import Settings, get_settings
from nutritwin_api.database import create_database_engine, create_session_factory
from nutritwin_api.models import Base
from nutritwin_api.routers import admin, auth, core, health, twin, users

logger = logging.getLogger("nutritwin")


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def create_app(
    settings: Settings | None = None,
    session_factory: sessionmaker[Session] | None = None,
) -> FastAPI:
    resolved = settings or get_settings()
    if session_factory is None:
        engine = create_database_engine(resolved.database_url)
        session_factory = create_session_factory(engine)
    else:
        engine = session_factory.kw["bind"]

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        configure_logging()
        if resolved.auto_create_schema:
            Base.metadata.create_all(engine)
        yield

    app = FastAPI(
        title="NutriTwin API",
        version="0.1.0",
        description=(
            "Non-diagnostic nutrition academic prototype. Estimated effective intake is not "
            "measured biological absorption."
        ),
        lifespan=lifespan,
    )
    app.state.settings = resolved
    app.state.session_factory = session_factory
    if resolved.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=resolved.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        )

    @app.middleware("http")
    async def request_context(request: Request, call_next: object) -> JSONResponse:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))[:64]
        request.state.request_id = request_id
        response = await call_next(request)  # type: ignore[operator]
        response.headers["X-Request-ID"] = request_id
        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                }
            )
        )
        return response  # type: ignore[no-any-return]

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, _: SQLAlchemyError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception(json.dumps({"event": "database_error", "request_id": request_id}))
        return JSONResponse(
            status_code=503,
            content={"error": "database temporarily unavailable", "request_id": request_id},
        )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(core.router)
    app.include_router(twin.router)
    app.include_router(admin.router)
    return app


app = create_app()
