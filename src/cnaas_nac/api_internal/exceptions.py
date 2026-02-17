from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from cnaas_nac.schemas.internal_auth import AccessReject


class BaseException(Exception):
    def __init__(self, error: str):
        self.error = error


class Unauthorized(BaseException):
    """Returns an Unauthorized 401"""
    pass



def unauthorized_exception_handler(request: Request, exc: Unauthorized):
    error = AccessReject(reply_message={"value": exc.error})

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error.model_dump(by_alias=True),
    )


async def validation_exception_handler(
    request, exc: RequestValidationError
) -> AccessReject:
    message = "Validation errors:"
    for error in exc.errors():
        message += f"\nField: {error['loc']}, Error: {error['msg']}"

    error = AccessReject(reply_message={"value": message})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error.model_dump(by_alias=True),
    )
