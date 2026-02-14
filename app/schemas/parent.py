import uuid
from datetime import datetime

from pydantic import BaseModel


class ParentCreate(BaseModel):
    name: str
    phone: str
    email: str | None = None
    address: str | None = None
    note: str | None = None


class ParentUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    note: str | None = None


class ParentOut(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    email: str | None
    address: str | None
    note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ParentStudentLink(BaseModel):
    student_id: uuid.UUID
    relationship_type: str


class ParentStudentOut(BaseModel):
    student_id: uuid.UUID
    student_name: str
    grade: str
    relationship_type: str
