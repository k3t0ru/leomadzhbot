from aiogram.fsm.state import StatesGroup, State

class ProfileForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_city = State()
    waiting_for_description = State()
    waiting_for_interests = State()
    waiting_for_photo = State()

class PreferenceForm(StatesGroup):
    waiting_for_min_age = State()
    waiting_for_max_age = State()
    waiting_for_gender = State()
    waiting_for_city = State()

class ViewingProfiles(StatesGroup):
    active = State()

class RespondingToLikes(StatesGroup):
    active = State()
