from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from cnaas_nac.api_internal.auth import router as auth_router

# from cnaas_nac.core.settings import settings
from cnaas_nac.api_internal.exceptions import (
    Unauthorized,
    unauthorized_exception_handler,
    validation_exception_handler,
)
from cnaas_nac.api_internal.schemas import AccessReject


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app_: FastAPI):
    run_migrations()
    yield


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


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "up"}


app.include_router(auth_router)
