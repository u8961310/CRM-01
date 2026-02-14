import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.communication import CommunicationRecord
from app.models.user import User
from app.schemas.communication import CommunicationCreate, CommunicationOut

router = APIRouter(prefix="/api/communications", tags=["communications"])


@router.get("", response_model=list[CommunicationOut])
async def list_communications(
    parent_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(CommunicationRecord).options(selectinload(CommunicationRecord.user))
    if parent_id:
        stmt = stmt.where(CommunicationRecord.parent_id == parent_id)
    stmt = stmt.order_by(CommunicationRecord.created_at.desc())
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [
        CommunicationOut(
            id=r.id, parent_id=r.parent_id, user_id=r.user_id,
            contact_type=r.contact_type, summary=r.summary,
            created_at=r.created_at, user_name=r.user.full_name if r.user else None,
        )
        for r in records
    ]


@router.post("", response_model=CommunicationOut, status_code=status.HTTP_201_CREATED)
async def create_communication(
    body: CommunicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = CommunicationRecord(
        parent_id=body.parent_id,
        user_id=current_user.id,
        contact_type=body.contact_type,
        summary=body.summary,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return CommunicationOut(
        id=record.id, parent_id=record.parent_id, user_id=record.user_id,
        contact_type=record.contact_type, summary=record.summary,
        created_at=record.created_at, user_name=current_user.full_name,
    )


@router.get("/{record_id}", response_model=CommunicationOut)
async def get_communication(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(CommunicationRecord).options(
        selectinload(CommunicationRecord.user)
    ).where(CommunicationRecord.id == record_id)
    result = await db.execute(stmt)
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Record not found")
    return CommunicationOut(
        id=r.id, parent_id=r.parent_id, user_id=r.user_id,
        contact_type=r.contact_type, summary=r.summary,
        created_at=r.created_at, user_name=r.user.full_name if r.user else None,
    )
