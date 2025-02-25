import jwt
import logging
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeviceToken, User
from app.schemas.api import Message
from app.config.apple_push import (
    create_push_notification_auth_token,
    send_push_notification
)

logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
logging.getLogger("prayer-api").setLevel(logging.INFO)
logger = logging.getLogger("prayer-api")


async def register_device_token(
    device_token: str,
    db: AsyncSession,
    current_user: User
):
    try:
        # Check if token already exists
        stmt = select(DeviceToken).where(
            (DeviceToken.device_token == device_token) &
            (DeviceToken.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        existing_token = result.scalar_one_or_none()
        
        if existing_token:
            existing_token.is_active = True
            existing_token.last_used = datetime.now()
            await db.commit()
            return Message(message="Device token updated successfully")
            
        # Create new token
        new_token = DeviceToken(
            user_id=current_user.id,
            device_token=device_token
        )
        db.add(new_token)
        await db.commit()
        
        return {"message": "Device token registered successfully"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error registering device token: {e}")
        raise HTTPException(status_code=500, detail="Error registering device token")

async def send_notification(
    user_id: str,
    title: str,
    body: str,
    db: AsyncSession
):
    try:
        # Get active device tokens for user
        stmt = select(DeviceToken).where(
            (DeviceToken.user_id == user_id) &
            (DeviceToken.is_active == True)
        )
        result = await db.execute(stmt)
        device_tokens = result.scalars().all()
        
        if not device_tokens:
            return
            
        # Create Apple auth token
        auth_token = create_push_notification_auth_token()
        
        # Send to all user's devices
        for token in device_tokens:
            try:
                await send_push_notification(
                    device_token=token.device_token,
                    title=title,
                    body=body,
                    auth_token=auth_token
                )
            except Exception as e:
                logger.error(f"Error sending notification to token {token.id}: {e}")
                # If token is invalid, mark as inactive
                if "BadDeviceToken" in str(e):
                    token.is_active = False
                    await db.commit()
                    
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail="Error sending notification")

async def send_notification_to_user(
    user_id: str,
    title: str,
    body: str,
    db: AsyncSession
):
    try:
        # Get all active device tokens for the user
        stmt = select(DeviceToken).where(
            (DeviceToken.user_id == user_id) &
            (DeviceToken.is_active == True)
        )
        result = await db.execute(stmt)
        device_tokens = result.scalars().all()
        
        if not device_tokens:
            logger.info(f"No active device tokens found for user {user_id}")
            return  # No active devices to send to
            
        # Create Apple auth token once for all devices
        try:
            auth_token = create_push_notification_auth_token()
        except Exception as e:
            logger.error(f"Failed to create auth token: {e}")
            raise HTTPException(status_code=500, detail="Failed to create notification auth token")
        
        # Send to all user's devices
        for token in device_tokens:
            try:
                await send_push_notification(
                    device_token=token.device_token,
                    title=title,
                    body=body,
                    auth_token=auth_token
                )
                # Update last_used timestamp
                token.last_used = datetime.now()
            except Exception as e:
                logger.error(f"Error sending notification to token {token.id}: {e}")
                # If token is invalid, mark as inactive
                # if "BadDeviceToken" in str(e) or "invalid" in str(e).lower() or "illegal" in str(e).lower():
                #     logger.info(f"Marking device token {token.id} as inactive due to error: {e}")
                #     token.is_active = False
        
        await db.commit()
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error sending notification: {e}")
        # Don't raise an exception here, just log the error
        # This prevents notification errors from breaking the main functionality 