import logging
from datetime import datetime, timedelta, timezone
from typing import List
import uuid
import tempfile
import os

from fastapi import HTTPException, UploadFile, File
from fastapi.encoders import jsonable_encoder 

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.messages import HumanMessage, SystemMessage

from app.models import Prayer, User, PrayerWall, prayer_wall_users, prayer_wall_prayers, PrayerVerseRecommendation
from app.config.llm import oai_llm
from app.schemas.prayers import (PrayerText, 
                                 ParsedPrayer, 
                                 PrayerCreate, 
                                 PrayerUpdate, 
                                 PrayerDelete,
                                 PrayerResponse,
                                 PrayerWallsResponse)
from app.schemas.llm import Prayer as LLMPrayer, PrayerList as LLMPrayerList
from app.schemas.prayer_walls import PrayerWallResponse
from app.services.stt import transcribe_audio

from .prompts import PRAYER_PARSE_SYSTEM_PROMPT
from .verse_recommendations import generate_verse_recommendations

logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
logging.getLogger("prayer-api").setLevel(logging.INFO)
logger = logging.getLogger("prayer-api")



async def process_create_prayer(prayer: Prayer, db: AsyncSession, current_user: User):
    try:
        print(f"Creating prayer: {prayer}")
        prayer = Prayer(prayer=prayer)
        db.add(prayer)
        await db.flush()  # Get the ID without committing
        
        # Generate verse recommendations
        await generate_verse_recommendations(prayer, db)
        
        return prayer
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating prayer: {e}")
        raise HTTPException(status_code=500, detail="Error creating prayer")
    

async def process_get_prayers(db: AsyncSession, current_user: User):
    try:
        print(f"Getting prayers: {current_user}")
        result = await db.execute(
            select(Prayer)
            .where(Prayer.user_id == current_user.id)
            .options(selectinload(Prayer.verse_recommendations))
        )
        prayers = result.scalars().all()
        prayers_list = []
        for prayer in prayers:
            prayer_response = PrayerResponse(
                id=prayer.id,
                transcription=prayer.transcription,
                entity=prayer.entity,
                synopsis=prayer.synopsis,
                description=prayer.description,
                prayer_type=prayer.prayer_type,
                is_answered=prayer.is_answered,
                created_at=prayer.created_at,
                verse_recommendations=prayer.verse_recommendations
            )
            prayers_list.append(prayer_response)
        return prayers_list
    except Exception as e:
        await db.rollback()
        logger.error(f"Error getting prayers: {e}")
        raise HTTPException(status_code=500, detail="Error getting prayers")


async def process_update_prayer(prayer: Prayer, db: AsyncSession, current_user: User):
    try:
        print(f"Creating prayer: {prayer}")
        prayer = Prayer(prayer=prayer)
        db.add(prayer)
        await db.flush()
        return prayer
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating prayer: {e}")
        raise HTTPException(status_code=500, detail="Error updating prayer")


async def process_delete_prayer(prayer_id: str, db: AsyncSession):
    try:
        # First delete any associations in prayer_wall_prayers
        stmt = delete(prayer_wall_prayers).where(prayer_wall_prayers.c.prayer_id == prayer_id)
        await db.execute(stmt)
        
        # Delete associated verse recommendations
        stmt = delete(PrayerVerseRecommendation).where(PrayerVerseRecommendation.prayer_id == prayer_id)
        await db.execute(stmt)
        
        # Then delete the prayer itself
        stmt = delete(Prayer).where(Prayer.id == prayer_id)
        await db.execute(stmt)
        
        await db.commit()
        return {"message": "Prayer deleted successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting prayer: {e}")
        raise HTTPException(status_code=500, detail="Error deleting prayer")



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
            parsed_prayer = ParsedPrayer(id=str(uuid.uuid4()),
                          transcription=prayer_text,
                          entity=prayer.entity,
                          synopsis=prayer.synopsis,
                          description=prayer.description,
                          prayer_type=prayer.prayer_type)
            prayers_list.append(parsed_prayer)

        print("JSON response:", jsonable_encoder(prayers_list))
        return prayers_list
    except Exception as e:
        logger.error(f"Error parsing prayers: {e}")
        raise HTTPException(status_code=500, detail="Error parsing prayers")

# @router.post("/process-audio", response_model=List[ParsedPrayer])
# async def process_audio(
#     audio: UploadFile = File(...),
#     current_user: User = Depends(get_current_user)
# ):
#    

async def process_audio_prayers(prayer_audio: UploadFile = File(...)):
    """
    Process an audio prayer recording and return parsed prayers.
    The audio is received as a file upload and processed transiently.
    """
    if not prayer_audio.filename.lower().endswith(('.m4a', '.mp3', '.wav')):
        raise HTTPException(status_code=400, detail="File must be an audio file (M4A, MP3, or WAV)")
    
    # Create a temporary file with the same extension as the upload
    file_extension = os.path.splitext(prayer_audio.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        try:
            # Write uploaded file to temporary file
            contents = await prayer_audio.read()
            temp_file.write(contents)
            temp_file.flush()
            
            # Get transcription
            prayer_text = await transcribe_audio(temp_file.name)
            
            # Process the transcribed text into prayers
            parsed_prayers = await process_text_prayers(prayer_text)
            
            return parsed_prayers
            
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
        finally:
            # Always clean up the temporary file
            os.unlink(temp_file.name)

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
        print(f"Prayers list: {prayers_list}")
        db.add_all(prayers_list)
        await db.flush()  # Commit the prayers first
        
        # Generate recommendations for each prayer
        for prayer in prayers_list:
            verse_recommendations = await generate_verse_recommendations(prayer)
            print(f"Verse recommendations: {verse_recommendations}")
            db.add_all(verse_recommendations)

        await db.commit()
        
        return {"message": "Prayers created successfully", "count": len(prayers_list)}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error bulk creating prayers: {e}")
        raise HTTPException(status_code=500, detail="Error bulk creating prayers")


async def process_share_prayer_to_walls(
    prayer_id: str,
    wall_ids: List[str],
    db: AsyncSession,
    current_user: User
):
    try:
        # Get the prayer
        result = await db.execute(select(Prayer).where(Prayer.id == prayer_id))
        prayer = result.scalar_one_or_none()
        
        if not prayer:
            raise HTTPException(status_code=404, detail="Prayer not found")
            
        # Verify prayer ownership
        if prayer.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to share this prayer")
            
        # Get the prayer walls with access check
        result = await db.execute(
            select(PrayerWall).join(
                prayer_wall_users,
                (prayer_wall_users.c.prayer_wall_id == PrayerWall.id) &
                (prayer_wall_users.c.user_id == current_user.id)
            ).where(PrayerWall.id.in_(wall_ids))
        )
        walls = result.scalars().all()
        
        if len(walls) != len(wall_ids):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access one or more prayer walls"
            )
        
        # Add prayer to walls using the association table
        for wall in walls:
            stmt = prayer_wall_prayers.insert().values(
                prayer_id=prayer_id,
                prayer_wall_id=wall.id
            )
            await db.execute(stmt)
            
        await db.commit()
        
        return {"message": "Prayer shared successfully"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error sharing prayer to walls: {e}")
        raise HTTPException(status_code=500, detail="Error sharing prayer")

async def process_remove_prayer_from_wall(
    prayer_id: str,
    wall_id: str,
    db: AsyncSession,
    current_user: User
):
    try:
        # Get the prayer and wall
        result = await db.execute(select(Prayer).where(Prayer.id == prayer_id))
        prayer = result.scalar_one_or_none()
        
        result = await db.execute(select(PrayerWall).where(PrayerWall.id == wall_id))
        wall = result.scalar_one_or_none()
        
        if not prayer or not wall:
            raise HTTPException(status_code=404, detail="Prayer or wall not found")
            
        # Verify ownership/access
        if prayer.user_id != current_user.id and wall.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to remove this prayer")
            
        # Remove prayer from wall using the association table
        stmt = delete(prayer_wall_prayers).where(
            (prayer_wall_prayers.c.prayer_id == prayer_id) &
            (prayer_wall_prayers.c.prayer_wall_id == wall_id)
        )
        await db.execute(stmt)
        await db.commit()
        
        return {"message": "Prayer removed from wall successfully"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error removing prayer from wall: {e}")
        raise HTTPException(status_code=500, detail="Error removing prayer from wall")

async def process_get_prayer_walls(
    prayer_id: str,
    db: AsyncSession,
    current_user: User
):
    try:
        # Get the prayer
        result = await db.execute(select(Prayer).where(Prayer.id == prayer_id))
        prayer = result.scalar_one_or_none()
        
        if not prayer:
            raise HTTPException(status_code=404, detail="Prayer not found")
            
        # Verify prayer ownership
        if prayer.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this prayer's walls")
            
        # Get walls with roles
        stmt = select(
            PrayerWall,
            prayer_wall_users.c.role
        ).join(
            prayer_wall_prayers,
            prayer_wall_prayers.c.prayer_wall_id == PrayerWall.id
        ).outerjoin(
            prayer_wall_users,
            (prayer_wall_users.c.prayer_wall_id == PrayerWall.id) &
            (prayer_wall_users.c.user_id == current_user.id)
        ).where(
            prayer_wall_prayers.c.prayer_id == prayer_id
        )
        
        result = await db.execute(stmt)
        prayer_walls = []
        
        for wall, role in result:
            wall_response = PrayerWallResponse(
                id=wall.id,
                title=wall.title,
                description=wall.description,
                is_public=wall.is_public,
                created_at=wall.created_at,
                owner_id=wall.owner_id,
                role="owner" if wall.owner_id == current_user.id else role
            )
            prayer_walls.append(wall_response)
            
        return PrayerWallsResponse(prayer_walls=prayer_walls)
        
    except Exception as e:
        logger.error(f"Error getting prayer walls: {e}")
        raise HTTPException(status_code=500, detail="Error getting prayer walls")