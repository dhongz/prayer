from pydantic import BaseModel

class AppleToken(BaseModel):
    apple_token: str

class AccessToken(BaseModel):
    access_token: str
