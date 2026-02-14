import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.communication import FollowUp
from app.models.user import Role, User
from app.schemas.communication import FollowUpCreate, FollowUpOut, FollowUpUpdate

router = APIRouter(prefix="/api/follow-ups", tags=["follow-ups"])


@router.get("", response_model=list[FollowUpOut])
async def list_follow_ups(
    mine: bool = Query(False),
    pending: bool = Query(False),
    parent_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(FollowUp).options(
        selectinload(FollowUp.assigned_user),
        selectinload(FollowUp.parent),
    )
    if mine or current_user.role != Role.admin:
        stmt = stmt.where(FollowUp.assigned_to == current_user.id)
    if pending:
        stmt = stmt.where(FollowUp.is_done == False)  # noqa: E712
    if parent_id:
        stmt = stmt.where(FollowUp.parent_id == parent_id)
    stmt = stmt.order_by(FollowUp.due_date.asc().nullslast(), FollowUp.created_at.desc())
    result = await db.execute(stmt)
    follow_ups = result.scalars().all()
    return [
        FollowUpOut(
            id=f.id, communication_id=f.communication_id, parent_id=f.parent_id,
            assigned_to=f.assigned_to, description=f.description,
            due_date=f.due_date, is_done=f.is_done, created_at=f.created_at,
            assigned_user_name=f.assigned_user.full_name if f.assigned_user else None,
            parent_name=f.parent.name if f.parent else None,
        )
        for f in follow_ups
    ]


@router.post("", response_model=FollowUpOut, status_code=status.HTTP_201_CREATED)
async def create_follow_up(
    body: FollowUpCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    follow_up = FollowUp(**body.model_dump())
    db.add(follow_up)
    await db.commit()
    await db.refresh(follow_up, ["assigned_user", "parent"])
    return FollowUpOut(
        id=follow_up.id, communication_id=follow_up.communication_id,
        parent_id=follow_up.parent_id, assigned_to=follow_up.assigned_to,
        description=follow_up.description, due_date=follow_up.due_date,
        is_done=follow_up.is_done, created_at=follow_up.created_at,
        assigned_user_name=follow_up.assigned_user.full_name if follow_up.assigned_user else None,
        parent_name=follow_up.parent.name if follow_up.parent else None,
    )


@router.patch("/{follow_up_id}", response_model=FollowUpOut)
async def update_follow_up(
    follow_up_id: uuid.UUID,
    body: FollowUpUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(FollowUp).options(
        selectinload(FollowUp.assigned_user),
        selectinload(FollowUp.parent),
    ).where(FollowUp.id == follow_up_id)
    result = await db.execute(stmt)
    follow_up = result.scalar_one_or_none()
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    if current_user.role != Role.admin and follow_up.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Can only update your own follow-ups")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(follow_up, field, value)
    await db.commit()
    await db.refresh(follow_up, ["assigned_user", "parent"])
    return FollowUpOut(
        id=follow_up.id, communication_id=follow_up.communication_id,
        parent_id=follow_up.parent_id, assigned_to=follow_up.assigned_to,
        description=follow_up.description, due_date=follow_up.due_date,
        is_done=follow_up.is_done, created_at=follow_up.created_at,
        assigned_user_name=follow_up.assigned_user.full_name if follow_up.assigned_user else None,
        parent_name=follow_up.parent.name if follow_up.parent else None,
    )
