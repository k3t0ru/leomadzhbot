from dataclasses import dataclass

import httpx

from app.config import settings


@dataclass(frozen=True)
class RegisteredUser:
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None


async def register_user(
    *,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> RegisteredUser:
    url = f"{settings.profile_service_base_url}/api/v1/users/register"
    payload = {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    return RegisteredUser(
        id=data["id"],
        telegram_id=data["telegram_id"],
        username=data.get("username"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
    )

