from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.models import User
from app.db.database import get_db
from app.services.auth import get_current_user

from app.schemas.prayers import (PrayerCreate, 
                                 PrayerUpdate, 
                                 PrayerDelete, 
                                 PrayerText,
                                 ParsedPrayer,
                                 PrayerResponse)
from app.services.prayers import (process_create_prayer, 
                                  process_get_prayers, 
                                  process_update_prayer, 
                                  process_delete_prayer,
                                  process_text_prayers,
                                  process_audio_prayers,
                                  process_bulk_create_prayer,
                                  process_share_prayer_to_walls,
                                  process_remove_prayer_from_wall,
                                  process_get_prayer_walls)


router = APIRouter()

@router.post("")
async def create_prayer(prayer: PrayerCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await process_create_prayer(prayer, db, current_user)

@router.get("")
async def get_prayers(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await process_get_prayers(db, current_user)

@router.put("/{prayer_id}")
async def update_prayer(prayer_id: str, prayer: PrayerUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await process_update_prayer(prayer_id, prayer, db, current_user)

@router.delete("/{prayer_id}")
async def delete_prayer(prayer_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await process_delete_prayer(prayer_id, db)

@router.post("/process-text")
async def process_text(prayer: PrayerText, current_user: User = Depends(get_current_user)):
    return await process_text_prayers(prayer)

@router.post("/process-audio")
async def process_audio(prayer_audio: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    
    return await process_audio_prayers(prayer_audio)

@router.post("/bulk-create-prayers")
async def bulk_create_prayers(prayers: List[ParsedPrayer], db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await process_bulk_create_prayer(prayers, db, current_user)



@router.post("/{prayer_id}/walls")
async def share_prayer_to_walls(
    prayer_id: str, 
    wall_ids: List[str], 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return await process_share_prayer_to_walls(prayer_id, wall_ids, db, current_user)

@router.delete("/{prayer_id}/walls/{wall_id}")
async def remove_from_wall(
    prayer_id: str,
    wall_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await process_remove_prayer_from_wall(prayer_id, wall_id, db, current_user)

@router.get("/{prayer_id}/walls")
async def get_prayer_walls(
    prayer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await process_get_prayer_walls(prayer_id, db, current_user)
