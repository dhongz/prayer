from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Table, func, Enum, Text
)
from sqlalchemy.orm import relationship, DeclarativeBase
import enum
import uuid


class Base(DeclarativeBase):
    pass

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
    provider = Column(String, nullable=False)  # e.g., "apple", "google", "email"
    profile_picture = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    prayers = relationship("Prayer", back_populates="user")
    prayer_walls = relationship("PrayerWall", secondary=prayer_wall_users, back_populates="users")
    notifications = relationship("PrayerNotification", back_populates="user")
    reactions = relationship("Reaction", back_populates="user")


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
