from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from cnaas_nac.schemas.generic import ErrorResponse

# ExceptionClasses


class BaseException(Exception):
    def __init__(self, error: str):
        self.error = error


class Unauthorized(BaseException):
    """Returns an Unauthorized 401"""

    pass


class NotFound(BaseException):
    """Returns an NotFound 404"""

    def __init__(self):
        self.error = "Not Found"


# ExceptionHandlers


def unauthorized_exception_handler(request: Request, exc: Unauthorized):
    error = ErrorResponse(message=exc.error)

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error.model_dump(),
    )


def notfound_exception_handler(request: Request, exc: NotFound):
    error = ErrorResponse(message=exc.error)

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error.model_dump(),
    )


async def validation_exception_handler(
    request, exc: RequestValidationError
) -> ErrorResponse:
    message = "Validation errors:"
    for error in exc.errors():
        message += f"\nField: {error['loc']}, Error: {error['msg']}"

    error = ErrorResponse(message=message)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error.model_dump(),
    )
