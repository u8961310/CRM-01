import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, role_required
from app.models.parent import Parent
from app.models.student import ParentStudent, Student
from app.models.user import Role, User
from app.schemas.parent import ParentCreate, ParentOut, ParentStudentLink, ParentStudentOut, ParentUpdate
from app.services.parent_detail import get_parent_full_detail

router = APIRouter(prefix="/api/parents", tags=["parents"])


@router.get("", response_model=list[ParentOut])
async def list_parents(
    q: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Parent).order_by(Parent.created_at.desc())
    if q:
        stmt = stmt.where(Parent.name.ilike(f"%{q}%") | Parent.phone.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    return [ParentOut.model_validate(p) for p in result.scalars().all()]


@router.post("", response_model=ParentOut, status_code=status.HTTP_201_CREATED)
async def create_parent(
    body: ParentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parent = Parent(**body.model_dump())
    db.add(parent)
    await db.commit()
    await db.refresh(parent)
    return ParentOut.model_validate(parent)


@router.get("/{parent_id}")
async def get_parent(
    parent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_parent_full_detail(db, parent_id)


@router.put("/{parent_id}", response_model=ParentOut)
async def update_parent(
    parent_id: uuid.UUID,
    body: ParentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Parent).where(Parent.id == parent_id))
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(parent, field, value)
    await db.commit()
    await db.refresh(parent)
    return ParentOut.model_validate(parent)


@router.delete("/{parent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parent(
    parent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(Role.admin)),
):
    result = await db.execute(select(Parent).where(Parent.id == parent_id))
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    await db.delete(parent)
    await db.commit()


@router.post("/{parent_id}/students", response_model=ParentStudentOut, status_code=status.HTTP_201_CREATED)
async def link_student(
    parent_id: uuid.UUID,
    body: ParentStudentLink,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parent = (await db.execute(select(Parent).where(Parent.id == parent_id))).scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    student = (await db.execute(select(Student).where(Student.id == body.student_id))).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    link = ParentStudent(parent_id=parent_id, student_id=body.student_id, relationship_type=body.relationship_type)
    db.add(link)
    await db.commit()
    return ParentStudentOut(
        student_id=student.id, student_name=student.name, grade=student.grade,
        relationship_type=body.relationship_type,
    )
