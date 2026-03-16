from contextlib import asynccontextmanager
from typing import Annotated

from alembic.config import Config
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.exc import InterfaceError
from sqlalchemy.ext.asyncio import AsyncSession
from cnaas_nac.core.settings import settings
from alembic import command
from cnaas_nac.api_internal.auth import router as auth_router

# from cnaas_nac.core.settings import settings
from cnaas_nac.api_internal.exceptions import (
    Unauthorized,
    unauthorized_exception_handler,
    validation_exception_handler,
)
from cnaas_nac.core.scheduled_tasks import setup_scheduled_tasks
from cnaas_nac.api_internal.schemas import AccessReject
from cnaas_nac.core.db import get_async_session


def run_alembic_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app_: FastAPI):
    run_alembic_migrations()

    if not settings.PRUNING_DISABLED:
        scheduler = setup_scheduled_tasks()
        scheduler.start()
        yield
        scheduler.shutdown()


app = FastAPI(
    title="CNaaS NAC Internal",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    lifespan=lifespan,
    exception_handlers={
        Unauthorized: unauthorized_exception_handler,
        RequestValidationError: validation_exception_handler,
    },
    responses={
        401: {
            "description": "Unauthorized",
            "model": AccessReject,
        },
        422: {
            "description": "Unprocessable Entity",
            "model": AccessReject,
        },
    },
)

# Set all CORS enabled origins
# if settings.all_cors_origins:
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=["*"],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )


@app.get("/api/v2/health")
async def health_check(db: Annotated[AsyncSession, Depends(get_async_session)]):
    try:
        await db.execute(text("SELECT 1"))

        return {"db": "up"}
    except (ConnectionRefusedError, InterfaceError) as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


app.include_router(auth_router)
