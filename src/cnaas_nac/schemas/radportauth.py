from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_validator
from pydantic_extra_types.mac_address import MacAddress

from cnaas_nac.schemas.generic import Username


class RadPostAuthLog(BaseModel):
    id: int
    endpoint_id: Optional[int] = None

    username: Username
    calling_station_id: MacAddress
    nas_identifier: Optional[str] = None
    nas_port_id: Optional[str] = None
    auth_date: datetime
    reply: str
    matched_policy_id: Optional[int] = None
    error_message: Optional[str] = None


class RadPostAuthLogFull(RadPostAuthLog):
    request_json: Optional[dict[str, Any]] = {}
    reply_json: Optional[dict[str, Any]] = {}

    @field_validator("request_json", mode="before")
    def clean_json(cls, val: dict[str, Any]) -> dict[str, Any]:
        if not val:
            return {}

        # Hack to replace \\\/ in NAS-Port-Id so it looks nicer
        return {
            k: v.replace("=5C=5C=5C/", "/") if isinstance(v, str) else v
            for k, v in val.items()
        }
