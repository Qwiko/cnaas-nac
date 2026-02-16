from pydantic import BaseModel


class GroupBase(BaseModel):
    name: str
    fieldname: str
    condition: str

class GroupResponse(GroupBase):
    id: int
