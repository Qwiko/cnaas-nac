from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import InterfaceError
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from cnaas_nac.api_external.routes_v2 import api_v2_router
from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import (
    NotFound,
    notfound_exception_handler,
    validation_exception_handler,
)
from cnaas_nac.core.settings import settings
from cnaas_nac.schemas.generic import ErrorResponse, ValidationErrorResponse

app = FastAPI(
    title="CNaaS NAC",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    exception_handlers={
        RequestValidationError: validation_exception_handler,
        NotFound: notfound_exception_handler,
    },
    responses={
        422: {
            "description": "Validation Error",
            "model": ValidationErrorResponse,
        },
        404: {
            "description": "Not Found",
            "model": ErrorResponse,
        },
    },
)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


# Set all CORS enabled origins
# if settings.all_cors_origins:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)


@app.get("/api/v2/health")
async def health_check(db: Annotated[AsyncSession, Depends(get_async_session)]):
    try:
        await db.execute(text("SELECT 1"))

        return {"db": "up"}
    except (ConnectionRefusedError, InterfaceError) as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


app.include_router(api_v2_router)
