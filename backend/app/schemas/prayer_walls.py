from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class WallUser(BaseModel):
    id: str
    user_id: str
    role: str  # "owner" or "member"

    class Config:
        from_attributes = True

class PrayerWallCreate(BaseModel):
    title: str
    description: str
    is_public: bool

class PrayerWallUpdate(BaseModel):
    title: str
    description: str
    is_public: bool

class PrayerWallResponse(BaseModel):
    id: str
    title: str
    description: str
    is_public: bool
    created_at: datetime
    owner_id: str
    users: List[WallUser]

    class Config:
        from_attributes = True

    def dict(self, *args, **kwargs):
        d = super().model_dump(*args, **kwargs)
        d['created_at'] = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return d

class PrayerWallsResponse(BaseModel):
    prayer_walls: List[PrayerWallResponse]

class InviteLinkResponse(BaseModel):
    invite_code: str
    wall_title: str
    expires_at: datetime

    def dict(self, *args, **kwargs):
        d = super().model_dump(*args, **kwargs)
        d['expires_at'] = self.expires_at.strftime("%Y-%m-%d %H:%M:%S")
        return d

class WallInviteResponse(BaseModel):
    wall_title: str
    description: str
    owner_name: str
    member_count: int

class JoinWallResponse(BaseModel):
    message: str
    wall: PrayerWallResponse