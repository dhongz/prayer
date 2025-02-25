from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DeviceTokenCreate(BaseModel):
    device_token: str

