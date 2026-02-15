import csv
import io
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user, role_required
from app.models.info_session import InfoSession, Registration, RegistrationStatus
from app.models.user import Role, User
from app.schemas.info_session import (
    ImportResult,
    InfoSessionCreate,
    InfoSessionOut,
    InfoSessionUpdate,
    RegistrationCreate,
    RegistrationOut,
    SendEmailResult,
)
from app.services.email import send_notification_email

router = APIRouter(prefix="/api/info-sessions", tags=["info-sessions"])


# ---- InfoSession CRUD ----

@router.get("", response_model=list[InfoSessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(
            InfoSession,
            func.count(Registration.id).label("reg_count"),
        )
        .outerjoin(Registration, Registration.session_id == InfoSession.id)
        .group_by(InfoSession.id)
        .order_by(InfoSession.session_date.desc())
    )
    rows = (await db.execute(stmt)).all()
    result = []
    for session, reg_count in rows:
        out = InfoSessionOut.model_validate(session)
        out.registration_count = reg_count
        result.append(out)
    return result


@router.post("", response_model=InfoSessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: InfoSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = InfoSession(**body.model_dump())
    db.add(session)
    await db.commit()
    await db.refresh(session)
    out = InfoSessionOut.model_validate(session)
    out.registration_count = 0
    return out


@router.get("/{session_id}")
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InfoSession)
        .options(selectinload(InfoSession.registrations))
        .where(InfoSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": str(session.id),
        "title": session.title,
        "description": session.description,
        "session_date": session.session_date.isoformat(),
        "session_time": session.session_time,
        "location": session.location,
        "capacity": session.capacity,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "registrations": [
            {
                "id": str(r.id),
                "name": r.name,
                "email": r.email,
                "status": r.status.value,
                "email_sent": r.email_sent,
                "note": r.note,
                "created_at": r.created_at.isoformat(),
            }
            for r in sorted(session.registrations, key=lambda r: r.created_at)
        ],
    }


@router.put("/{session_id}", response_model=InfoSessionOut)
async def update_session(
    session_id: uuid.UUID,
    body: InfoSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(InfoSession).where(InfoSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(session, field, value)
    await db.commit()
    await db.refresh(session)
    # count registrations
    count_result = await db.execute(
        select(func.count(Registration.id)).where(Registration.session_id == session_id)
    )
    out = InfoSessionOut.model_validate(session)
    out.registration_count = count_result.scalar() or 0
    return out


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(Role.admin)),
):
    result = await db.execute(select(InfoSession).where(InfoSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()


# ---- Registrations ----

@router.post("/{session_id}/registrations", response_model=RegistrationOut, status_code=status.HTTP_201_CREATED)
async def add_registration(
    session_id: uuid.UUID,
    body: RegistrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (await db.execute(select(InfoSession).where(InfoSession.id == session_id))).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    reg = Registration(session_id=session_id, name=body.name, email=body.email, note=body.note)
    db.add(reg)
    await db.commit()
    await db.refresh(reg)
    return RegistrationOut.model_validate(reg)


@router.delete("/{session_id}/registrations/{reg_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_registration(
    session_id: uuid.UUID,
    reg_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Registration).where(Registration.id == reg_id, Registration.session_id == session_id)
    )
    reg = result.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
    await db.delete(reg)
    await db.commit()


@router.post("/{session_id}/registrations/import", response_model=ImportResult)
async def import_registrations(
    session_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (await db.execute(select(InfoSession).where(InfoSession.id == session_id))).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    content = (await file.read()).decode("utf-8-sig")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return ImportResult(imported=0, skipped=0)

    # Auto-detect header row: skip if first row has no '@' in any field
    start = 0
    if rows[0] and not any("@" in cell for cell in rows[0]):
        start = 1

    imported = 0
    skipped = 0
    for row in rows[start:]:
        if len(row) < 2:
            skipped += 1
            continue
        name = row[0].strip()
        email = row[1].strip()
        if not name or not email:
            skipped += 1
            continue
        reg = Registration(session_id=session_id, name=name, email=email)
        db.add(reg)
        imported += 1

    await db.commit()
    return ImportResult(imported=imported, skipped=skipped)


# ---- Email ----

@router.post("/{session_id}/send-email", response_model=SendEmailResult)
async def send_email(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InfoSession)
        .options(selectinload(InfoSession.registrations))
        .where(InfoSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    unsent = [r for r in session.registrations if not r.email_sent and r.status != RegistrationStatus.cancelled]
    sent_count = 0
    for reg in unsent:
        subject = f"說明會通知：{session.title}"
        body = (
            f"{reg.name} 您好，\n\n"
            f"感謝您報名「{session.title}」說明會。\n"
            f"日期：{session.session_date}\n"
            f"時間：{session.session_time}\n"
            f"地點：{session.location}\n\n"
            f"期待您的蒞臨！"
        )
        ok = await send_notification_email(reg.email, reg.name, subject, body)
        if ok:
            reg.email_sent = True
            sent_count += 1

    await db.commit()
    return SendEmailResult(sent=sent_count, message=f"已發送 {sent_count} 封通知（placeholder）")
