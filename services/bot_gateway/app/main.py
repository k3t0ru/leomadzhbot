import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import BOT_TOKEN
from app.profile_api import register_user


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    tg_user = message.from_user
    if tg_user is None:
        await message.answer("Не удалось прочитать данные пользователя Telegram.")
        return

    try:
        registered = await register_user(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
    except Exception:
        await message.answer("Сервис профилей временно недоступен. Попробуй позже.")
        return

    await message.answer(
        "Регистрация выполнена.\n"
        f"Твой ID в системе: {registered.id}\n"
        "Дальше здесь будет заполнение анкеты."
    )


async def main() -> None:

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

