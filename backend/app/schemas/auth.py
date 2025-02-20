from pydantic import BaseModel

class AppleToken(BaseModel):
    appleToken: str

class AccessToken(BaseModel):
    accessToken: str
