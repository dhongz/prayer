from pydantic import BaseModel, Field
from app.models import PrayerType

class Prayer(BaseModel):
    entity: str = Field(description="The entity being prayed for - e.g. 'Family', 'John', 'Job', 'Health', 'Financial', 'Opportunity', 'Peace'")
    synopsis: str = Field(description="A concise summary of the prayer - e.g. 'My family is in need of financial stability', 'John is seeking a new job', 'Dan became a dad', 'God has blessed me with good health'")
    description: str = Field(description="A detailed description of the entity being prayed for including the specific details of the prayer")
    prayer_type: PrayerType = Field(description="The type of prayer: thanksgiving - (), worship(), request()")

class PrayerList(BaseModel):
    prayers: list[Prayer] = Field(description="A list of prayers following the format of the Prayer model")


class Query(BaseModel):
    """A refined search query for vector embedding"""
    verse_text: str = Field(description="The text of the Bible verse that is relevant to the prayer")
    verse_details: str = Field(description="The details of the verse including the book, chapter, and verse number")
    justification: str = Field(description="A brief explanation of why you selected this type of verse focusing on the core themes of the prayer and verse. DO not mention the verse text or verse reference in the justification.")