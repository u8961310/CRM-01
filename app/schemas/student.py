import uuid
from datetime import datetime

from pydantic import BaseModel


class StudentCreate(BaseModel):
    name: str
    grade: str
    note: str | None = None


class StudentUpdate(BaseModel):
    name: str | None = None
    grade: str | None = None
    note: str | None = None


class StudentOut(BaseModel):
    id: uuid.UUID
    name: str
    grade: str
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentParentLink(BaseModel):
    parent_id: uuid.UUID
    relationship_type: str
