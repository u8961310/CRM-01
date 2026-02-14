import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.communication import ContactType


class CommunicationCreate(BaseModel):
    parent_id: uuid.UUID
    contact_type: ContactType
    summary: str


class CommunicationOut(BaseModel):
    id: uuid.UUID
    parent_id: uuid.UUID
    user_id: uuid.UUID
    contact_type: ContactType
    summary: str
    created_at: datetime
    user_name: str | None = None

    model_config = {"from_attributes": True}


class FollowUpCreate(BaseModel):
    communication_id: uuid.UUID
    parent_id: uuid.UUID
    assigned_to: uuid.UUID
    description: str
    due_date: date | None = None


class FollowUpUpdate(BaseModel):
    is_done: bool | None = None
    description: str | None = None
    due_date: date | None = None
    assigned_to: uuid.UUID | None = None


class FollowUpOut(BaseModel):
    id: uuid.UUID
    communication_id: uuid.UUID
    parent_id: uuid.UUID
    assigned_to: uuid.UUID
    description: str
    due_date: date | None
    is_done: bool
    created_at: datetime
    assigned_user_name: str | None = None
    parent_name: str | None = None

    model_config = {"from_attributes": True}
