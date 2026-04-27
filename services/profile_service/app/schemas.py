from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class UserRegisterIn(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime
    is_active: bool

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    interests: Optional[List[str]] = None
    photo_ids: Optional[List[str]] = None
    photos_count: Optional[int] = None

class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    interests: Optional[List[str]] = None
    photo_ids: Optional[List[str]] = None
    photos_count: int
    completeness_score: float

class UserPreferenceUpdate(BaseModel):
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    preferred_gender: Optional[str] = None
    preferred_city: Optional[str] = None

class UserPreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    preferred_gender: Optional[str] = None
    preferred_city: Optional[str] = None

