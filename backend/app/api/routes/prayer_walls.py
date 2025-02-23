from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.models import User
from app.db.database import get_db
from app.services.auth import get_current_user

from app.schemas.prayer_walls import (PrayerWallCreate, 
                                     PrayerWallUpdate, 
                                     PrayerWallResponse)
from app.services.prayer_walls import (process_create_prayer_wall, 
                                      process_get_prayer_walls, 
                                      process_update_prayer_wall, 
                                      process_delete_prayer_wall,
                                      process_get_wall_prayers,
                                      process_add_prayers_to_wall,
                                      process_remove_prayer_from_wall,
                                      process_generate_invite_link,
                                      process_get_wall_invite,
                                      process_join_wall_with_invite)


router = APIRouter()

@router.post("")
async def create_prayer_wall(prayer_wall: PrayerWallCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await process_create_prayer_wall(prayer_wall, db, current_user)

@router.get("")
async def get_prayer_walls(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await process_get_prayer_walls(db, current_user)

@router.get("/{wall_id}/prayers")
async def get_wall_prayers(
    wall_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await process_get_wall_prayers(wall_id, db, current_user)


@router.post("/{wall_id}/prayers")
async def add_prayers_to_wall(
    wall_id: str,
    prayer_ids: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await process_add_prayers_to_wall(wall_id, prayer_ids, db, current_user)

@router.delete("/{wall_id}/prayers/{prayer_id}")
async def remove_prayer_from_wall(
    wall_id: str,
    prayer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await process_remove_prayer_from_wall(wall_id, prayer_id, db, current_user)

@router.post("/{wall_id}/generate-invite")
async def generate_invite_link(
    wall_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await process_generate_invite_link(wall_id, db, current_user)

@router.get("/join/{invite_code}")
async def get_wall_invite(
    invite_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await process_get_wall_invite(invite_code, db, current_user)

@router.post("/join/{invite_code}")
async def join_wall_with_invite(
    invite_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await process_join_wall_with_invite(invite_code, db, current_user)