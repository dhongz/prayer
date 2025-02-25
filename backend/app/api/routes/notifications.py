from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.db.database import get_db
from app.services.auth import get_current_user
from app.services.notifications import register_device_token
from app.schemas.notifications import DeviceTokenCreate
from app.schemas.api import Message

router = APIRouter()

@router.post("/register-device", response_model=Message)
async def register_device(
    token: DeviceTokenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await register_device_token(token.device_token, db, current_user) 