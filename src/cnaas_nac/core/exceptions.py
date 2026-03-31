from typing import Any
from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from cnaas_nac.schemas.generic import ErrorResponse

# ExceptionClasses


class Unauthorized(Exception):
    """Returns an Unauthorized 401"""

    def __init__(self, error: str) -> None:
        super().__init__(error)
        self.error = error

    pass


class NotFound(Exception):
    """Returns an NotFound 404"""

    def __init__(self, error: str = "Not Found") -> None:
        super().__init__(error)
        self.error = error

    pass


# ExceptionHandlers


def format_react_admin_errors(exc: RequestValidationError) -> dict[str, Any]:
    errors: dict[str, Any] = {}

    for error in exc.errors():
        loc = error["loc"]

        if loc[0] == "body" and len(loc) > 3 and type(loc[2]) is int:
            # This is a nested field in a list, e.g. "body" -> "terms[0].nested_policy_id"
            field = f"{loc[1]}[{loc[2]}].{loc[-1]}"
        elif len(loc) > 1:
            field = loc[-1]
        else:
            field = "root"
        msg = error["msg"]

        if field == "root":
            errors.setdefault("root", {})["serverError"] = msg
        else:
            errors[field] = msg

    return errors


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"errors": format_react_admin_errors(exc)},
    )


async def unauthorized_exception_handler(
    request: Request, exc: Unauthorized
) -> Response:
    error = ErrorResponse(message=exc.error)

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error.model_dump(),
    )


async def notfound_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, NotFound)

    error = ErrorResponse(message=exc.error)

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error.model_dump(),
    )
