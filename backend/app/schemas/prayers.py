from pydantic import BaseModel
from datetime import datetime
from typing import List

from app.models.models import PrayerType
from app.schemas.prayer_walls import PrayerWallResponse

class ParsedPrayer(BaseModel):
    id: str
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


class VerseRecommendationResponse(BaseModel):
    book_name: str
    chapter_number: int
    verse_number_start: int
    verse_number_end: int | None
    verse_text: str
    justification: str
    relevance_score: float
    verse_reference: str

    class Config:
        from_attributes = True

class PrayerResponse(BaseModel):
    id: str
    transcription: str
    entity: str
    synopsis: str
    description: str
    prayer_type: PrayerType
    is_answered: bool
    created_at: datetime
    verse_recommendations: List[VerseRecommendationResponse] = []

    class Config:
        from_attributes = True

    def dict(self, *args, **kwargs):
        d = super().model_dump(*args, **kwargs)
        d['created_at'] = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return d

class PrayerWallsResponse(BaseModel):
    prayer_walls: List[PrayerWallResponse]

    class Config:
        from_attributes = True
