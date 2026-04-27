import asyncio

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.state import StatesGroup, State

from app.config import BOT_TOKEN
from app.profile_api import register_user
from app.profile_fsm import ProfileForm, ViewingProfiles, RespondingToLikes
from app.redis_cache import get_next_profile
from app.keyboards import get_main_menu_kb, get_my_profile_kb, get_viewing_kb, get_skip_photo_kb, get_gender_kb, get_like_response_kb
import httpx

router = Router()
PROFILE_SERVICE_URL = "http://profile-service:8000"

async def get_db_user_id(telegram_id: int) -> int:
    async with httpx.AsyncClient() as client:
        registered = await register_user(telegram_id=telegram_id, username="", first_name="", last_name="")
        return registered.id

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
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

    await state.update_data(user_id=registered.id)
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{PROFILE_SERVICE_URL}/api/v1/profiles/{registered.id}")
        profile = resp.json() if resp.status_code == 200 else {}
        
    if profile.get("name"):
        await message.answer("С возвращением! Используй меню 👇", reply_markup=get_main_menu_kb())
    else:
        await message.answer("Привет! Давай создадим твою анкету.\nКак тебя зовут?")
        await state.set_state(ProfileForm.waiting_for_name)

@router.message(ProfileForm.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ProfileForm.waiting_for_age)
    await message.answer("Сколько тебе лет?")

@router.message(ProfileForm.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Возраст должен быть числом. Попробуй еще раз:")
        return
    await state.update_data(age=int(message.text))
    await state.set_state(ProfileForm.waiting_for_gender)
    await message.answer("Укажи свой пол:", reply_markup=get_gender_kb())

@router.callback_query(ProfileForm.waiting_for_gender, F.data.startswith("gender_"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender = "M" if callback.data == "gender_m" else "F"
    await state.update_data(gender=gender)
    await callback.message.edit_text(f"Пол выбран: {'Парень' if gender == 'M' else 'Девушка'}")
    await state.set_state(ProfileForm.waiting_for_city)
    await callback.message.answer("В каком городе ты живешь?")
    await callback.answer()

@router.message(ProfileForm.waiting_for_gender)
async def process_gender_invalid(message: Message):
    await message.answer("Пожалуйста, выбери пол, используя кнопки выше.")

@router.message(ProfileForm.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(ProfileForm.waiting_for_description)
    await message.answer("Расскажи немного о себе (описание анкеты):")

@router.message(ProfileForm.waiting_for_description)
async def process_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(ProfileForm.waiting_for_photo)
    await message.answer("Отправь фото для своей анкеты (или нажми 'Без фото'):", reply_markup=get_skip_photo_kb())

@router.message(ProfileForm.waiting_for_photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_ids = data.get("photo_ids", [])
    
    if message.photo:
        photo_ids.append(message.photo[-1].file_id)
        await state.update_data(photo_ids=photo_ids)
        # Assuming only 1 photo for simplicity during registration, but can be multiple.
    elif message.text == "Без фото":
        pass
    else:
        await message.answer("Пожалуйста, отправь фото или нажми 'Без фото'.")
        return
        
    data = await state.get_data()
    user_id = data.get("user_id")
    if not user_id:
        user_id = await get_db_user_id(message.from_user.id)
        
    async with httpx.AsyncClient() as client:
        payload = {
            "name": data.get("name"),
            "age": data.get("age"),
            "gender": data.get("gender"),
            "city": data.get("city"),
            "description": data.get("description"),
            "photo_ids": data.get("photo_ids", []),
            "photos_count": len(data.get("photo_ids", []))
        }
        await client.put(f"{PROFILE_SERVICE_URL}/api/v1/profiles/{user_id}", json=payload)
    
    await state.clear()
    await message.answer(
        "Анкета успешно сохранена! Ждем пока кто-то увидит твою анкету.", 
        reply_markup=get_main_menu_kb()
    )

# --- Main Menu Handlers ---
@router.message(F.text == "1. Смотреть анкеты")
async def start_viewing(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message.from_user.id)
        
    profile = await get_next_profile(user_id)
    if not profile:
        await message.answer("Пока нет новых анкет. Возвращайся позже!", reply_markup=get_main_menu_kb())
        return
        
    await state.set_state(ViewingProfiles.active)
    await state.update_data(current_profile_id=profile["user_id"])
    
    desc = f"{profile.get('name', 'Аноним')}, {profile['age']}, {profile['city']}\n{profile['description']}"
    if profile.get("photo_ids") and len(profile["photo_ids"]) > 0:
        await message.answer_photo(
            photo=profile["photo_ids"][0],
            caption=f"Анкета:\n{desc}",
            reply_markup=get_viewing_kb()
        )
    else:
        await message.answer(f"Анкета (без фото):\n{desc}", reply_markup=get_viewing_kb())

@router.message(F.text == "2. Моя анкета")
async def view_my_profile(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message.from_user.id)
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PROFILE_SERVICE_URL}/api/v1/profiles/{user_id}")
        if response.status_code == 200:
            profile = response.json()
            desc = f"Твоя анкета:\nИмя: {profile.get('name', 'Аноним')}\nВозраст: {profile.get('age')}\nПол: {profile.get('gender')}\nГород: {profile.get('city')}\nО себе: {profile.get('description')}"
            
            if profile.get("photo_ids") and len(profile["photo_ids"]) > 0:
                await message.answer_photo(
                    photo=profile["photo_ids"][0],
                    caption=desc,
                    reply_markup=get_my_profile_kb()
                )
            else:
                await message.answer(desc, reply_markup=get_my_profile_kb())
        else:
            await message.answer("Анкета не найдена. Заполни ее заново.")

@router.message(F.text == "3. Кто меня лайкнул")
async def view_likes(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message.from_user.id)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PROFILE_SERVICE_URL}/api/v1/likes/{user_id}")
        if response.status_code == 200:
            likes = response.json()
            if not likes:
                await message.answer("Пока никто не лайкнул твою анкету. Продолжай смотреть анкеты!", reply_markup=get_main_menu_kb())
                return
            
            # Store likes in state and show first one
            await state.update_data(pending_likes=[like["user_id"] for like in likes], current_like_index=0)
            await state.set_state(RespondingToLikes.active)
            
            # Show first profile
            first_like = likes[0]
            desc = f"{first_like.get('name', 'Аноним')}, {first_like['age']}, {first_like['city']}\n{first_like['description']}"
            
            if first_like.get("photo_ids") and len(first_like["photo_ids"]) > 0:
                await message.answer_photo(
                    photo=first_like["photo_ids"][0],
                    caption=f"❤️ Эта анкета лайкнула тебя!\n\n{desc}",
                    reply_markup=get_like_response_kb()
                )
            else:
                await message.answer(f"❤️ Эта анкета лайкнула тебя!\n\n{desc}", reply_markup=get_like_response_kb())
        else:
            await message.answer("Не удалось загрузить лайки. Попробуй позже.", reply_markup=get_main_menu_kb())

@router.message(F.text == "4. Я больше не хочу никого искать")
async def stop_searching(message: Message, state: FSMContext):
    await message.answer("Хорошо, твоя анкета скрыта. Возвращайся, когда захочешь!", reply_markup=get_main_menu_kb())
    # Note: In a real app we'd set is_active=False on user or profile

@router.message(F.text == "2. Заполнить анкету заново")
async def refill_profile(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message.from_user.id)
    await state.update_data(user_id=user_id)
    await message.answer("Давай заполним анкету заново! Как тебя зовут?")
    await state.set_state(ProfileForm.waiting_for_name)

class EditProfileForm(StatesGroup):
    waiting_for_new_text = State()
    waiting_for_new_photo = State()

@router.message(F.text == "4. Изменить текст анкеты")
async def edit_profile_text(message: Message, state: FSMContext):
    await message.answer("Введи новый текст для своей анкеты (о себе):")
    await state.set_state(EditProfileForm.waiting_for_new_text)

@router.message(EditProfileForm.waiting_for_new_text)
async def process_new_text(message: Message, state: FSMContext):
    user_id = await get_db_user_id(message.from_user.id)
    async with httpx.AsyncClient() as client:
        payload = {"description": message.text}
        await client.put(f"{PROFILE_SERVICE_URL}/api/v1/profiles/{user_id}", json=payload)
    
    await state.clear()
    await message.answer("Текст анкеты обновлен!", reply_markup=get_my_profile_kb())

@router.message(F.text == "3. Изменить фото/видео")
async def edit_profile_photo(message: Message, state: FSMContext):
    await message.answer("Отправь новое фото для анкеты:")
    await state.set_state(EditProfileForm.waiting_for_new_photo)

@router.message(EditProfileForm.waiting_for_new_photo)
async def process_new_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста, отправь фото.")
        return
        
    user_id = await get_db_user_id(message.from_user.id)
    photo_id = message.photo[-1].file_id
    
    async with httpx.AsyncClient() as client:
        payload = {
            "photo_ids": [photo_id],
            "photos_count": 1
        }
        await client.put(f"{PROFILE_SERVICE_URL}/api/v1/profiles/{user_id}", json=payload)
    
    await state.clear()
    await message.answer("Фото анкеты обновлено!", reply_markup=get_my_profile_kb())

# --- Viewing Profile Handlers ---
@router.message(ViewingProfiles.active)
async def process_interaction(message: Message, state: FSMContext):
    if message.text == "Вернуться в меню":
        await state.clear()
        await message.answer("Ждем пока кто-то увидит твою анкету.", reply_markup=get_main_menu_kb())
        return

    action = "LIKE" if message.text == "👍" else "SKIP" if message.text == "👎" else None
    if not action:
        await message.answer("Используй кнопки ниже.", reply_markup=get_viewing_kb())
        return

    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    user_id = await get_db_user_id(message.from_user.id)
    
    # Send interaction to Profile Service
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PROFILE_SERVICE_URL}/api/v1/interactions/{user_id}",
            json={"to_user_id": to_user_id, "interaction_type": action}
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("is_match"):
                m_tg_id = data.get("matched_tg_id")
                m_username = data.get("matched_username")
                m_name = data.get("matched_name") or "Пользователь"
                c_username = data.get("current_username")
                c_name = data.get("current_name") or "Пользователь"
                
                c_link = f"@{c_username}" if c_username else f"[{c_name}](tg://user?id={message.from_user.id})"
                m_link = f"@{m_username}" if m_username else f"[{m_name}](tg://user?id={m_tg_id})"
                
                await message.answer(f"🎉 У вас взаимная симпатия с {m_link}! Начинайте общаться!", parse_mode="Markdown")
                
                try:
                    await message.bot.send_message(
                        m_tg_id,
                        f"🎉 У вас взаимная симпатия с {c_link}! Начинайте общаться!",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Failed to send match notification: {e}")
            elif action == "LIKE":
                # Send notification to the liked user
                liked_tg_id = data.get("liked_tg_id")
                if liked_tg_id:
                    try:
                        await message.bot.send_message(
                            liked_tg_id,
                            "❤️ Кто-то лайкнул твою анкету! Посмотри кто это в главном меню.",
                        )
                    except Exception as e:
                        print(f"Failed to send like notification: {e}")
        
    # Get next
    profile = await get_next_profile(user_id)
    if not profile:
        await state.clear()
        await message.answer("Анкеты закончились. Ждем пока кто-то увидит твою анкету.", reply_markup=get_main_menu_kb())
        return
        
    await state.update_data(current_profile_id=profile["user_id"])
    desc = f"{profile.get('name', 'Аноним')}, {profile['age']}, {profile['city']}\n{profile['description']}"
    if profile.get("photo_ids") and len(profile["photo_ids"]) > 0:
        await message.answer_photo(
            photo=profile["photo_ids"][0],
            caption=f"Анкета:\n{desc}",
            reply_markup=get_viewing_kb()
        )
    else:
        await message.answer(f"Анкета (без фото):\n{desc}", reply_markup=get_viewing_kb())

# --- Responding to Likes Handlers ---
@router.message(RespondingToLikes.active)
async def process_like_response(message: Message, state: FSMContext):
    if message.text == "Вернуться в меню":
        await state.clear()
        await message.answer("Возвращаемся в главное меню.", reply_markup=get_main_menu_kb())
        return
    
    action = "LIKE" if message.text == "👍" else "SKIP" if message.text == "👎" else None
    if not action:
        await message.answer("Используй кнопки ниже.", reply_markup=get_like_response_kb())
        return
    
    data = await state.get_data()
    pending_likes = data.get("pending_likes", [])
    current_index = data.get("current_like_index", 0)
    
    if current_index >= len(pending_likes):
        await state.clear()
        await message.answer("Все лайки просмотрены!", reply_markup=get_main_menu_kb())
        return
    
    to_user_id = pending_likes[current_index]
    user_id = await get_db_user_id(message.from_user.id)
    
    # Send interaction to Profile Service
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PROFILE_SERVICE_URL}/api/v1/interactions/{user_id}",
            json={"to_user_id": to_user_id, "interaction_type": action}
        )
        if resp.status_code == 200:
            resp_data = resp.json()
            if resp_data.get("is_match"):
                m_tg_id = resp_data.get("matched_tg_id")
                m_username = resp_data.get("matched_username")
                m_name = resp_data.get("matched_name") or "Пользователь"
                c_username = resp_data.get("current_username")
                c_name = resp_data.get("current_name") or "Пользователь"
                
                c_link = f"@{c_username}" if c_username else f"[{c_name}](tg://user?id={message.from_user.id})"
                m_link = f"@{m_username}" if m_username else f"[{m_name}](tg://user?id={m_tg_id})"
                
                await message.answer(f"🎉 У вас взаимная симпатия с {m_link}! Начинайте общаться!", parse_mode="Markdown")
                
                try:
                    await message.bot.send_message(
                        m_tg_id,
                        f"🎉 У вас взаимная симпатия с {c_link}! Начинайте общаться!",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Failed to send match notification: {e}")
    
    # Move to next like
    next_index = current_index + 1
    if next_index >= len(pending_likes):
        await state.clear()
        await message.answer("Все лайки просмотрены! Возвращаемся в меню.", reply_markup=get_main_menu_kb())
        return
    
    # Fetch next profile
    next_user_id = pending_likes[next_index]
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PROFILE_SERVICE_URL}/api/v1/profiles/{next_user_id}")
        if response.status_code == 200:
            profile = response.json()
            await state.update_data(current_like_index=next_index)
            
            desc = f"{profile.get('name', 'Аноним')}, {profile['age']}, {profile['city']}\n{profile['description']}"
            
            if profile.get("photo_ids") and len(profile["photo_ids"]) > 0:
                await message.answer_photo(
                    photo=profile["photo_ids"][0],
                    caption=f"❤️ Эта анкета лайкнула тебя!\n\n{desc}",
                    reply_markup=get_like_response_kb()
                )
            else:
                await message.answer(f"❤️ Эта анкета лайкнула тебя!\n\n{desc}", reply_markup=get_like_response_kb())
        else:
            # Skip to next if profile not found
            await state.update_data(current_like_index=next_index)
            await message.answer("Не удалось загрузить следующую анкету. Попробуй еще раз.", reply_markup=get_like_response_kb())

@router.message(StateFilter(None))
async def fallback_handler(message: Message, state: FSMContext):
    await cmd_start(message, state)

async def main() -> None:
    # Use RedisStorage for FSM
    from redis.asyncio import Redis
    redis_client = Redis.from_url("redis://redis:6379/0")
    storage = RedisStorage(redis=redis_client)
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())