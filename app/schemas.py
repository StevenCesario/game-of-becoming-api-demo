from pydantic import BaseModel, field_validator, Field, EmailStr, ConfigDict, computed_field
from typing import Optional, Union
from datetime import datetime
from enum import Enum
import math


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
    hla: Optional[str] = Field(None, min_length=1, max_length=8000) # Reasonable cap. Can be None at registration, not after onboarding!

    @field_validator('name') # Validator doesn't validate hla anymore
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
    
    
class UserUpdate(BaseModel):
    """Schema for updating a user's profile, e.g., during onboarding."""
    # We only allow updating the hla for now, but could add name, etc., later.
    hla: str = Field(..., min_length=10, max_length=8000)

    @field_validator('hla')
    def validate_hla(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("HLA cannot be empty.")
        return v
    

class UserResponse(BaseModel):
    """Schema for User response (without password)"""
    id: int
    name: str
    email: str
    hla: Optional[str]
    current_streak: int
    longest_streak: int
    registered_at: datetime

    # New Onboarding fields
    vision: Optional[str]
    milestone: Optional[str]
    constraint: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class CharacterStatsResponse(BaseModel):
    user_id: int
    # level: int, xp_for_next_level: int, and xp_needed_to_level: int are now all computed fields!
    xp: int
    resilience: int
    clarity: int
    discipline: int
    commitment: int

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def level(self) -> int:
        """Calculate the user level based on total XP"""
        if self.xp < 0: return 1
        # The formula for level is the inverse of the XP formula: L = floor(sqrt(XP/100)) + 1
        return math.floor((self.xp / 100) ** 0.5) + 1
    
    @computed_field
    @property
    def xp_for_next_level(self) -> int:
        """Calculates the total XP required to reach the next level."""
        # The formula for total XP to reach a level is 100 * (L-1)^2
        next_level = self.level + 1
        return 100 * (next_level - 1) ** 2

    @computed_field
    @property
    def xp_needed_to_level(self) -> int:
        """Calculates the XP needed to get to the next level."""
        return self.xp_for_next_level - self.xp


# =============================================================================
# ONBOARDING SCHEMAS
# =============================================================================

class OnboardingStepInput(BaseModel):
    """Input from the user for a given onboarding step."""
    step: str = Field(..., description="The current step being completed, e.g., 'vision', 'milestone', 'constraint', 'hla'")
    text: str = Field(..., min_length=5, max_length=2000)

class OnboardingStepResponse(BaseModel):
    """The AI Coach's response, guiding the user to the next step."""
    ai_response: str
    next_step: Optional[str] = Field(None, description="The name of the next step, e.g., 'milestone'. Null if onboarding is complete.")
    # This will hold the final, AI-refined HLA at the end of the process
    final_hla: Optional[str] = None


# =============================================================================
# DAILY INTENTIONS SCHEMAS (Updated for Smart Detection)
# =============================================================================

class DailyIntentionCreate(BaseModel):
    """Schema for creating a new Daily Intention"""
    daily_intention_text: str
    target_quantity: int
    focus_block_count: int 
    is_refined: bool = False # Flag to indicate need for clarity refinement. Defaults to False

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


# # NEW: This is the response when the AI says the intention needs refinement
# class DailyIntentionRefinementResponse(BaseModel):
#     """Response when an intention needs refinement by the user"""
#     needs_refinement: bool = True # Defaults to True
#     ai_feedback: str
# Obsolete, no longer used


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

class FocusBlockCompletionResponse(FocusBlockResponse):
    """Specific response for when a Focus Block is completed, including the XP awarded."""
    xp_awarded: int = 0


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

class DailyResultCompletionResponse(DailyResultResponse):
    """
    Specific response for when a Daily Intention is completed or failed, including the XP 
    awarded and stat gain.
    """
    xp_awarded: int = 0
    discipline_stat_gain: int = 0


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
    resilience_stat_gain: int = 0
    xp_awarded: int = 0


# DailyIntentionResponse is down here since it contain both Focus Blocks and potentially a Daily Result
# MODIFIED: Now includes Focus Blocks for a more RESTful approach
# MODIFIED: Now *also* includes an optional DailyResult
class DailyIntentionResponse(BaseModel):
    """Unified response for all successful/existing Daily Intention endpoints"""
    id: int
    user_id: int
    daily_intention_text: str
    target_quantity: int
    completed_quantity: int
    focus_block_count: int
    # completion_percentage: float is removed and replaced with a computed_field!
    status: str # 'pending', 'in_progress', 'completed', 'failed'
    created_at: datetime
    ai_feedback: Optional[str] = None # AI coach's immediate feedback. Can be null if Claude API fails
    needs_refinement: bool = False # New. Always False for an approved intention (doesn't need refinement)
    
    focus_blocks: list[FocusBlockResponse] = [] # It tells Pydantic to expect a list of objects that match the FocusBlockResponse schema
    daily_result: Optional[DailyResultCompletionResponse] = None

    model_config = ConfigDict(from_attributes=True) # Allows model to be created from ORM attributes

    @computed_field
    @property
    def completion_percentage(self) -> float:
        """Calculates the completion percentage for the intention."""
        if self.target_quantity == 0:
            return 0.0
        return (self.completed_quantity / self.target_quantity) * 100

# # Tells the creation endpoint what its possible responses are
# DailyIntentionCreateResponse = Union[DailyIntentionRefinementResponse, DailyIntentionResponse]
# Obsolete, no longer used


# =============================================================================
# GAME STATE SCHEMA
# =============================================================================

class GameStateResponse(BaseModel):
    """
    The comprehensive state of the user's game, returned on login
    or app start. The single source of truth for the frontend
    """
    user: UserResponse
    stats: CharacterStatsResponse
    todays_intention: Optional[DailyIntentionResponse] = None
    unresolved_intention: Optional[DailyIntentionResponse] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# AI CHAT SCHEMAS
# =============================================================================

class ChatMessageInput(BaseModel):
    """Schema for the user's input message to the AI chat."""
    text: str = Field(..., min_length=1, max_length=4000)

class ChatMessageResponse(BaseModel):
    """Schema for the AI's response in the chat."""
    ai_response: str


# =============================================================================
# CONVERSATIONAL DAILY INTENTION CREATION SCHEMAS
# =============================================================================

class CreationStep(str, Enum):
    """Defines the possible steps in the conversational creation process."""
    AWAITING_TEXT = "AWAITING_TEXT"
    AWAITING_REFINEMENT = "AWAITING_REFINEMENT"
    # We will add these in the next iteration to keep the flow manageable
    # AWAITING_QUANTITY = "AWAITING_QUANTITY"
    # AWAITING_BLOCKS = "AWAITING_BLOCKS"
    COMPLETE = "COMPLETE"

class IntentionCreationRequest(BaseModel):
    """The frontend sends this to the backend with each message during creation."""
    user_text: str = Field(..., min_length=1)
    # The frontend must tell the backend what step of the conversation it thinks it's on.
    current_step: CreationStep
    
    # We'll use these fields in subsequent steps. For now, they can be optional.
    target_quantity: Optional[int] = None
    focus_block_count: Optional[int] = None

class IntentionCreationResponse(BaseModel):
    """The backend sends this back, telling the frontend exactly what to do next."""
    next_step: CreationStep
    ai_message: str
    # The final, completed intention object will only be sent when the conversation is complete.
    intention_payload: Optional[DailyIntentionResponse] = None