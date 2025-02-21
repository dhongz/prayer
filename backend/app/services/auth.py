import httpx
import jwt
import logging
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.config import config
from app.schemas.auth import AppleToken, AccessToken
from app.models import User
from app.db.database import get_db

logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
logging.getLogger("prayer-api").setLevel(logging.INFO)
logger = logging.getLogger("prayer-api")



APPLE_PUBLIC_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_AUDIENCE = "dhongz.Prayer" 


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    # Expect the token to always come via the Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    # Extract the token from the header
    token = auth_header[len("Bearer "):].strip()
    
    try:
        # Decode the token using the secret key and specify the algorithm
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token payload missing subject")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Retrieve the user based on the email contained in the token's payload
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def generate_access_token(user_id: str)-> AccessToken:
    try:
        print(f"Generating access token for user_id: {user_id}")
        payload = {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
            "iat": datetime.now(timezone.utc)
        }
        access_token = jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")
        print(f"Access token generated: {access_token}")
        return AccessToken(access_token=access_token)
    except Exception as e:
        logger.error(f"Error generating JWT: {e}")
        raise HTTPException(status_code=500, detail="Error generating JWT")
    


async def create_user(provider_id: str, email: str, db: AsyncSession):
    try:
        print(f"Creating user with provider_id: {provider_id}, email: {email}")
        user = User(provider_id=provider_id, email=email, provider="apple")
        db.add(user)
        await db.flush()
        return user
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Error creating user")






async def get_apple_public_keys():
    async with httpx.AsyncClient() as client:
        response = await client.get(APPLE_PUBLIC_KEYS_URL)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Could not fetch Apple public keys")
        return response.json()["keys"]

async def verify_apple_token(identity_token: str):
    try:
        apple_keys = await get_apple_public_keys()

        # Extract the JWT header to determine which Apple key was used
        headers = jwt.get_unverified_header(identity_token)

        key_id = headers["kid"]

        # Find the correct Apple public key
        key = next((key for key in apple_keys if key["kid"] == key_id), None)
        if not key:
            raise HTTPException(status_code=400, detail="Invalid Apple public key")

        # Construct the public key
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        try:
            # ✅ Decode and verify the JWT
            decoded_token = jwt.decode(
                identity_token,
                public_key,
                algorithms=["RS256"],
                audience=APPLE_AUDIENCE,  # Must match your app's bundle ID
                issuer="https://appleid.apple.com"
            )

            return decoded_token
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Apple token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid Apple token")
    except Exception as e:
        logger.error(f"Error verifying Apple token: {e}")
        raise HTTPException(status_code=500, detail="Error verifying Apple token")

async def apple_authentication(apple_token: AppleToken, db: AsyncSession) -> AccessToken:
    """
    Authenticate a user using Apple ID.

    This function verifies the ID token using Apple's authentication service and returns
    user information if the token is valid.
    """
    try:
        print(apple_token)
        # Step 1: Verify Apple Token
        apple_data = await verify_apple_token(apple_token.apple_token)
        # Step 2: Extract Apple User ID
        apple_user_id = apple_data.get("sub")
        email = apple_data.get("email")

        if not apple_user_id:
            raise HTTPException(status_code=400, detail="Invalid Apple ID Token")
        print(f"Checking if user exists with provider_id: {apple_user_id}")
        stmt = select(User).filter(User.provider_id == apple_user_id)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            print(f"User does not exist, creating user with provider_id: {apple_user_id}")
            user = await create_user(apple_user_id, email, db)
        else:
            print(f"User exists, fetching user with provider_id: {apple_user_id}")
            user = existing_user
        print(f"Generating access token for user_id: {user.id}")
        access_token = generate_access_token(user.id)
        print(f"Access token generated: {access_token}")
        await db.commit()
        return access_token
    except Exception as e:
        await db.rollback()
        logger.error(f"Error authenticating user: {e}")
        raise HTTPException(status_code=500, detail="Error authenticating user")
