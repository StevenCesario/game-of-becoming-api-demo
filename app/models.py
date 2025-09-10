from __future__ import annotations # Keep ForwardRef happy with annotation-handling
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy import (
    String, 
    Text, 
    ForeignKey
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)

# Define a new Base class using DeclarativeBase
class Base(DeclarativeBase):
    pass

# Let each model inherit from the new Base and use Mapped/mapped_column
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100)) # Nullable is False by default
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hla: Mapped[Optional[str]] = mapped_column(Text) # Highest Leverage Activity. Unlimited text field - let users be as comprehensive as they wish
    default_focus_block_duration: Mapped[int] = mapped_column(default=50) # In minutes
    registered_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # --- NEW: Onboarding fields ---
    vision: Mapped[Optional[str]] = mapped_column(Text) # The North Star
    milestone: Mapped[Optional[str]] = mapped_column(Text) # The 90-day milestone
    constraint: Mapped[Optional[str]] = mapped_column(Text) # The "Boss" obstacle

    # --- Streak-related fields --- 
    current_streak: Mapped[int] = mapped_column(default=0, server_default='0', nullable=False)
    longest_streak: Mapped[int] = mapped_column(default=0, server_default='0', nullable=False)
    last_streak_update: Mapped[Optional[datetime]] = mapped_column()

    # Relationships
    daily_intentions: Mapped[List["DailyIntention"]] = relationship(back_populates="user")
    ai_coaching_logs: Mapped[List["AICoachingLog"]] = relationship(back_populates="user")
    auth: Mapped["UserAuth"] = relationship(back_populates="user") # One-to-one relationship with UserAuth. uselist=False is infered from the non-List Mapped type
    character_stats: Mapped["CharacterStats"] = relationship(back_populates="user") # Same here for one-to-one relationship with CharacterStats

class UserAuth(Base):
    __tablename__ = "user_auth"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    last_login: Mapped[Optional[datetime]] = mapped_column() # For analytics, nullable if user has never logged in

    # Relationship back to User
    user: Mapped["User"] = relationship(back_populates="auth")

class CharacterStats(Base):
    __tablename__ = "character_stats"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    xp: Mapped[int] = mapped_column(default=0) # We only store the total XP, level is calculated. Gained by executing Focus Blocks
    clarity: Mapped[int] = mapped_column(default=0) # Gained from setting Daily Intentions
    discipline: Mapped[int] = mapped_column(default=0) # Gained from completing Daily Intentions
    resilience: Mapped[int] = mapped_column(default=0) # Gained from completing Recovery Quests after failing Daily Intentions
    commitment: Mapped[int] = mapped_column(default=0) # Gained from hitting a Milestone

    user: Mapped["User"] = relationship(back_populates="character_stats")

class DailyIntention(Base):
    __tablename__ = "daily_intentions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Core execution tracking
    daily_intention_text: Mapped[str] = mapped_column(Text)
    target_quantity: Mapped[int] = mapped_column()
    completed_quantity: Mapped[int] = mapped_column(default=0) # Default to 0, updated as user completes tasks
    status: Mapped[str] = mapped_column(String(20), default='pending') # 'pending', 'in_progress', 'completed', 'failed'
    focus_block_count: Mapped[int] = mapped_column()
    
    # AI Coaching (keeping for V2)
    ai_feedback: Mapped[Optional[str]] = mapped_column(Text) # Null if Claude API is to fail. Will be given using async retry if this was to be the case
    user_response_to_ai_feedback: Mapped[Optional[str]] = mapped_column(Text)
    user_agreed_with_ai: Mapped[Optional[bool]] = mapped_column()
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), index=True) # Index for quick retrieval of daily intentions

    # Relationships
    user: Mapped["User"] = relationship(back_populates="daily_intentions")
    daily_result: Mapped["DailyResult"] = relationship(back_populates="daily_intention") # One-to-one relationship with DailyResult
    focus_blocks: Mapped[List["FocusBlock"]] = relationship(back_populates="daily_intention") #For individual focus block tracking

class FocusBlock(Base):
    __tablename__ = "focus_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    daily_intention_id: Mapped[int] = mapped_column(ForeignKey("daily_intentions.id")) # Foreign Key to link back to the main goal

    duration_minutes: Mapped[int] = mapped_column(default=50) # Defaults to 50
    focus_block_intention: Mapped[str] = mapped_column(Text) # The "chunked-down intention"

    # The optional video journal URLs from Neeto/Loom
    pre_block_video_url: Mapped[Optional[str]] = mapped_column(String(2048))
    post_block_video_url: Mapped[Optional[str]] = mapped_column(String(2048))

    status: Mapped[str] = mapped_column(String(20), default='pending') # e.g., 'pending', 'completed'
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationship back to DailyIntention
    daily_intention: Mapped["DailyIntention"] = relationship(back_populates="focus_blocks")

class DailyResult(Base):
    __tablename__ = "daily_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    daily_intention_id: Mapped[int] = mapped_column(ForeignKey("daily_intentions.id"))
    succeeded_failed: Mapped[bool] = mapped_column()
    ai_feedback: Mapped[Optional[str]] = mapped_column(Text)
    xp_awarded: Mapped[int] = mapped_column(default=0)
    discipline_stat_gain: Mapped[int] = mapped_column(default=0)
    user_confirmation_correction: Mapped[Optional[bool]] = mapped_column() # User can confirm or correct AI feedback. True is confirmation, False is correction
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Recovery Quest fields - Action Quests will be added in V2!
    recovery_quest: Mapped[Optional[str]] = mapped_column(Text) # Null if user succeeded in their Daily Intention
    recovery_quest_type: Mapped[str] = mapped_column(String(20), default='reflection') # 'reflection' or 'action'. Defaults to 'reflection' in MVP
    recovery_quest_response: Mapped[Optional[str]] = mapped_column(Text) # Users's response/proof. Null if no Recovery Quest was given
    recovery_quest_completed: Mapped[bool] = mapped_column(default=False) # V2 feature

    daily_intention: Mapped["DailyIntention"] = relationship(back_populates="daily_result")

class AICoachingLog(Base):
    __tablename__ = "ai_coaching_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user_text: Mapped[str] = mapped_column(Text) # What someone submitted/said
    ai_feedback: Mapped[str] = mapped_column(Text) # AI's coaching response
    coaching_trigger: Mapped[str] = mapped_column(String(50)) # Trigger for the AI coaching, e.g. 'daily_intention', 'evening_assessment', 'recovery_quest' etc. String now, Enum in V2
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="ai_coaching_logs")