from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware

from cnaas_nac.api_external.routes_v2 import api_v2_router
from cnaas_nac.core.exceptions import (
    NotFound,
    notfound_exception_handler,
    validation_exception_handler,
)
from cnaas_nac.core.settings import settings
from cnaas_nac.schemas.generic import ErrorResponse

app = FastAPI(
    title="CNaaS NAC",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    exception_handlers={
        NotFound: notfound_exception_handler,
        RequestValidationError: validation_exception_handler,
    },
    responses={
        404: {
            "description": "Not Found",
            "model": ErrorResponse,
        },
        422: {
            "description": "Unprocessable Entity",
            "model": ErrorResponse,
        },
    },
)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

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


app.include_router(api_v2_router)
