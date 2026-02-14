"""Create default admin user."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.user import Role, User
from app.services.auth import hash_password

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_FULL_NAME = "System Admin"


async def seed():
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == ADMIN_USERNAME))
        if result.scalar_one_or_none():
            print(f"User '{ADMIN_USERNAME}' already exists. Skipping.")
            return
        admin = User(
            username=ADMIN_USERNAME,
            hashed_password=hash_password(ADMIN_PASSWORD),
            full_name=ADMIN_FULL_NAME,
            role=Role.admin,
        )
        session.add(admin)
        await session.commit()
        print(f"Admin user created: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
