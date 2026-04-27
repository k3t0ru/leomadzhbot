from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from app.models import Profile, UserPreference, ProfileInteraction
from typing import List

async def calculate_primary_score(candidate: Profile, seeker_prefs: UserPreference) -> float:
    score = candidate.completeness_score * 0.3  # Max 30 points for completeness
    score += min(candidate.photos_count * 5, 20)  # Max 20 points for photos (up to 4 photos)
    
    # Preference matching (max 50 points)
    if seeker_prefs.min_age and candidate.age and candidate.age >= seeker_prefs.min_age:
        score += 10
    if seeker_prefs.max_age and candidate.age and candidate.age <= seeker_prefs.max_age:
        score += 10
    if seeker_prefs.preferred_gender and candidate.gender == seeker_prefs.preferred_gender:
        score += 15
    if seeker_prefs.preferred_city and candidate.city and seeker_prefs.preferred_city.lower() in candidate.city.lower():
        score += 15
        
    return score

async def calculate_behavioral_score(session: AsyncSession, candidate_id: int) -> float:
    result = await session.execute(
        select(
            func.count().label("total"),
            func.sum(case((ProfileInteraction.interaction_type == "LIKE", 1), else_=0)).label("likes"),
            func.sum(case((ProfileInteraction.interaction_type == "MATCH", 1), else_=0)).label("matches")
        ).where(ProfileInteraction.to_user_id == candidate_id)
    )
    row = result.one()
    total = row.total or 0
    likes = row.likes or 0
    matches = row.matches or 0
    
    if total == 0:
        return 50.0  # Default neutral score
        
    like_ratio = likes / total
    match_bonus = min(matches * 2, 20)  # Up to 20 bonus points for matches
    
    score = (like_ratio * 80) + match_bonus
    return min(score, 100.0)

async def get_ranked_profiles(session: AsyncSession, user_id: int, limit: int = 15) -> List[Profile]:
    # 1. Get user preferences
    prefs_result = await session.execute(select(UserPreference).where(UserPreference.user_id == user_id))
    seeker_prefs = prefs_result.scalar_one_or_none()
    if not seeker_prefs:
        seeker_prefs = UserPreference(user_id=user_id)
        
    # 2. Get profiles user hasn't interacted with yet
    subq = select(ProfileInteraction.to_user_id).where(ProfileInteraction.from_user_id == user_id)
    candidates_result = await session.execute(
        select(Profile).where(
            and_(
                Profile.user_id != user_id,
                Profile.user_id.notin_(subq)
            )
        )
    )
    candidates = candidates_result.scalars().all()
    
    # 3. Calculate combined score
    ranked_candidates = []
    for candidate in candidates:
        primary_score = await calculate_primary_score(candidate, seeker_prefs)
        behavioral_score = await calculate_behavioral_score(session, candidate.user_id)
        
        # Combined score (60% primary, 40% behavioral)
        combined_score = (primary_score * 0.6) + (behavioral_score * 0.4)
        ranked_candidates.append((combined_score, candidate))
        
    # Sort descending by score
    ranked_candidates.sort(key=lambda x: x[0], reverse=True)
    return [c[1] for c in ranked_candidates[:limit]]
