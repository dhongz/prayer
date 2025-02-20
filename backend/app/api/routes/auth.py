from fastapi import APIRouter, Depends, Request
from app.services.auth import apple_authentication
from app.schemas.auth import AppleToken
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/apple")
async def apple_auth(apple_token: AppleToken, db: AsyncSession = Depends(get_db)):
    return await apple_authentication(apple_token, db)