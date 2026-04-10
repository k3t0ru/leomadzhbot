from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import engine, get_session
from app.models import Base, User
from app.schemas import UserOut, UserRegisterIn


app = FastAPI(title="Profile Service")


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/users/register", response_model=UserOut)
async def register_user(
    payload: UserRegisterIn, session: AsyncSession = Depends(get_session)
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == payload.telegram_id))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(
        telegram_id=payload.telegram_id,
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

