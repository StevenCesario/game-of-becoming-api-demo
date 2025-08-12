from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship # To define relationships between models
from datetime import datetime, timezone
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hrga = Column(Text, nullable=False) # Highest Revenue Generated Activity. Unlimited text field - let users be as comprehensive as they wish
    default_focus_block_duration = Column(Integer, default=50, nullable=False) # In minutes
    registered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    daily_intentions = relationship("DailyIntention", back_populates="user")
    ai_coaching_logs = relationship("AICoachingLog", back_populates="user")
    auth = relationship("UserAuth", back_populates="user", uselist=False) # One-to-one relationship with UserAuth
    character_stats = relationship("CharacterStats", back_populates="user", uselist=False) # One-to-one relationship with CharacterStats

class UserAuth(Base):
    __tablename__ = "user_auth"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = Column(DateTime, nullable=True) # For analytics, nullable if user has never logged in

    # Relationships
    user = relationship("User", back_populates="auth")

class CharacterStats(Base):
    __tablename__ = "character_stats"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    xp = Column(Integer, default=0, nullable=False) # We only store the total XP, level is calculated
    resilience = Column(Integer, default=0, nullable=False)
    clarity = Column(Integer, default=0, nullable=False)
    discipline = Column(Integer, default=0, nullable=False)
    commitment = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="character_stats")

class DailyIntention(Base):
    __tablename__ = "daily_intentions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Core execution tracking
    daily_intention_text = Column(Text, nullable=False)
    target_quantity = Column(Integer, nullable=False)
    completed_quantity = Column(Integer, default=0, nullable=False) # Default to 0, updated as user completes tasks
    status = Column(String(20), default='pending', nullable=False) # 'pending', 'in_progress', 'completed', 'failed'
    focus_block_count = Column(Integer, nullable=False)
    
    # AI Coaching (keeping for V2)
    ai_feedback = Column(Text, nullable=True) # Null if Claude API is to fail. Will be given using async retry if this was to be the case
    user_response_to_ai_feedback = Column(Text, nullable=True)
    user_agreed_with_ai = Column(Boolean, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True) # Index for quick retrieval of daily intentions

    # Relationships
    user = relationship("User", back_populates="daily_intentions")
    daily_results = relationship("DailyResult", back_populates="daily_intention", uselist=False) # One-to-one relationship with DailyResult
    focus_blocks = relationship("FocusBlock", back_populates="daily_intention") #For individual focus block tracking

class FocusBlock(Base):
    __tablename__ = "focus_blocks"

    id = Column(Integer, primary_key=True)
    # Foreign Key to link back to the main goal
    daily_intention_id = Column(Integer, ForeignKey("daily_intentions.id"), nullable=False)

    duration_minutes = Column(Integer, default=50, nullable=False) # Defaults to 50
    focus_block_intention = Column(Text, nullable=False)

    # The URLs from Neeto/Loom
    pre_block_video_url = Column(String(2048), nullable=True)
    post_block_video_url = Column(String(2048), nullable=True)

    status = Column(String(20), default='pending', nullable=False) # e.g., 'pending', 'completed'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Establishes the link in SQLAlchemy
    daily_intention = relationship("DailyIntention", back_populates="focus_blocks")

class DailyResult(Base):
    __tablename__ = "daily_results"

    id = Column(Integer, primary_key=True, index=True)
    daily_intention_id = Column(Integer, ForeignKey("daily_intentions.id"), nullable=False)
    succeeded_failed = Column(Boolean, nullable=False)
    ai_feedback = Column(Text, nullable=True)
    user_confirmation_correction = Column(Boolean, nullable=True) # User can confirm or correct AI feedback. True is confirmation, False is correction
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Recovery Quest fields - Action Quests will be added in V2!
    recovery_quest = Column(Text, nullable=True) # Null if user succeeded in their Daily Intention
    recovery_quest_type = Column(String(20), default='reflection', nullable=False) # 'reflection' or 'action'
    recovery_quest_response = Column(Text, nullable=True) # Users's response/proof. Null if no Recovery Quest was given
    recovery_quest_completed = Column(Boolean, default=False, nullable=False) # V2 feature

    # Relationships
    daily_intention = relationship("DailyIntention", back_populates="daily_results")

class AICoachingLog(Base):
    __tablename__ = "ai_coaching_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_text = Column(Text, nullable=False) # What someone submitted/said
    ai_feedback = Column(Text, nullable=False) # AI's coaching response
    coaching_trigger = Column(String(50), nullable=False) # Trigger for the AI coaching, e.g. 'daily_intention', 'evening_assessment', 'recovery_quest' etc. String now, Enum in V2
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="ai_coaching_logs")
