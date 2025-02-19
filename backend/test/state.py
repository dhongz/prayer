from pydantic import BaseModel, Field

class ContinueAdding(BaseModel):
    """Whether to continue adding verses to the current document"""
    continue_adding: bool = Field(description="Whether to continue adding verses to the current document")


class Query(BaseModel):
    """A refined search query for vector embedding"""
    verse: str = Field(description="A Bible verse that is relevant to the prayer")
    verse_details: str = Field(description="The details of the verse including the book, chapter, and verse number")
    justification: str = Field(description="A brief explanation of why you selected this verse and how it relates to the core themes of the prayer")