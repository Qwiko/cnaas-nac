from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from cnaas_nac.api_internal.schemas import AccessReject, AttributeDetail, InternalAuth
from cnaas_nac.models.policy import ClientType


class Unauthorized(Exception):
    """Returns an Unauthorized 401"""

    def __init__(self, error: str, policy_id: int | None = None):
        self.error = error
        self.policy_id = policy_id

    pass


async def unauthorized_exception_handler(
    request: Request, exc: Unauthorized
) -> JSONResponse:
    error = AccessReject(
        policy_id=AttributeDetail(value=exc.policy_id) if exc.policy_id else None,
        error_message=AttributeDetail(value=exc.error),
    )

    auth = InternalAuth.model_construct(**(await request.json()))

    # Fix to make eap-tls post-auth to actually process the json body
    # to extract log information and save to postauth
    mab_user_type = auth.client_type == ClientType.MAB

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED
        if mab_user_type
        else status.HTTP_200_OK,
        content=error.model_dump(by_alias=True),
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)

    message = "Validation errors:"
    for error in exc.errors():
        message += f"\nField: {error['loc']}, Error: {error['msg']}"

    error = AccessReject(error_message=AttributeDetail(value=message))

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error.model_dump(by_alias=True),
    )
