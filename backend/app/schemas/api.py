from pydantic import BaseModel

class Message(BaseModel):
    message: str

    class Config:
        from_attributes = True