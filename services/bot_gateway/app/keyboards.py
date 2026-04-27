from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_kb() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="1. Смотреть анкеты")],
        [KeyboardButton(text="2. Моя анкета")],
        [KeyboardButton(text="3. Кто меня лайкнул")],
        [KeyboardButton(text="4. Я больше не хочу никого искать")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_my_profile_kb() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="1. Смотреть анкеты")],
        [KeyboardButton(text="2. Заполнить анкету заново")],
        [KeyboardButton(text="3. Изменить фото/видео")],
        [KeyboardButton(text="4. Изменить текст анкеты")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_viewing_kb() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="👍"), KeyboardButton(text="👎")],
        [KeyboardButton(text="Вернуться в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_skip_photo_kb() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="Без фото")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_gender_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Парень", callback_data="gender_m")],
        [InlineKeyboardButton(text="Девушка", callback_data="gender_f")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_like_response_kb() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="👍"), KeyboardButton(text="👎")],
        [KeyboardButton(text="Вернуться в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
