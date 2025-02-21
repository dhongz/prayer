from pydantic import BaseModel
from datetime import datetime
import uuid

from app.models.models import PrayerType

class ParsedPrayer(BaseModel):
    id: uuid.UUID
    transcription: str
    entity: str
    synopsis: str
    description: str
    prayer_type: PrayerType



#  Process Prayers
class PrayerText(BaseModel):
    text: str

class PreviewPrayers(BaseModel):
    prayer: str


# CRUD Prayers
class PrayerCreate(BaseModel):
    prayer: str

class PrayerUpdate(BaseModel):
    prayer: str

class PrayerDelete(BaseModel):
    prayer_id: str


class PrayerResponse(BaseModel):
    id: str
    transcription: str
    entity: str
    synopsis: str
    description: str
    prayer_type: PrayerType
    is_answered: bool
    created_at: datetime

    class Config:
        from_attributes = True

    def dict(self, *args, **kwargs):
        d = super().model_dump(*args, **kwargs)
        d['created_at'] = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return d
