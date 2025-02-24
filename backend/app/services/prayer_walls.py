import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from typing import List
import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
import secrets

from app.models import (PrayerWall, 
                        User, 
                        Prayer, 
                        PrayerWallInvite, 
                        prayer_wall_users, 
                        prayer_wall_prayers)

from app.schemas.prayer_walls import (PrayerWallCreate, 
                                     PrayerWallUpdate, 
                                     PrayerWallResponse,
                                     WallUser,
                                     PrayerWallsResponse)


logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
logging.getLogger("prayer-api").setLevel(logging.INFO)
logger = logging.getLogger("prayer-api")



async def process_create_prayer_wall(prayer_wall: PrayerWallCreate, db: AsyncSession, current_user: User):
    try:
        # Create the prayer wall
        new_wall = PrayerWall(
            id=str(uuid.uuid4()),
            title=prayer_wall.title,   
            description=prayer_wall.description,
            is_public=prayer_wall.is_public,
            owner_id=current_user.id
        )
        db.add(new_wall)
        await db.flush()  # Flush to get the wall ID
        
        # Add creator as owner in prayer_wall_users table
        stmt = prayer_wall_users.insert().values(
            user_id=current_user.id,
            prayer_wall_id=new_wall.id,
            role='owner'
        )
        await db.execute(stmt)
        
        await db.commit()
        
        # Return wall response
        return PrayerWallResponse(
            id=new_wall.id,
            title=new_wall.title,
            description=new_wall.description,
            is_public=new_wall.is_public,
            created_at=new_wall.created_at,
            owner_id=new_wall.owner_id,
            users=[WallUser(
                id=f"{new_wall.id}_{current_user.id}",
                user_id=current_user.id,
                role="owner"
            )]
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating prayer wall: {e}")
        raise HTTPException(status_code=500, detail="Error creating prayer wall")
    
async def process_get_prayer_walls(db: AsyncSession, current_user: User):
    try:
        # Get walls with roles and users
        stmt = select(
            PrayerWall,
            prayer_wall_users.c.role
        ).outerjoin(
            prayer_wall_users,
            (prayer_wall_users.c.prayer_wall_id == PrayerWall.id) &
            (prayer_wall_users.c.user_id == current_user.id)
        ).where(
            (PrayerWall.owner_id == current_user.id) |  # Walls they own
            (PrayerWall.id.in_(  # Walls they're a member of
                select(prayer_wall_users.c.prayer_wall_id)
                .where(prayer_wall_users.c.user_id == current_user.id)
            ))
        )
        
        result = await db.execute(stmt)
        prayer_walls = []
        
        for wall, role in result:
            # Get users for this wall
            users_stmt = select(User, prayer_wall_users.c.role).join(
                prayer_wall_users,
                (prayer_wall_users.c.user_id == User.id) &
                (prayer_wall_users.c.prayer_wall_id == wall.id)
            )
            users_result = await db.execute(users_stmt)
            wall_users = []
            
            for user, user_role in users_result:
                wall_users.append(WallUser(
                    id=f"{wall.id}_{user.id}",
                    user_id=user.id,
                    role="owner" if user.id == wall.owner_id else user_role
                ))
            
            wall_response = PrayerWallResponse(
                id=wall.id,
                title=wall.title,
                description=wall.description,
                is_public=wall.is_public,
                created_at=wall.created_at,
                owner_id=wall.owner_id,
                users=wall_users
            )
            prayer_walls.append(wall_response)
        print(prayer_walls)
        return PrayerWallsResponse(prayer_walls=prayer_walls)
        
    except Exception as e:
        logger.error(f"Error getting prayer walls: {e}")
        raise HTTPException(status_code=500, detail="Error getting prayer walls")
    
async def process_update_prayer_wall(prayer_wall: PrayerWallUpdate, db: AsyncSession, current_user: User):
    try:
        stmt = select(PrayerWall).where(PrayerWall.id == prayer_wall.id)
        result = await db.execute(stmt)
        prayer_wall = result.scalar_one_or_none()
        if not prayer_wall:
            raise HTTPException(status_code=404, detail="Prayer wall not found")    
        prayer_wall.title = prayer_wall.title
        prayer_wall.description = prayer_wall.description
        prayer_wall.is_public = prayer_wall.is_public
        await db.commit()
        return prayer_wall
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating prayer wall: {e}")
        raise HTTPException(status_code=500, detail="Error updating prayer wall")
    
async def process_delete_prayer_wall(prayer_wall_id: str, db: AsyncSession, current_user: User):
    try:
        # First verify the wall exists and user has permission
        stmt = select(PrayerWall).where(PrayerWall.id == prayer_wall_id)
        result = await db.execute(stmt)
        wall = result.scalar_one_or_none()
        
        if not wall:
            raise HTTPException(status_code=404, detail="Prayer wall not found")
            
        if wall.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this wall")
        
        # Delete all prayer wall associations
        await db.execute(
            delete(prayer_wall_prayers).where(
                prayer_wall_prayers.c.prayer_wall_id == prayer_wall_id
            )
        )
        
        # Delete all user associations
        await db.execute(
            delete(prayer_wall_users).where(
                prayer_wall_users.c.prayer_wall_id == prayer_wall_id
            )
        )
        
        # Delete any invites for this wall
        await db.execute(
            delete(PrayerWallInvite).where(
                PrayerWallInvite.wall_id == prayer_wall_id
            )
        )
        
        # Finally delete the wall itself
        await db.delete(wall)
        await db.commit()
        
        return {"message": "Prayer wall deleted successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting prayer wall: {e}")
        raise HTTPException(status_code=500, detail="Error deleting prayer wall")

async def process_get_wall_prayers(
    wall_id: str,
    db: AsyncSession,
    current_user: User
):
    try:
        # Get the prayer wall and verify user access in one query
        access_stmt = select(PrayerWall).join(
            prayer_wall_users,
            (prayer_wall_users.c.prayer_wall_id == PrayerWall.id) &
            (prayer_wall_users.c.user_id == current_user.id)
        ).where(PrayerWall.id == wall_id)
        
        result = await db.execute(access_stmt)
        wall = result.scalar_one_or_none()
        print(wall)
        
        if not wall:
            raise HTTPException(status_code=404, detail="Prayer wall not found or not authorized")
            
        # Get prayers for this wall
        prayers_stmt = select(Prayer).join(
            prayer_wall_prayers,
            (prayer_wall_prayers.c.prayer_id == Prayer.id) &
            (prayer_wall_prayers.c.prayer_wall_id == wall_id)
        )
        
        result = await db.execute(prayers_stmt)
        prayers = result.scalars().all()
        
        return prayers
        
    except Exception as e:
        logger.error(f"Error getting wall prayers: {e}")
        raise HTTPException(status_code=500, detail="Error getting wall prayers")

async def process_add_prayers_to_wall(
    wall_id: str,
    prayer_ids: List[str],
    db: AsyncSession,
    current_user: User
):
    try:
        # Get the prayer wall
        result = await db.execute(select(PrayerWall).where(PrayerWall.id == wall_id))
        wall = result.scalar_one_or_none()
        
        if not wall:
            raise HTTPException(status_code=404, detail="Prayer wall not found")
            
        # Verify user has access to wall
        if wall.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to add prayers to this wall")
            
        # Get the prayers
        result = await db.execute(select(Prayer).where(Prayer.id.in_(prayer_ids)))
        prayers = result.scalars().all()
        
        # Verify prayer ownership
        for prayer in prayers:
            if prayer.user_id != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail=f"Not authorized to add prayer {prayer.id} to wall"
                )
        
        # Add prayers to wall
        wall.prayers.extend(prayers)
        await db.commit()
        
        return {"message": "Prayers added to wall successfully"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding prayers to wall: {e}")
        raise HTTPException(status_code=500, detail="Error adding prayers to wall")

async def process_remove_prayer_from_wall(
    wall_id: str,
    prayer_id: str,
    db: AsyncSession,
    current_user: User
):
    try:
        # Get the prayer wall and verify user access
        access_stmt = select(PrayerWall).join(
            prayer_wall_users,
            (prayer_wall_users.c.prayer_wall_id == PrayerWall.id) &
            (prayer_wall_users.c.user_id == current_user.id)
        ).where(PrayerWall.id == wall_id)
        
        result = await db.execute(access_stmt)
        wall = result.scalar_one_or_none()
        
        if not wall:
            raise HTTPException(status_code=404, detail="Prayer wall not found or not authorized")
            
        # Delete the association in prayer_wall_prayers
        stmt = delete(prayer_wall_prayers).where(
            (prayer_wall_prayers.c.prayer_wall_id == wall_id) &
            (prayer_wall_prayers.c.prayer_id == prayer_id)
        )
        await db.execute(stmt)
        await db.commit()
        
        return {"message": "Prayer removed from wall successfully"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error removing prayer from wall: {e}")
        raise HTTPException(status_code=500, detail="Error removing prayer from wall")

async def process_generate_invite_link(
    wall_id: str,
    db: AsyncSession,
    current_user: User
):
    try:
        # Get the prayer wall
        result = await db.execute(select(PrayerWall).where(PrayerWall.id == wall_id))
        wall = result.scalar_one_or_none()
        
        if not wall:
            raise HTTPException(status_code=404, detail="Prayer wall not found")
            
        # Verify user is owner or has share permissions
        if wall.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to generate invite")
        
        # Generate unique invite code
        invite_code = secrets.token_urlsafe(16)
        
        # Store invite in database (you'll need to create an Invite model)
        invite = PrayerWallInvite(
            code=invite_code,
            wall_id=wall_id,
            created_by=current_user.id,
            expires_at=datetime.now() + timedelta(days=7)  # Optional: expire after 7 days
        )
        db.add(invite)
        await db.commit()
        
        # Return shareable link info
        return {
            "invite_code": invite_code,
            "wall_title": wall.title,
            "expires_at": invite.expires_at
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error generating invite: {e}")
        raise HTTPException(status_code=500, detail="Error generating invite")

async def process_get_wall_invite(
    invite_code: str,
    db: AsyncSession,
    current_user: User
):
    try:
        # Get invite details
        result = await db.execute(
            select(PrayerWallInvite, PrayerWall)
            .join(PrayerWall)
            .where(PrayerWallInvite.code == invite_code)
        )
        invite, wall = result.one_or_none()
        
        if not invite or not wall:
            raise HTTPException(status_code=404, detail="Invalid invite link")
            
        if invite.expires_at and invite.expires_at < datetime.now():
            raise HTTPException(status_code=400, detail="Invite link has expired")
            
        # Return wall preview info
        return {
            "wall_title": wall.title,
            "description": wall.description,
            "owner_name": wall.owner.name,  # Assuming you have this relationship
            "member_count": len(wall.users)
        }
        
    except Exception as e:
        logger.error(f"Error getting invite: {e}")
        raise HTTPException(status_code=500, detail="Error getting invite details")

async def process_join_wall_with_invite(
    invite_code: str,
    db: AsyncSession,
    current_user: User
):
    try:
        # Get invite and wall
        result = await db.execute(
            select(PrayerWallInvite, PrayerWall)
            .join(PrayerWall)
            .where(PrayerWallInvite.code == invite_code)
        )
        invite, wall = result.one_or_none()
        
        if not invite or not wall:
            raise HTTPException(status_code=404, detail="Invalid invite link")
            
        if invite.expires_at and invite.expires_at < datetime.now():
            raise HTTPException(status_code=400, detail="Invite link has expired")
            
        # Check if user is already a member using async query
        membership_check = await db.execute(
            select(prayer_wall_users).where(
                (prayer_wall_users.c.prayer_wall_id == wall.id) &
                (prayer_wall_users.c.user_id == current_user.id)
            )
        )
        if membership_check.first():
            return {"message": "Already a member of this prayer wall"}
            
        # Add user as member
        stmt = prayer_wall_users.insert().values(
            user_id=current_user.id,
            prayer_wall_id=wall.id,
            role='member'
        )
        await db.execute(stmt)
        await db.commit()
        
        return {
            "message": "Joined prayer wall successfully"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error joining wall: {e}")
        raise HTTPException(status_code=500, detail="Error joining wall")