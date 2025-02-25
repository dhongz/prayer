from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Table, func, Enum, Text, Float
)
from sqlalchemy.orm import relationship
import enum
import uuid
from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

# Many-to-Many join table between prayers and prayer walls
prayer_wall_prayers = Table(
    "prayer_wall_prayers",
    Base.metadata,
    Column("prayer_id", String, ForeignKey("prayers.id"), primary_key=True),
    Column("prayer_wall_id", String, ForeignKey("prayer_walls.id"), primary_key=True)
)

# Many-to-Many join table for sharing prayer walls with users (with roles)
prayer_wall_users = Table(
    "prayer_wall_users",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("prayer_wall_id", String, ForeignKey("prayer_walls.id"), primary_key=True),
    Column("role", String, nullable=False)  # e.g., "owner", "member"
)

# Enum for prayer types
class PrayerType(enum.Enum):
    thanksgiving = "thanksgiving"
    worship = "worship"
    request = "request"

# User model
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)  # UUID or OAuth ID
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    provider = Column(String, nullable=False)
    provider_id = Column(String, nullable=False)
    profile_picture = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    prayers = relationship("Prayer", back_populates="user")
    prayer_walls = relationship("PrayerWall", secondary=prayer_wall_users, back_populates="users")
    notifications = relationship("PrayerNotification", back_populates="user")
    reactions = relationship("Reaction", back_populates="user")
    device_tokens = relationship("DeviceToken", back_populates="user")


# Prayer model
class Prayer(Base):
    __tablename__ = "prayers"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)  # UUID
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    transcription = Column(Text, nullable=False)  # Original spoken or typed prayer
    entity = Column(String, nullable=False)         # Extracted by LLM (e.g., "Family", "Job Opportunity")
    synopsis = Column(String, nullable=False)         # Concise summary (5-6 words)
    description = Column(Text, nullable=False)        # Detailed, structured prayer output
    prayer_type = Column(Enum(PrayerType), nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_answered = Column(Boolean, default=False)

    # Many-to-Many relationship: a prayer can be shared on multiple prayer walls
    prayer_walls = relationship("PrayerWall", secondary=prayer_wall_prayers, back_populates="prayers")

    # Relationship with User
    user = relationship("User", back_populates="prayers")
    
    # Reactions on this prayer (if shared on any wall)
    reactions = relationship("Reaction", back_populates="prayer")

    verse_recommendations = relationship("PrayerVerseRecommendation", back_populates="prayer")


# PrayerWall model (private groups for sharing prayers)
class PrayerWall(Base):
    __tablename__ = "prayer_walls"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)  # UUID
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_public = Column(Boolean, default=False)  # Defaults to private
    created_at = Column(DateTime, default=func.now())

    # Relationships: prayers added to the wall and users invited to the wall
    prayers = relationship("Prayer", secondary=prayer_wall_prayers, back_populates="prayer_walls")
    users = relationship("User", secondary=prayer_wall_users, back_populates="prayer_walls")
    owner = relationship("User", backref="owned_prayer_walls")
    
    # Reactions specific to prayers shared on this wall will be stored in the Reaction model

class PrayerVerseRecommendation(Base):
    __tablename__ = "prayer_verse_recommendations"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    prayer_id = Column(String, ForeignKey("prayers.id"), nullable=False)
    
    # Split verse reference into components for better querying
    book_name = Column(String, nullable=False)
    chapter_number = Column(Integer, nullable=False)
    verse_number_start = Column(Integer, nullable=False)
    verse_number_end = Column(Integer, nullable=True)  # For cases where recommendation spans multiple verses
    
    verse_text = Column(Text, nullable=False)
    encouragement = Column(Text, nullable=False)
    relevance_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    prayer = relationship("Prayer", back_populates="verse_recommendations")
    
    @property
    def verse_reference(self):
        """Returns formatted verse reference (e.g., 'Psalm 23:1-6')"""
        if self.verse_number_end and self.verse_number_end != self.verse_number_start:
            return f"{self.book_name} {self.chapter_number}:{self.verse_number_start}-{self.verse_number_end}"
        return f"{self.book_name} {self.chapter_number}:{self.verse_number_start}"

# Reaction model: reactions to a prayer that is shared on a prayer wall.
class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)  # UUID
    prayer_id = Column(String, ForeignKey("prayers.id"), nullable=False)
    prayer_wall_id = Column(String, ForeignKey("prayer_walls.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    emoji = Column(String, nullable=False)  # e.g., "🙏", "❤️", etc.
    created_at = Column(DateTime, default=func.now())

    prayer = relationship("Prayer", back_populates="reactions")
    prayer_wall = relationship("PrayerWall")
    user = relationship("User", back_populates="reactions")


# PrayerNotification model (for reminders and prayer notifications)
class PrayerNotification(Base):
    __tablename__ = "prayer_notifications"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)  # UUID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    prayer_id = Column(String, ForeignKey("prayers.id"), nullable=True)  # Optional: linked to a specific prayer
    scheduled_time = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)

    user = relationship("User", back_populates="notifications")
    prayer = relationship("Prayer")


# PrayerWallInvite model
class PrayerWallInvite(Base):
    __tablename__ = "prayer_wall_invites"

    code = Column(String(36), primary_key=True)
    wall_id = Column(String(36), ForeignKey("prayer_walls.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    
    wall = relationship("PrayerWall")
    creator = relationship("User")

class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    device_token = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_used = Column(DateTime, default=func.now())
    
    # Relationship with User
    user = relationship("User", back_populates="device_tokens")
