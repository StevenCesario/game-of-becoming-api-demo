from pydantic import BaseModel, field_validator, Field, EmailStr, ConfigDict
from typing import Optional, Union
from datetime import datetime

# =============================================================================
# SECURITY SCHEMAS
# =============================================================================

class TokenResponse(BaseModel):
    """
    Schema for the response when a token is successfully created.
    This is the standard way to return a JWT.
    """
    access_token: str
    token_type: str = "bearer" # "bearer" is the standard token type

class TokenData(BaseModel):
    """
    Schema for the data we embed inside the JWT payload.
    This is what we'll get back after decoding a token.
    """
    user_id: str | None = None

# =============================================================================
# USER SCHEMAS (Updated for Character Stats)
# =============================================================================

class UserBase(BaseModel):
    """Base schema for User"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    hrga: str = Field(..., min_length=1, max_length=8000) # Reasonable cap

    @field_validator('name', 'hrga')
    def validate_text_fields(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty or just whitespace")
        return v
    

class UserCreate(UserBase):
    """Schema for creating a new User"""
    password: str = Field(..., min_length=12, max_length=128)

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long")
        return v
    
    
class UserUpdate(UserBase):
    """Schema for updating User information"""
    # Inherits all fields from UserBase
    pass
    

class UserResponse(BaseModel):
    """Schema for User response (without password)"""
    id: int
    name: str
    email: str
    hrga: str
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CharacterStatsResponse(BaseModel):
    user_id: int
    level: int # The calculated level
    xp: int
    resilience: int
    clarity: int
    discipline: int
    commitment: int

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# DAILY INTENTIONS SCHEMAS (Updated for Smart Detection)
# =============================================================================

class DailyIntentionCreate(BaseModel):
    """Schema for creating a new Daily Intention"""
    daily_intention_text: str
    target_quantity: int
    focus_block_count: int 
    is_refined: bool = False # NEW: Flag to indicate a refine submission. Defaults to False

    @field_validator('daily_intention_text')
    def validate_daily_intention_text(cls, v):
        # Strip whitespace and ensure not empty
        v = v.strip()
        if not v:
            raise ValueError("Daily intention cannot be empty or just whitespace")
        if len(v) > 2000:
            raise ValueError("Daily intention cannot exceed 2000 characters")
        return v
    
    @field_validator('target_quantity')
    def validate_target_quantity(cls, v):
        if v < 1:
            raise ValueError('Target quantity must be at least 1')
        if v > 100:
            raise ValueError('Target quantity cannot exceed 100. Let\'s focus on what truly matters today!')
        return v

    @field_validator('focus_block_count')
    def validate_focus_block_count(cls, v):
        if v < 1:
            raise ValueError('Focus block count must be at least 1')
        if v > 30:
            raise ValueError('Focus block count cannot exceed 30 - that\'s unrealistic for one day!') # Assuming a reasonable range for amount of focus blocks in a day
        return v
    

class DailyIntentionUpdate(BaseModel):
    """Schema for updating Daily Intention progress"""
    completed_quantity: int

    @field_validator('completed_quantity')
    def validate_completed_quantity(cls, v):
        if v < 0:
            raise ValueError('Completed quantity cannot be negative')
        if v > 1000:
            raise ValueError('Completed quantity cannot exceed 1000')
        return v


# NEW: This is the response when the AI says the intention needs refinement
class DailyIntentionRefinementResponse(BaseModel):
    """Response when an intention needs refinement by the user"""
    needs_refinement: bool = True # Defaults to True
    ai_feedback: str


# MODIFIED: Original response schema
class DailyIntentionResponse(BaseModel):
    """Unified response for all successful/existing Daily Intention endpoints"""
    id: int
    user_id: int
    daily_intention_text: str
    target_quantity: int
    completed_quantity: int
    focus_block_count: int
    completion_percentage: float
    status: str # 'pending', 'in_progress', 'completed', 'failed'
    created_at: datetime
    ai_feedback: Optional[str] = None # AI coach's immediate feedback. Can be null if Claude API fails
    needs_refinement: bool = False # New. Always False for an approved intention (doesn't need refinement)

    model_config = ConfigDict(from_attributes=True) # Allows model to be created from ORM attributes


# NEW: Tells the creation endpoint what its possible responses are
DailyIntentionCreateResponse = Union[DailyIntentionRefinementResponse, DailyIntentionResponse]


# =============================================================================
# FOCUS BLOCK SCHEMAS
# =============================================================================

class FocusBlockBase(BaseModel):
    """Base schema for a Focus Block, containing shared fields."""
    focus_block_intention: str = Field(..., min_length=1, max_length=2000)
    duration_minutes: int = Field(default=50, gt=0, le=120) # Must be > 0 and <= 120 mins

# FocusBlockCreate is an alias for FocusBlockBase. To create a block, we just need the base fields. No user_id needed!
FocusBlockCreate = FocusBlockBase

class FocusBlockResponse(FocusBlockBase):
    """Schema for returning a Focus Block from the API."""
    id: int
    daily_intention_id: int
    status: str
    pre_block_video_url: Optional[str] = None
    post_block_video_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FocusBlockUpdate(BaseModel):
    """Schema for updating a Focus Block, e.g., with video URLs."""
    pre_block_video_url: Optional[str] = None
    post_block_video_url: Optional[str] = None
    status: Optional[str] = None # To mark as 'completed' later


# =============================================================================
# DAILY RESULTS SCHEMAS (Evening Reflection)
# =============================================================================

class DailyResultCreate(BaseModel):
    """Schema for creating evening reflection"""
    daily_intention_id: int

    @field_validator('daily_intention_id')
    def validate_daily_intention_id(cls, v):
        if v < 1:
            raise ValueError('Daily intention ID must be a positive integer')
        return v


class DailyResultResponse(BaseModel):
    """Schema for daily result responses"""
    id: int
    daily_intention_id: int
    succeeded_failed: bool
    ai_feedback: Optional[str] = None
    recovery_quest: Optional[str] = None
    recovery_quest_response: Optional[str] = None
    user_confirmation_correction: Optional[bool] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecoveryQuestInput(BaseModel):
    """Schema for user's Recovery Quest response input"""
    recovery_quest_response: str

    @field_validator('recovery_quest_response')
    def validate_response(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Recovery quest response cannot be empty")
        if len(v) > 2000:
            raise ValueError("Response cannot exceed 2000 characters")
        return v

class RecoveryQuestResponse(BaseModel):
    """Schema for the complete Recovery Quest response (includes AI feedback)"""
    recovery_quest_response: str
    ai_coaching_feedback: str  # AI generates this