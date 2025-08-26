from sqlalchemy.orm import Session
from datetime import datetime, date, timezone
import random

import app.models as models
import app.schemas as schemas

"""
======================================================================
SERVICE LAYER (PUBLIC DEMO)
======================================================================
This file contains the business logic for the application.

NOTE FOR REVIEWERS:
For this public demonstration repository, the complex business logic
and proprietary AI prompt engineering have been "hollowed-out". 
The functions in this service layer simulate the expected outcomes 
without revealing the core intellectual property of the application.

In the private production repository, these functions contain:
- Detailed game mechanic calculations (XP, stat gains, etc.).
- Complex, multi-step prompt chains for the Anthropic API.
- Logic for dynamic content generation based on user history.
======================================================================
"""

# --- GAME MECHANICS ---
# This dictionary defines the core reward structure
XP_REWARDS = {
    'focus_block_completed': 10,
    'daily_intention_completed': 20,
    'recovery_quest_completed': 15,
}

# --- STREAK LOGIC ---
# This function is a core piece of the application's retention strategy and
# a great example of testable, standalone business logic.
def update_user_streak(user: models.User, today: date = date.today()):
    """
    The "Streak Guardian." Contains the core logic for updating a user's streak,
    following the "one grace day" rule.
    """
    if user.last_streak_update and user.last_streak_update.date() >= today:
        return False # Streak already updated today

    days_since_last_update = float('inf')
    if user.last_streak_update:
        days_since_last_update = (today - user.last_streak_update.date()).days

    if days_since_last_update == 1:
        user.current_streak += 1 # Continue streak
    elif days_since_last_update > 1 or days_since_last_update == float('inf'):
        user.current_streak = 1 # Reset or start streak

    if user.current_streak > user.longest_streak:
        user.longest_streak = user.current_streak

    user.last_streak_update = datetime.now(timezone.utc)
    return True

# --- MOCKED AI INTERACTIONS ---

def create_and_process_intention(
    db: Session, user: models.User, intention_data: schemas.DailyIntentionCreate
) -> dict:
    """
    SIMULATES analyzing a new Daily Intention.

    In the production app, this calls the AI to analyze the Daily Intention 
    against the user's HRGA and determines if it needs refinement. For this demo, 
    it randomly decides whether to approve it or ask for refinement to showcase
    both application flows.
    """
    print("--- SIMULATING DAILY INTENTION ANALYSIS ---")
    
    # Showcase both paths: if it's the first submission, randomly ask for refinement.
    # If it's a refined submission, always approve.
    if not intention_data.is_refined and random.choice([True, False]):
        print("--- SIMULATION: Intention needs refinement. ---")
        return {
            "needs_refinement": True,
            "ai_feedback": "Mock Feedback: This is a good start, but could you be more specific? For example, instead of 'work on business', try 'send 5 cold outreach emails'."
        }

    print("--- SIMULATION: DAILY Intention approved. Creating in database. ---")
    # In the real app, stats would be modified here. We simulate that.
    # The actual db commit will happen in the endpoint.
    return {
        "needs_refinement": False,
        "ai_feedback": "Mock Feedback: This is a clear and actionable intention. Approved!",
        "clarity_stat_gain": 1 # The endpoint will use this to update the model
    }


def complete_focus_block(db: Session, user: models.User, block: models.FocusBlock) -> dict:
    """
    SIMULATES awarding XP for completing a Focus Block.
    """
    print(f"--- SIMULATING XP GAIN FOR FOCUS BLOCK {block.id} ---")
    return {"xp_awarded": XP_REWARDS['focus_block_completed']}


def create_daily_reflection(
    db: Session, user: models.User, daily_intention: models.DailyIntention
) -> dict:
    """
    SIMULATES the evening reflection process.

    Checks if the day was a success or failure and returns mock AI feedback
    and a mock Recovery Quest if needed. In production, this involves calls
    to different AI endpoints based on the outcome.
    """
    print("--- SIMULATING DAILY REFLECTION AND FEEDBACK GENERATION ---")
    
    succeeded = daily_intention.status == 'completed'
    
    if succeeded:
        return {
            "succeeded": True,
            "ai_feedback": "Mock Success Feedback: Great job completing your goal! Consistency is key.",
            "recovery_quest": None,
            "discipline_stat_gain": 1,
            "xp_awarded": XP_REWARDS['daily_intention_completed']
        }
    else: # Failed
        completion_rate = (
            (daily_intention.completed_quantity / daily_intention.target_quantity) * 100
            if daily_intention.target_quantity > 0 else 0
        )
        return {
            "succeeded": False,
            "ai_feedback": f"Mock Failure Feedback: You achieved {completion_rate:.1f}%. Let's reflect on this.",
            "recovery_quest": "Mock Recovery Quest: What was the primary obstacle you faced today?",
            "discipline_stat_gain": 0,
            "xp_awarded": 0
        }


def process_recovery_quest_response(
    db: Session, user: models.User, result: models.DailyResult, response_text: str
) -> dict:
    """
    SIMULATES providing AI coaching after a user reflects on a failed day,
    re-wiring how the user thinks about failure.
    """
    print("--- SIMULATING AI COACHING FOR RECOVERY QUEST ---")
    
    return {
        "ai_coaching_feedback": "Mock Coaching: That's a valuable insight. Acknowledging the obstacle is the first step to overcoming it. You've earned Resilience for this reflection.",
        "resilience_stat_gain": 1,
        "xp_awarded": XP_REWARDS['recovery_quest_completed']
    }

