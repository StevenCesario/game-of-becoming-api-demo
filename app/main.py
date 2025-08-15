from __future__ import annotations  # keep ForwardRef happy with annotation-handling

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timezone
from typing import Annotated
from dotenv import load_dotenv
import math

# ---- Internal package imports (namespaced) ----
import app.crud as crud
import app.database as database
import app.security as security
import app.services as services
import app.utils as utils
import app.models as models
import app.schemas as schemas

# Load environment variables
load_dotenv()

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI app setup
app = FastAPI(
    title="Game of Becoming API",
    description="Gamify your business growth with AI-driven daily intentions and feedback.",
    version="1.0.0",
    docs_url="/docs"
)

# Utility functions
def calculate_level(xp: int) -> int:
    """Calculates user level based on total XP."""
    if xp < 0:
        return 1
    return math.floor((xp / 100) ** 0.5) + 1

# ---------- ENDPOINT DEPENDENCIES ----------

def get_current_user_daily_intention(
    # This dependency itself depends on our other dependencies
    current_user: Annotated[models.User, Depends(security.get_current_user)],
    db: Session = Depends(database.get_db)
) -> models.DailyIntention:
    """
    A dependency that gets the current user's intention for today.

    It automatically handles authentication and database access.
    If an intention is found, it returns the DailyIntention object.
    If no intention is found, it raises a 404 error, stopping the request.
    """
    # Get today's Daily Intention for the currently logged in user
    intention = crud.get_today_intention(db, current_user.id)
    if not intention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily Intention for today not found. Ready to create one?"
        )
    return intention

def get_current_user_stats(
    current_user: Annotated[models.User, Depends(security.get_current_user)],
    db: Session = Depends(database.get_db)
) -> models.CharacterStats:
    """
    A dependency that gets the current user's character stats.
    
    It automatically handles authentication and database access.
    It will always return a valid CharacterStats object, creating one
    if it doesn't exist.
    """
    # The crud function guarantees a stats object will be returned,
    # so we can just return its result directly. No check needed.
    return crud.get_or_create_user_stats(db, user_id=current_user.id)

def get_owned_focus_block(
        block_id: int, # We get this from the endpoint path parameter
        current_user: Annotated[models.User, Depends(security.get_current_user)], 
        db: Session = Depends(database.get_db)
) -> models.FocusBlock:
    """
    A dependency that gets a specific Focus Block by its ID, but only if
    it belongs to the currently authenticated user.

    Raises a 404 if the block is not found or not owned by the user.
    """
    # Join FocusBlock and DailyIntention and filter by BOTH block_id and user_id
    block = db.query(models.FocusBlock).join(models.DailyIntention).filter(
        models.FocusBlock.id == block_id,
        models.DailyIntention.user_id == current_user.id
    ).first()

    if not block:
        # We use 404 for both "not found" and "not owned" to avoid leaking information.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Focus Block not found.")
    
    return block

def get_owned_daily_result_by_intention_id(
        intention_id: int, # Gets this from the endpoint path parameter
        current_user: Annotated[models.User, Depends(security.get_current_user)],
        db: Session = Depends(database.get_db)
) -> models.DailyResult:
    """
    A dependency that gets a specific Daily Result by its parent intention's ID,
    but only if it belongs to the currently authenticated user.

    Raises a 404 if the result is not found or not owned by the user.
    """
    # This query links the DailyResult to the DailyIntention to check the user_id.
    result = db.query(models.DailyResult).join(models.DailyIntention).filter(
        models.DailyResult.daily_intention_id == intention_id,
        models.DailyIntention.user_id == current_user.id
    ).first()

    if not result:
        # Use 404 for security, hiding whether the result exists or is just not owned.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Daily Result not found.")
    
    return result

def get_owned_daily_result_by_result_id(
    result_id: int, # Gets this from the path
    current_user: Annotated[models.User, Depends(security.get_current_user)],
    db: Session = Depends(database.get_db)
) -> models.DailyResult:
    """
    Dependency to get a DailyResult by its own ID, ensuring it belongs
    to the current user. This is the final ownership check.
    """
    # We query DailyResult, join its parent DailyIntention, and check the user_id.
    result = db.query(models.DailyResult).join(models.DailyIntention).filter(
        models.DailyResult.id == result_id,
        models.DailyIntention.user_id == current_user.id
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="Daily Result not found.")
    
    return result

# ---------- GENERAL ENDPOINTS ----------

@app.get("/")
def read_root():
    """Welcome root endpoint - the beginning of the transformational journey!"""
    return {
        "message": "Welcome to The Game of Becoming API!",
        "description": "Ready to turn your exectution blockers into breakthrough momentum?",
        "docs": "Visit /docs for interactive API documentation.",
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and deployment verification"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "service": "Game of Becoming API",
        "version": "1.0.0"
    }

@app.post("/login", response_model=schemas.TokenResponse)
def login_for_access_token(
    # This is the "magic" part. FastAPI will automatically handle getting the 
    # 'username' and 'password' from the form body and put them into this 'form_data' object.
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], # Annotated can be seen as a sticky note
    db: Session = Depends(database.get_db)
):
    """
    The Bouncer. Now using OAuth2PasswordRequestForm to handle form data. 
    1. Uses the standard OAuth2PasswordRequestForm to handle form data.
    2. Finds the user in the database via the new crud function.
    3. Verifies the password using the security function.
    4. If valid, creates and returns a JWT (the wristband).
    """
    # 1. Find the user by their email (which OAuth2 calls 'username')
    user = crud.get_user_by_email(db, email=form_data.username)

    # 2. Verify that the user exists and that the password is correct
    if not user or not utils.verify_password(form_data.password, user.auth.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # We use a generic error to prevent attackers from guessing valid emails.
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 3. If credentials are valid, create the access token
    # The 'sub' (subject) claim in the token is the user's ID
    access_token = security.create_access_token(data={"sub": str(user.id)})

    # 4. Return the token in the standard Bearer format
    return {"access_token": access_token, "token_type": "bearer"}


# USER ENDPOINTS

# Simplified using create_user in crud.py
@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """
    Register a new user and their associated records. 
    Also now creates their initial character stats

    The user starts their Game of Becoming journey here!
    """

    # Check if user already exists
    existing_user = crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Ready to log in instead?"
        )
    
    try:
        # Create the User record
        new_user = crud.create_user(db=db, user_data=user_data)
        db.commit()
        db.refresh(new_user)

        # Return the user 
        return new_user
    
    except Exception as e:
        db.rollback()  # Roll back on any error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user account: {str(e)}"
        )

@app.get("/users/me", response_model=schemas.UserResponse)
def get_user(current_user: Annotated[models.User, Depends(security.get_current_user)]):
    """Get the profile for the currently logged-in user for the frontend to display user informaiton."""
    # The 'get_current_user' dependency has already done all the work:
    # 1. It got the token.
    # 2. It validated the token.
    # 3. It fetched the user from the database.
    # 4. It handled the "user not found" case.
    
    return current_user

@app.get("/users/me/stats", response_model=schemas.CharacterStatsResponse)
def get_my_character_stats(
    current_user: Annotated[models.User, Depends(security.get_current_user)]
    ):
    """Get the character stats for the currently authenticated user."""
    # Access the stats directly through the relationship
    stats = current_user.character_stats

    # The user should always have stats, but it's good practice to check
    if not stats:
        raise HTTPException(status_code=404, detail="Character stats not found for your account.")

    # Return a response that includes the calculated level
    response = schemas.CharacterStatsResponse.model_validate(stats)
    response.level = calculate_level(stats.xp) # Manually add the calculated level value
    return response


# DAILY INTENTIONS ENDPOINTS

# Updated for Smart Detection!
@app.post("/intentions", response_model=schemas.DailyIntentionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_daily_intention(
    intention_data: schemas.DailyIntentionCreate,
    current_user: Annotated[models.User, Depends(security.get_current_user)],
    stats: Annotated[models.CharacterStats, Depends(get_current_user_stats)],
    db: Session = Depends(database.get_db)
):
    """
    Create today's Daily Intention, using the mock service layer.
    Handles initial submissions and refined submissions after AI feedback.
    """
    # 1. Check if today's Daily Intention for the currently logged in user already exists
    if crud.get_today_intention(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daily Intention already exists for today! Get going making progress on it!"
        )
    
    # 2. Delegate to the mock service layer (with mock AI prompts and logic for this showcase)
    process_result = services.create_and_process_intention(db, current_user, intention_data)

    # 3. Handle the result from the mock service
    if process_result.get("needs_refinement"):
        # Path 1: The mock service decided refinement is needed. Return the AI feedback
        # This is a manual construction because the object doesn't exist in the DB.
        return schemas.DailyIntentionRefinementResponse(ai_feedback=process_result["ai_feedback"])
    else:
        # Path 2: The mock service approved the intention. Save it to the database
        try:
            db_intention = models.DailyIntention(
                user_id=current_user.id,
                daily_intention_text=intention_data.daily_intention_text.strip(),
                target_quantity=intention_data.target_quantity,
                focus_block_count=intention_data.focus_block_count,
                ai_feedback=process_result.get("ai_feedback"),
            )
            db.add(db_intention)

            # Update Clarity stat using our dependency
            clarity_gain = process_result.get("clarity_stat_gain", 0)
            if clarity_gain > 0:
                stats.clarity += clarity_gain

            db.commit()
            db.refresh(db_intention)
            if clarity_gain > 0:
                db.refresh(stats)

            return db_intention
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create Daily Intention: {e}")
            

@app.get("/intentions/today/me", response_model=schemas.DailyIntentionResponse)
def get_my_daily_intention(
    intention: Annotated[models.DailyIntention, Depends(get_current_user_daily_intention)]
    ):
    """
    Get today's Daily Intention for the currently logged in user.
    The core of the Daily Commitment Screen!
    """
    # 1. Calculate the value that doesn't exist in the database model.
    completion_percentage = (
        (intention.completed_quantity / intention.target_quantity) * 100
        if intention.target_quantity > 0 else 0.0
    )

    # 2. Because we have a calculated value, we MUST manually construct the Pydantic response model. 
    return schemas.DailyIntentionResponse(
        id=intention.id,
        user_id=intention.user_id,
        daily_intention_text=intention.daily_intention_text,
        target_quantity=intention.target_quantity,
        completed_quantity=intention.completed_quantity,
        focus_block_count=intention.focus_block_count,
        completion_percentage=completion_percentage, # Use the calculated value
        status=intention.status,
        created_at=intention.created_at,
        ai_feedback=intention.ai_feedback
    )

@app.patch("/intentions/today/progress", response_model=schemas.DailyIntentionResponse)
def update_daily_intention_progress(
    progress_data: schemas.DailyIntentionUpdate,
    intention: Annotated[models.DailyIntention, Depends(get_current_user_daily_intention)],
    db: Session = Depends(database.get_db),
):
    """
    Updates Daily Intention progress for the currently logged in user - the core of the Daily Execution Loop!
    - User reports progress after each Focus Block
    - System calculates completion percentage
    - Determines if intention is completed, in progress or failed
    """
    # Strict Forward Progress: Users should not be able to report less progress than already recorded
    if progress_data.completed_quantity < intention.completed_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot report less progress than you have already recorded."
        )

    try:
        # Update progress: absolute, not incremental! Simpler mental model - "Where am I vs my goal?"
        intention.completed_quantity = min(progress_data.completed_quantity, intention.target_quantity)
        if intention.completed_quantity >= intention.target_quantity:
            intention.status = 'completed'
        elif intention.completed_quantity > 0:
            intention.status = 'in_progress'
        else:
            intention.status = 'pending'

        db.commit()
        db.refresh(intention)

        # Calculate completion percentage
        completion_percentage = (
            (intention.completed_quantity / intention.target_quantity) * 100
            if intention.target_quantity > 0 else 0.0
        )

        return schemas.DailyIntentionResponse(
            id=intention.id,
            user_id=intention.user_id,
            daily_intention_text=intention.daily_intention_text,
            target_quantity=intention.target_quantity,
            completed_quantity=intention.completed_quantity,
            focus_block_count=intention.focus_block_count,
            completion_percentage=completion_percentage, # Use the calculated value
            status=intention.status,
            created_at=intention.created_at
        )
    
    except Exception as e:
        print(f"Database error: {e}") 
        db.rollback()  # Roll back on any error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Daily Intention progress: {str(e)}"
        )
    
@app.patch("/intentions/today/complete", response_model=schemas.DailyIntentionResponse)
def complete_daily_intention(
    daily_intention: Annotated[models.DailyIntention, Depends(get_current_user_daily_intention)],
    db: Session = Depends(database.get_db)
    ):
    """
    Mark today's Daily Intention for the currently logged in user as completed
    
    This triggers:
    - XP gain for the user
    - Discipline stat increase
    - Streak continuation
    """
    # The dependency guarantees Daily Intention that belongs to the currently logged in user
    
    try:
        # Mark as completed
        daily_intention.status = 'completed'
        daily_intention.completed_quantity = daily_intention.target_quantity  # Ensure full completion

        db.commit()
        db.refresh(daily_intention)

        return schemas.DailyIntentionResponse(
            id=daily_intention.id,
            user_id=daily_intention.user_id,
            daily_intention_text=daily_intention.daily_intention_text,
            target_quantity=daily_intention.target_quantity,
            completed_quantity=daily_intention.completed_quantity,
            focus_block_count=daily_intention.focus_block_count,
            completion_percentage=100.0,  # Fully completed
            status=daily_intention.status,
            created_at=daily_intention.created_at
        )
    
    except Exception as e:
        print(f"Database error: {e}") 
        db.rollback()  # Roll back on any error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete Daily Intention: {str(e)}"
        )
    
@app.patch("/intentions/today/fail", response_model=schemas.DailyIntentionResponse)
def fail_daily_intention(
    daily_intention: Annotated[models.DailyIntention, Depends(get_current_user_daily_intention)],
    db: Session = Depends(database.get_db)
    ):
    """
    Mark today's Daily Intention for the currently logged in user as failed
    
    This triggers the "Fail Forward" mechanism!
    - AI feedback on failure in order to re-frame failure
    - AI generates and initiates Recovery Quest
    - Opportunity to gain Resilience stat
    """
    # The dependency once again guarantees Daily Intention that belongs to the currently logged in user
    
    try:
        # Mark as failed
        daily_intention.status = 'failed'
        
        db.commit()
        db.refresh(daily_intention)

        # Calculate the final completion percentage
        completion_percentage = (
            (daily_intention.completed_quantity / daily_intention.target_quantity) * 100
            if daily_intention.target_quantity > 0 else 0.0
        )

        return schemas.DailyIntentionResponse(
            id=daily_intention.id,
            user_id=daily_intention.user_id,
            daily_intention_text=daily_intention.daily_intention_text,
            target_quantity=daily_intention.target_quantity,
            completed_quantity=daily_intention.completed_quantity,
            focus_block_count=daily_intention.focus_block_count,
            completion_percentage=completion_percentage,  # Use the calculated percentage at the time of failure
            status=daily_intention.status,
            created_at=daily_intention.created_at
        )
    
    except Exception as e:
        print(f"Database error: {e}") 
        db.rollback()  # Roll back on any error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark Daily Intention as failed: {str(e)}"
        )
    
# FOCUS BLOCK ENDPOINTS

@app.post("/focus-blocks", response_model=schemas.FocusBlockResponse, status_code=status.HTTP_201_CREATED)
def create_focus_block(
    block_data: schemas.FocusBlockCreate, 
    daily_intention: Annotated[models.DailyIntention, Depends(get_current_user_daily_intention)],
    db: Session = Depends(database.get_db)):
    """
    Create a new Focus Block when the currently logged in user starts a timed execution sprint.
    Creates it by finding the user's active intention for the day.
    This logs the user's chunked-down intention for the block.
    NEW: Also ensures that the user has no other active Focus Blocks!
    """
    # The dependency has already guaranteed the currently logged in user's Daily Intention!
    
    # NEW: Enforce "One Active Block at a Time" rule
    existing_active_block = db.query(models.FocusBlock).filter(
        models.FocusBlock.daily_intention_id == daily_intention.id,
        models.FocusBlock.status.in_(['pending', 'in_progress'])
    ).first()

    if existing_active_block:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, # 409 Conflict is the perfect status code for this
            detail="You already have an active Focus Block. Please complete or update it before starting a new one."
        )
    
    # Create the new Focus Block instance if the check passes using the ID from the found intention
    new_block = models.FocusBlock(
        daily_intention_id=daily_intention.id,
        focus_block_intention=block_data.focus_block_intention,
        duration_minutes=block_data.duration_minutes
    )

    try:
        db.add(new_block)
        db.commit()
        db.refresh(new_block)
        return new_block
    except Exception as e:
        print(f"Database error on Focus Block creation: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Focus Block: {str(e)}"
        )
    
@app.patch("/focus-blocks/{block_id}", response_model=schemas.FocusBlockResponse)
def update_focus_block(
    update_data: schemas.FocusBlockUpdate, 
    block: Annotated[models.FocusBlock, Depends(get_owned_focus_block)],
    stats: Annotated[models.CharacterStats, Depends(get_current_user_stats)],
    db: Session = Depends(database.get_db)
    ):
    """
    Updates a Focus Block's status or video URLs.
    Awards XP upon completion by delegating to the service layer.
    """
    # The get_owned_focus_block dependency guarantees a Focus Block that belongs to the currently logged in user
    
    # This check ensures the block is from today, preserving the game's integrity.
    today = datetime.now(timezone.utc).date()
    if block.created_at.date() != today:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This Focus Block is from a previous day and can no longer be updated."
        )

    try:
        # Flag to track if we need to commit stats changes
        xp_awarded = 0

        # Check if the block is being marked as completed for the first time
        if update_data.status == "completed" and block.status != "completed":
            # Delegate completion logic and xp gain to the service layer
            completion_result = services.complete_focus_block(db=db, user=stats.user, block=block)
            # Get the result from the service
            xp_awarded = completion_result.get("xp_awarded", 0)

        # Update the block's data from the request payload
        if update_data.status is not None:
            block.status = update_data.status.strip()
        if update_data.pre_block_video_url is not None:
            block.pre_block_video_url = update_data.pre_block_video_url
        if update_data.post_block_video_url is not None:
            block.post_block_video_url = update_data.post_block_video_url
        
        # Apply stat changes from the service call
        if xp_awarded > 0:
            stats.xp += xp_awarded

        db.commit()
        db.refresh(block)
        if xp_awarded > 0:
            db.refresh(stats)
            
        return block

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Focus Block: {str(e)}"
        )


# DAILY RESULTS ENDPOINTS

@app.post("/daily-results", response_model=schemas.DailyResultResponse, status_code=status.HTTP_201_CREATED)
def create_daily_result(
    current_user: Annotated[models.User, Depends(security.get_current_user)],
    daily_intention: Annotated[models.DailyIntention, Depends(get_current_user_daily_intention)],
    stats: Annotated[models.CharacterStats, Depends(get_current_user_stats)], 
    db: Session = Depends(database.get_db)
):
    """Creates the evening Daily Result and triggers reflection via the service layer."""
    # The get_current_user_daily_intention dependency guarantees a Daily Intention from the currently logged in user
    
    # Check if Daily Result already exists for this intention
    existing_result = db.query(models.DailyResult).filter(
        models.DailyResult.daily_intention_id == daily_intention.id
    ).first()
    if existing_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daily Result already exists for this intention. Sacred finality!"
        )
    
    # 1. Call the service to get the logic result
    reflection_data = services.create_daily_reflection(
        db=db, user=current_user, daily_intention=daily_intention
    )
    
    try:
        # 2. Use the data from the service to build the DB object
        db_result = models.DailyResult(
            daily_intention_id=daily_intention.id,
            succeeded_failed=reflection_data["succeeded"],
            ai_feedback=reflection_data["ai_feedback"],
            recovery_quest=reflection_data["recovery_quest"]
        )
        db.add(db_result)

        # 3. Update stats based on service output
        stats.discipline += reflection_data["discipline_stat_gain"]

        
        db.commit()
        db.refresh(db_result)
        db.refresh(stats)

        return db_result
    
    except Exception as e:
        print(f"Database error: {e}") 
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Daily Result: {str(e)}"
        )
    
@app.get("/daily-results/{intention_id}", response_model=schemas.DailyResultResponse)
def get_daily_result(
    # The dependency does all the work: finds the result AND verifies ownership.
    result: Annotated[models.DailyResult, Depends(get_owned_daily_result_by_intention_id)]
    ):
    """
    Get the Daily Result for a specific, user-owned intention.
    Used for disaplying reflection insights and Recovery Quests
    """
    # The 'result' object is guaranteed to be the correct, owned DailyResult.
    return result

@app.post("/daily-results/{result_id}/recovery-quest", response_model=schemas.RecoveryQuestResponse)
def respond_to_recovery_quest(
    quest_response: schemas.RecoveryQuestInput,
    result: Annotated[models.DailyResult, Depends(get_owned_daily_result_by_result_id)],
    stats: Annotated[models.CharacterStats, Depends(get_current_user_stats)],
    current_user: Annotated[models.User, Depends(security.get_current_user)], # Added for the service call
    db: Session = Depends(database.get_db)
):
    """Submits user's reflection on a failed day and receives AI coaching via the service layer."""
    
    # --- PRE-CONDITION CHECKS ---
    # The dependency already found the user-owned DailyResult.
    
    # Check if Recovery Quest exists; business logic check specific to this endpoint
    if not result.recovery_quest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Recovery Quest available for this result."
        )
    
    # Check if a response has already been submitted
    if result.recovery_quest_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A response for this Recovery Quest has already been submitted."
        )
        
    # --- LOGIC DELEGATION ---
    try:
        # 1. DELEGATE: Call the service to get the simulated AI coaching and stat gains
        coaching_data = services.process_recovery_quest_response(
            db=db,
            user=current_user,
            result=result,
            response_text=quest_response.recovery_quest_response
        )

        # 2. UPDATE STATE: Apply the user's input and the service's results to the models
        result.recovery_quest_response = quest_response.recovery_quest_response.strip()
        stats.resilience += coaching_data.get("resilience_stat_gain", 0)

        # 3. COMMIT: Save the changes to the database
        db.commit()
        db.refresh(result)
        db.refresh(stats)

        # 4. RESPOND: Return the data, using the coaching feedback from the service
        return schemas.RecoveryQuestResponse(
            recovery_quest_response=result.recovery_quest_response,
            ai_coaching_feedback=coaching_data["ai_coaching_feedback"]
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to respond to Recovery Quest: {str(e)}"
        )
