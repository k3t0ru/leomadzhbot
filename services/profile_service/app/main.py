from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.db import engine, get_session
from app.models import Base, User, Profile, UserPreference, ProfileInteraction
from app.schemas import UserOut, UserRegisterIn, ProfileOut, ProfileUpdate, UserPreferenceOut, UserPreferenceUpdate
from app.ranking import get_ranked_profiles
from app.minio_client import upload_photo, ensure_bucket_exists

app = FastAPI(title="Profile Service")


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    ensure_bucket_exists()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/api/v1/profiles/{user_id}/photo")
async def upload_profile_photo(user_id: int, file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    file_ext = file.filename.split(".")[-1] if file.filename else "jpg"
    file_name = f"user_{user_id}/{uuid.uuid4()}.{file_ext}"
    
    file_data = await file.read()
    minio_path = await upload_photo(file_data, file_name)
    
    if not minio_path:
        raise HTTPException(status_code=500, detail="Failed to upload photo")

    # Update profile with new photo path
    if profile.photo_ids is None:
        profile.photo_ids = []
    
    profile.photo_ids.append(minio_path)
    profile.photos_count = len(profile.photo_ids)
    profile.completeness_score = calculate_completeness(profile)
    
    await session.commit()
    await session.refresh(profile)
    
    return {"status": "ok", "photo_url": minio_path}


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
    
    # Create empty profile and preferences for the new user
    profile = Profile(user_id=user.id)
    prefs = UserPreference(user_id=user.id)
    session.add(profile)
    session.add(prefs)
    await session.commit()
    
    return user

def calculate_completeness(profile: Profile) -> float:
    score = 0.0
    fields = ['name', 'age', 'gender', 'city', 'description', 'interests']
    filled = sum(1 for field in fields if getattr(profile, field) is not None)
    score = (filled / len(fields)) * 100.0
    return score

@app.get("/api/v1/profiles/{user_id}", response_model=ProfileOut)
async def get_profile(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = Profile(user_id=user_id)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
    return profile

@app.put("/api/v1/profiles/{user_id}", response_model=ProfileOut)
async def update_profile(user_id: int, payload: ProfileUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = Profile(user_id=user_id)
        session.add(profile)
    
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
        
    profile.completeness_score = calculate_completeness(profile)
    
    await session.commit()
    await session.refresh(profile)
    return profile

@app.get("/api/v1/preferences/{user_id}", response_model=UserPreferenceOut)
async def get_preferences(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(UserPreference).where(UserPreference.user_id == user_id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = UserPreference(user_id=user_id)
        session.add(prefs)
        await session.commit()
        await session.refresh(prefs)
    return prefs

@app.put("/api/v1/preferences/{user_id}", response_model=UserPreferenceOut)
async def update_preferences(user_id: int, payload: UserPreferenceUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(UserPreference).where(UserPreference.user_id == user_id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = UserPreference(user_id=user_id)
        session.add(prefs)
    
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(prefs, key, value)
        
    await session.commit()
    await session.refresh(prefs)
    return prefs

from pydantic import BaseModel
class InteractionIn(BaseModel):
    to_user_id: int
    interaction_type: str

@app.post("/api/v1/interactions/{user_id}")
async def create_interaction(user_id: int, payload: InteractionIn, session: AsyncSession = Depends(get_session)):
    # Check if already interacted
    existing = await session.execute(
        select(ProfileInteraction).where(
            ProfileInteraction.from_user_id == user_id,
            ProfileInteraction.to_user_id == payload.to_user_id
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_interacted", "is_match": False}

    interaction = ProfileInteraction(
        from_user_id=user_id,
        to_user_id=payload.to_user_id,
        interaction_type=payload.interaction_type
    )
    session.add(interaction)
    
    is_match = False
    matched_tg_id = None
    matched_username = None
    matched_name = None
    current_username = None
    current_name = None
    liked_tg_id = None

    # Check for match
    if payload.interaction_type == "LIKE":
        result = await session.execute(
            select(ProfileInteraction).where(
                ProfileInteraction.from_user_id == payload.to_user_id,
                ProfileInteraction.to_user_id == user_id,
                ProfileInteraction.interaction_type == "LIKE"
            )
        )
        if result.scalar_one_or_none():
            interaction.interaction_type = "MATCH"
            is_match = True
            # Update the other direction as well
            from sqlalchemy import update
            await session.execute(
                update(ProfileInteraction).where(
                    ProfileInteraction.from_user_id == payload.to_user_id,
                    ProfileInteraction.to_user_id == user_id,
                    ProfileInteraction.interaction_type == "LIKE"
                ).values(interaction_type="MATCH")
            )
            
            # Fetch user info for match notification
            c_user_obj = await session.execute(select(User).where(User.id == user_id))
            c_user = c_user_obj.scalar_one()
            current_username = c_user.username
            
            m_user_obj = await session.execute(select(User).where(User.id == payload.to_user_id))
            m_user = m_user_obj.scalar_one()
            matched_tg_id = m_user.telegram_id
            matched_username = m_user.username
            
            c_prof_obj = await session.execute(select(Profile).where(Profile.user_id == user_id))
            c_prof = c_prof_obj.scalar_one_or_none()
            if c_prof:
                current_name = c_prof.name
                
            m_prof_obj = await session.execute(select(Profile).where(Profile.user_id == payload.to_user_id))
            m_prof = m_prof_obj.scalar_one_or_none()
            if m_prof:
                matched_name = m_prof.name
        else:
            m_user_obj = await session.execute(select(User).where(User.id == payload.to_user_id))
            m_user = m_user_obj.scalar_one_or_none()
            if m_user:
                liked_tg_id = m_user.telegram_id
            
    await session.commit()
    return {
        "status": "ok", 
        "is_match": is_match,
        "matched_tg_id": matched_tg_id,
        "matched_username": matched_username,
        "matched_name": matched_name,
        "current_username": current_username,
        "current_name": current_name,
        "liked_tg_id": liked_tg_id
    }

@app.get("/api/v1/likes/{user_id}", response_model=List[ProfileOut])
async def get_likes(user_id: int, session: AsyncSession = Depends(get_session)):
    subq = select(ProfileInteraction.to_user_id).where(ProfileInteraction.from_user_id == user_id)
    
    query = select(Profile).join(
        ProfileInteraction, ProfileInteraction.from_user_id == Profile.user_id
    ).where(
        ProfileInteraction.to_user_id == user_id,
        ProfileInteraction.interaction_type == "LIKE",
        ProfileInteraction.from_user_id.notin_(subq)
    )
    result = await session.execute(query)
    return result.scalars().all()

@app.get("/api/v1/recommendations/{user_id}", response_model=List[ProfileOut])
async def get_recommendations(user_id: int, limit: int = 15, session: AsyncSession = Depends(get_session)):
    profiles = await get_ranked_profiles(session, user_id, limit)
    return profiles

