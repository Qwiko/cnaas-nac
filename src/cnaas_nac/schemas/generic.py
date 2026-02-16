from typing import Literal

from pydantic import (
    BaseModel,
)


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    message: str



