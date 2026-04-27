import redis.asyncio as redis
import json
import httpx
from typing import List, Dict, Any
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
PROFILE_SERVICE_URL = os.getenv("PROFILE_SERVICE_BASE_URL", "http://profile-service:8000")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def prefetch_profiles(user_id: int, limit: int = 15):
    """Fetches recommendations from the Profile Service and pushes them to Redis."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PROFILE_SERVICE_URL}/api/v1/recommendations/{user_id}?limit={limit}")
        if response.status_code == 200:
            profiles = response.json()
            if profiles:
                # Push to Redis list
                key = f"user:{user_id}:recommendations"
                # Clear existing to prevent duplicates
                await redis_client.delete(key)
                for profile in profiles:
                    await redis_client.rpush(key, json.dumps(profile))
            return profiles
    return []

async def get_next_profile(user_id: int) -> Dict[str, Any] | None:
    """Pops the next profile from Redis. If queue is running low, trigger a background prefetch."""
    key = f"user:{user_id}:recommendations"
    
    # Check remaining length
    queue_length = await redis_client.llen(key)
    
    # If 2 or fewer profiles left, trigger prefetch (in real app, use asyncio.create_task)
    if queue_length <= 2:
        # Simple sync wait for now, can be backgrounded
        await prefetch_profiles(user_id, limit=10)
        
    profile_json = await redis_client.lpop(key)
    if profile_json:
        return json.loads(profile_json)
        
    return None
