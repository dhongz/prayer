from pydantic import BaseModel, Field
from app.models import PrayerType

class Prayer(BaseModel):
    entity: str = Field(description="The entity being prayed for - e.g. 'Family', 'John', 'Job', 'Health', 'Financial', 'Opportunity', 'Peace'")
    synopsis: str = Field(description="A concise summary of the prayer - e.g. 'My family is in need of financial stability', 'John is seeking a new job', 'Dan became a dad', 'God has blessed me with good health'")
    description: str = Field(description="A detailed description of the entity being prayed for including the specific details of the prayer")
    prayer_type: PrayerType = Field(description="The type of prayer: thanksgiving - (), worship(), request()")

class PrayerList(BaseModel):
    prayers: list[Prayer] = Field(description="A list of prayers following the format of the Prayer model")

