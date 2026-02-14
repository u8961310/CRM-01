import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.communication import CommunicationRecord, FollowUp
from app.models.parent import Parent
from app.models.student import ParentStudent, Student


async def get_parent_full_detail(db: AsyncSession, parent_id: uuid.UUID) -> dict:
    """Fetch a parent's full profile: info + students + communications + follow-ups."""
    result = await db.execute(select(Parent).where(Parent.id == parent_id))
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    # Students linked to this parent
    stmt_students = (
        select(ParentStudent, Student)
        .join(Student, ParentStudent.student_id == Student.id)
        .where(ParentStudent.parent_id == parent_id)
    )
    student_rows = (await db.execute(stmt_students)).all()
    students = [
        {
            "student_id": str(s.id),
            "student_name": s.name,
            "grade": s.grade,
            "relationship_type": ps.relationship_type,
        }
        for ps, s in student_rows
    ]

    # Communication records
    stmt_comms = (
        select(CommunicationRecord)
        .options(selectinload(CommunicationRecord.user))
        .where(CommunicationRecord.parent_id == parent_id)
        .order_by(CommunicationRecord.created_at.desc())
    )
    comms = (await db.execute(stmt_comms)).scalars().all()
    communications = [
        {
            "id": str(c.id),
            "contact_type": c.contact_type.value,
            "summary": c.summary,
            "created_at": c.created_at.isoformat(),
            "user_name": c.user.full_name if c.user else None,
        }
        for c in comms
    ]

    # Follow-ups
    stmt_follow = (
        select(FollowUp)
        .options(selectinload(FollowUp.assigned_user))
        .where(FollowUp.parent_id == parent_id)
        .order_by(FollowUp.is_done.asc(), FollowUp.due_date.asc().nullslast())
    )
    follow_ups_rows = (await db.execute(stmt_follow)).scalars().all()
    follow_ups = [
        {
            "id": str(f.id),
            "description": f.description,
            "due_date": f.due_date.isoformat() if f.due_date else None,
            "is_done": f.is_done,
            "assigned_user_name": f.assigned_user.full_name if f.assigned_user else None,
            "created_at": f.created_at.isoformat(),
        }
        for f in follow_ups_rows
    ]

    return {
        "id": str(parent.id),
        "name": parent.name,
        "phone": parent.phone,
        "email": parent.email,
        "address": parent.address,
        "note": parent.note,
        "created_at": parent.created_at.isoformat(),
        "updated_at": parent.updated_at.isoformat(),
        "students": students,
        "communications": communications,
        "follow_ups": follow_ups,
    }
