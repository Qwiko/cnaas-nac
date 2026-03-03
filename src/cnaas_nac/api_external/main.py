from fastapi import FastAPI

from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware

from cnaas_nac.api_external.routes_v2 import api_v2_router

from cnaas_nac.core.settings import settings
from cnaas_nac.core.exceptions import (
    validation_exception_handler,
    NotFound,
    notfound_exception_handler,
)
from cnaas_nac.schemas.generic import ValidationErrorResponse, ErrorResponse

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


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "up"}


app.include_router(api_v2_router)
