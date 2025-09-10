from typing import Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime, date, timezone
import os, asyncio

from . import models
from . import schemas

"""
======================================================================
SERVICE LAYER (PUBLIC DEMO V2)
======================================================================
This file contains the business logic for the application.

NOTE FOR REVIEWERS:
For this public demonstration repository, the complex business logic
and proprietary AI prompt engineering have been "hollowed-out". 
The functions in this service layer simulate the expected outcomes by
returning structured Pydantic models, mirroring the production app's
architecture without revealing the core intellectual property.
======================================================================
"""

# --- GAME MECHANICS ---
XP_REWARDS = {
    'focus_block_completed': 10,
    'daily_intention_completed': 20,
    'recovery_quest_completed': 15,
}

def _calculate_xp_with_streak_bonus(base_xp: int, current_streak: int) -> int:
    """
    Calculates the final XP to be awarded by applying a streak bonus.
    This is the single source of truth for the streak multiplier formula.
    """
    if current_streak <= 0:
        return base_xp
    
    streak_bonus_multiplier = 1 + (current_streak * 0.01)
    xp_to_award = round(base_xp * streak_bonus_multiplier)
    return xp_to_award

# --- STRUCTURED AI RESPONSE MODELS (FOR DEMONSTRATION) ---

class IntentionAnalysisResponse(BaseModel):
    is_strong_intention: bool = Field(description="True if the intention is clear, specific, and ready for commitment. False if it needs refinement.")
    feedback: str = Field(description="Encouraging, actionable coaching feedback for the user (2-3 sentences max).")
    clarity_stat_gain: int = Field(description="Set to 1 if is_strong_intention is true, otherwise 0.")

class DailyReflectionResponse(BaseModel):
    ai_feedback: str = Field(description="AI coach's feedback on the user's day.")
    recovery_quest: Optional[str] = Field(description="A specific recovery quest if the day was a failure. Null if successful.")
    discipline_stat_gain: int = Field(description="Discipline stat points to award (1 for success, 0 for failure).")

class RecoveryQuestCoachingResponse(BaseModel):
    ai_coaching_feedback: str = Field(description="Encouraging, wisdom-building coaching based on the user's reflection.")
    resilience_stat_gain: int = Field(description="Set to 1 for completing the reflection.")


# --- SERVICE FUNCTIONS (BUSINESS LOGIC LAYER) ---

def update_user_streak(user: models.User):
    """
    The "Streak Guardian." Contains the core logic for updating a user's streak,
    following the "one grace day" rule.
    """
    today = date.today() # Get the date when the function is actually called
    if user.last_streak_update and user.last_streak_update.date() >= today:
        return False

    days_since_last_update = float('inf')
    if user.last_streak_update:
        days_since_last_update = (today - user.last_streak_update.date()).days

    if days_since_last_update == 1:
        user.current_streak += 1
    elif days_since_last_update > 1 or days_since_last_update == float('inf'):
        user.current_streak = 1

    if user.longest_streak is None or user.current_streak > user.longest_streak:
        user.longest_streak = user.current_streak

    user.last_streak_update = datetime.now(timezone.utc)
    return True

async def create_and_process_intention(db: Session, user: models.User, intention_data: schemas.DailyIntentionCreate) -> dict:
    """
    SIMULATES analyzing a new Daily Intention using the production app's architecture.
    """
    # This pattern allows for testing the full application flow without making real AI calls.
    if os.getenv("DISABLE_AI_CALLS") == "True":
        print("--- AI CALL DISABLED: Returning mock 'APPROVED' response. ---")
        return {
            "needs_refinement": False,
            "ai_feedback": "Mock Feedback: This is a clear and actionable intention!",
            "clarity_stat_gain": 1
        }
    
    # In production, this section contains a detailed multi-step prompt
    # that calls an LLM provider and returns a validated Pydantic model.
    print("--- SIMULATING PRODUCTION AI CALL FOR INTENTION ANALYSIS ---")
    await asyncio.sleep(1) # Simulate network latency
    
    # This mock response simulates the AI approving the intention.
    mock_analysis = IntentionAnalysisResponse(
        is_strong_intention=True,
        feedback="This is a clear, specific, and actionable intention. Let's get to work!",
        clarity_stat_gain=1
    )
    
    return {
        "needs_refinement": not mock_analysis.is_strong_intention,
        "ai_feedback": mock_analysis.feedback,
        "clarity_stat_gain": mock_analysis.clarity_stat_gain,
    }

def complete_focus_block(db: Session, user: models.User, block: models.FocusBlock) -> dict:
    """
    Awards XP for a completed Focus Block using the central rulebook and streak multiplier.
    """
    base_xp = XP_REWARDS.get('focus_block_completed', 0)
    xp_to_award = _calculate_xp_with_streak_bonus(base_xp, user.current_streak)
    return {"xp_awarded": xp_to_award}

async def create_daily_reflection(db: Session, user: models.User, daily_intention: models.DailyIntention) -> dict:
    """
    SIMULATES generating the end-of-day reflection.
    """
    succeeded = daily_intention.status == "completed"
    xp_to_award = 0
    if succeeded:
        base_xp = XP_REWARDS.get('daily_intention_completed', 0)
        xp_to_award = _calculate_xp_with_streak_bonus(base_xp, user.current_streak)

    if os.getenv("DISABLE_AI_CALLS") == "True":
        print("--- AI CALL DISABLED: Returning mock reflection. ---")
        if succeeded:
            return {"succeeded": True, "ai_feedback": "Mock Success: Great job!", "recovery_quest": None, "discipline_stat_gain": 1, "xp_awarded": xp_to_award}
        else:
            return {"succeeded": False, "ai_feedback": "Mock Fail: Let's reflect.", "recovery_quest": "What was the main obstacle?", "discipline_stat_gain": 0, "xp_awarded": 0}

    # In production, this contains a prompt that generates a structured response.
    print("--- SIMULATING PRODUCTION AI CALL FOR DAILY REFLECTION ---")
    await asyncio.sleep(1)

    mock_reflection = DailyReflectionResponse(
        ai_feedback="Outstanding execution! Completing your intention directly fuels your goal. This is how momentum is built.",
        recovery_quest=None,
        discipline_stat_gain=1
    )
    
    response = mock_reflection.model_dump()
    response["succeeded"] = succeeded
    response["xp_awarded"] = xp_to_award
    return response

async def process_recovery_quest_response(db: Session, user: models.User, result: models.DailyResult, response_text: str) -> dict:
    """
    SIMULATES providing AI coaching for a Recovery Quest.
    """
    base_xp = XP_REWARDS.get('recovery_quest_completed', 0)
    xp_to_award = _calculate_xp_with_streak_bonus(base_xp, user.current_streak)

    if os.getenv("DISABLE_AI_CALLS") == "True":
        print("--- AI CALL DISABLED: Returning mock coaching. ---")
        return {"ai_coaching_feedback": "Mock Coaching: That's a great insight.", "resilience_stat_gain": 1, "xp_awarded": xp_to_award}

    print("--- SIMULATING PRODUCTION AI CALL FOR RECOVERY QUEST COACHING ---")
    await asyncio.sleep(1)

    mock_coaching = RecoveryQuestCoachingResponse(
        ai_coaching_feedback="That's a powerful insight. Recognizing the trigger is the first step to managing it. This awareness is how you build resilience.",
        resilience_stat_gain=1
    )
    
    response = mock_coaching.model_dump()
    response["xp_awarded"] = xp_to_award
    return response