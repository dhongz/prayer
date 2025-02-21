import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from typing import List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder 

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import config
from app.models import Prayer, User

from app.config.llm import oai_llm
from app.schemas.prayers import (PrayerText, 
                                 ParsedPrayer, 
                                 PrayerCreate, 
                                 PrayerUpdate, 
                                 PrayerDelete,
                                 PrayerResponse)

from app.schemas.llm import Prayer as LLMPrayer, PrayerList as LLMPrayerList
from .prompts import PRAYER_PARSE_SYSTEM_PROMPT

logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
logging.getLogger("prayer-api").setLevel(logging.INFO)
logger = logging.getLogger("prayer-api")



async def process_create_prayer(prayer: Prayer, db: AsyncSession, current_user: User):
    try:
        print(f"Creating prayer: {prayer}")
        prayer = Prayer(prayer=prayer)
        db.add(prayer)
        await db.flush()
        return prayer
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Error creating user")
    

async def process_get_prayers(db: AsyncSession, current_user: User):
    try:
        print(f"Getting prayers: {current_user}")
        result = await db.execute(select(Prayer).where(Prayer.user_id == current_user.id))
        prayers = result.scalars().all()
        prayers_list = []
        for prayer in prayers:
            prayer_response = PrayerResponse(id=prayer.id,
                            transcription=prayer.transcription,
                            entity=prayer.entity,
                            synopsis=prayer.synopsis,
                            description=prayer.description,
                            prayer_type=prayer.prayer_type,
                            is_answered=prayer.is_answered,
                            created_at=prayer.created_at)
            prayers_list.append(prayer_response)
        print(prayers_list)
        return prayers_list
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Error creating user")


async def process_update_prayer(prayer: Prayer, db: AsyncSession, current_user: User):
    try:
        print(f"Creating prayer: {prayer}")
        prayer = Prayer(prayer=prayer)
        db.add(prayer)
        await db.flush()
        return prayer
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Error creating user")


async def process_delete_prayer(prayer: Prayer, db: AsyncSession, current_user: User):
    try:
        print(f"Creating prayer: {prayer}")
        prayer = Prayer(prayer=prayer)
        db.add(prayer)
        await db.flush()
        return prayer
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Error creating user")



async def process_text_prayers(prayer: PrayerText):
    try:
        prayer_text = prayer.text
        structured_prayer_llm = oai_llm.with_structured_output(LLMPrayerList)
        user_message = HumanMessage(content=f"Parse this prayer: {prayer_text}")
        messages = [SystemMessage(content=PRAYER_PARSE_SYSTEM_PROMPT)] + [user_message]
        response = structured_prayer_llm.invoke(messages)
        
        prayers = response.prayers
        print(f"Prayers: {prayers}")
        prayers_list = []
        for prayer in prayers:
            parsed_prayer = ParsedPrayer(id=uuid.uuid4(),
                          transcription=prayer_text,
                          entity=prayer.entity,
                          synopsis=prayer.synopsis,
                          description=prayer.description,
                          prayer_type=prayer.prayer_type)
            prayers_list.append(parsed_prayer)

        print("JSON response:", jsonable_encoder(prayers_list))
        return prayers_list
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Error creating user")


async def process_bulk_create_prayer(prayers: List[ParsedPrayer], db: AsyncSession, current_user: User):
    try:
        prayers_list = []
        for prayer in prayers:
            prayer = Prayer(
                id=str(prayer.id),
                user_id=current_user.id,
                transcription=prayer.transcription,
                entity=prayer.entity,
                synopsis=prayer.synopsis,
                description=prayer.description,
                prayer_type=prayer.prayer_type)
            prayers_list.append(prayer)
        db.add_all(prayers_list)
        await db.commit()
        return {"message": "Prayers created successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error bulk creating prayers: {e}")
        raise HTTPException(status_code=500, detail="Error bulk creating prayers")