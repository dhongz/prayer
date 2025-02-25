import jwt
from datetime import datetime, timedelta, timezone
import httpx
from app.config import config
import uuid
import logging

APPLE_PUSH_URL = "https://api.push.apple.com" # Use api.development.push.apple.com for dev
TEAM_ID = config.APPLE_TEAM_ID
KEY_ID = config.APPLE_KEY_ID
BUNDLE_ID = config.APPLE_BUNDLE_ID
PRIVATE_KEY = config.APPLE_PRIVATE_KEY # Load this from a .p8 file

logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
logging.getLogger("prayer-api").setLevel(logging.INFO)
logger = logging.getLogger("prayer-api")

def create_push_notification_auth_token():
    """Create JWT token for Apple Push Notifications"""
    try:
        # Check if required config values are present
        if not TEAM_ID or not KEY_ID or not PRIVATE_KEY:
            raise ValueError("Missing required Apple Push configuration: TEAM_ID, KEY_ID, or PRIVATE_KEY")
            
        token = jwt.encode(
            {
                'iss': TEAM_ID,
                'iat': datetime.now(timezone.utc),
                'exp': datetime.now(timezone.utc) + timedelta(hours=1)
            },
            PRIVATE_KEY,
            algorithm='ES256',
            headers={
                'kid': KEY_ID
            }
        )
        return token
    except Exception as e:
        raise Exception(f"Failed to create Apple Push auth token: {str(e)}")

async def send_push_notification(
    device_token: str,
    title: str,
    body: str,
    auth_token: str
):
    """Send push notification to Apple Push Notification service"""
    try:
        # Clean device token - remove any spaces or special characters
        # Ensure we have a valid hex string without any UUID formatting
        device_token = device_token.strip().replace(' ', '').replace('-', '').replace('<', '').replace('>', '')
        
        # Validate that the device token is a valid hex string
        # Apple device tokens should be 64 hex characters (32 bytes)
        try:
            int(device_token, 16)
            if len(device_token) != 64:
                logger.warning(f"Device token length is {len(device_token)}, expected 64 characters")
        except ValueError:
            logger.error(f"Invalid device token format: {device_token[:8]}...")
            raise ValueError(f"Device token is not a valid hex string: {device_token[:8]}...")
        
        # Properly formatted headers according to Apple's documentation
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'apns-topic': BUNDLE_ID,
            'apns-push-type': 'alert',
            'apns-priority': '10',
            'Content-Type': 'application/json',
            'apns-id': str(uuid.uuid4()),  # Unique ID for this notification
            'apns-expiration': '0'  # 0 means the notification is only sent once
        }
        
        payload = {
            'aps': {
                'alert': {
                    'title': title,
                    'body': body
                },
                'sound': 'default',
                'badge': 1
            }
        }
        
        # Construct URL with properly formatted device token
        url = f"{APPLE_PUSH_URL}/3/device/{device_token}"
        
        # Log request details for debugging
        logger.debug(f"Sending push notification to: {url}")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Payload: {payload}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Successfully sent notification to device: {device_token[:8]}...")
                return response
            else:
                error_msg = f"Push notification failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    except httpx.RequestError as e:
        logger.error(f"Request error for device {device_token[:8] if len(device_token) >= 8 else device_token}...: {str(e)}")
        raise Exception(f"Request error: {str(e)}")
    except Exception as e:
        logger.error(f"Push notification error for device {device_token[:8] if len(device_token) >= 8 else device_token}...: {str(e)}")
        raise Exception(f"Push notification error: {str(e)}") 