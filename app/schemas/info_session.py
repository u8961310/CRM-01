import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.info_session import RegistrationStatus


# --- InfoSession ---

class InfoSessionCreate(BaseModel):
    title: str
    description: str | None = None
    session_date: date
    session_time: str
    location: str
    capacity: int | None = None


class InfoSessionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    session_date: date | None = None
    session_time: str | None = None
    location: str | None = None
    capacity: int | None = None


class InfoSessionOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    session_date: date
    session_time: str
    location: str
    capacity: int | None
    created_at: datetime
    updated_at: datetime
    registration_count: int = 0

    model_config = {"from_attributes": True}


# --- Registration ---

class RegistrationCreate(BaseModel):
    name: str
    email: str
    note: str | None = None


class RegistrationOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    name: str
    email: str
    status: RegistrationStatus
    email_sent: bool
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ImportResult(BaseModel):
    imported: int
    skipped: int


class SendEmailResult(BaseModel):
    sent: int
    message: str
