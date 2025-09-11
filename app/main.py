from __future__ import annotations  # keep ForwardRef happy with annotation-handling

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Annotated
from dotenv import load_dotenv

# --- Internal package imports (namespaced) ---
from . import crud
from . import database
from . import security
from . import services
from . import utils
from . import models
from . import schemas

# Load environment variables
load_dotenv()

# FastAPI app setup
app = FastAPI(
    title="Game of Becoming API (Public Demo)",
    description="A demonstration of the backend architecture for a gamified productivity application.",
    version="2.0.0",
    docs_url="/docs"
)

# Configure CORS middleware
origins = [
    "http://localhost",
    "http://localhost:5173",
    # Frontend production URL to be added here after deployment
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # Utility functions
# def calculate_level(xp: int) -> int:
#     """Calculates user level based on total XP."""
#     if xp < 0:
#         return 1
#     return math.floor((xp / 100) ** 0.5) + 1
# We use calculated fields instead!

# --- ENDPOINT DEPENDENCIES ---

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

# --- GENERAL ENDPOINTS ---

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
        "version": "2.0.0"
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


# --- USER & ONBOARDING ENDPOINTS ---

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

@app.put("/users/me", response_model=schemas.UserResponse)
def update_user_me(user_data: schemas.UserUpdate, current_user: Annotated[models.User, Depends(security.get_current_user)], db: Session = Depends(database.get_db)):
    """The new onboarding endpoint."""
    try:
        current_user.hla = user_data.hla
        # This is the "ignition" that starts the streak at 1.
        services.update_user_streak(user=current_user)
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update user profile: {str(e)}")

@app.get("/users/me/stats", response_model=schemas.CharacterStatsResponse)
def get_my_character_stats(
    stats: Annotated[models.CharacterStats, Depends(get_current_user_stats)]
    ):
    """Get the character stats for the currently authenticated user."""
    # The response model now uses computed_field, so we can return the stats object directly!
    return stats

@app.get("/api/users/me/game-state", response_model=schemas.GameStateResponse)
async def get_game_state(
    current_user: Annotated[models.User, Depends(security.get_current_user)],
    db: Session = Depends(database.get_db)
):
    """
    The primary endpoint for the frontend to get all necessary data
    to render the user's current game state upon loading the app.
    """
    stats = crud.get_or_create_user_stats(db, current_user.id)
    todays_intention = crud.get_today_intention(db, current_user.id)
    unresolved_intention = crud.get_yesterday_incomplete_intention(db, current_user.id)

    # The "passive failure" path; user did nothing with yesterday's Daily Intention
    if unresolved_intention and not unresolved_intention.daily_result:
        unresolved_intention.status = 'failed' # Mark it as failed

        # Call existing service to generate the result and Recovery Quest
        reflection_data = await services.create_daily_reflection(
            db=db, user=current_user, daily_intention=unresolved_intention
        )

        new_result = models.DailyResult(
            daily_intention_id=unresolved_intention.id,
            succeeded_failed=False,
            ai_feedback=reflection_data["ai_feedback"],
            recovery_quest=reflection_data["recovery_quest"],
            xp_awarded=0,
            discipline_stat_gain=0
        )
        db.add(new_result)
        db.commit()
        db.refresh(unresolved_intention) # Refresh to load the new relationship

    # Pydantic now handles everything automatically thanks to our schema changes using computed_field
    return schemas.GameStateResponse(
        user=current_user,
        stats=stats,
        todays_intention=todays_intention,
        unresolved_intention=unresolved_intention
    )

@app.post("/api/onboarding/step", response_model=schemas.OnboardingV2Response)
async def handle_onboarding_step(
    step_data: schemas.OnboardingV2Request, # UPDATED: We now use the new V2 request schema
    current_user: Annotated[models.User, Depends(security.get_current_user)],
    db: Session = Depends(database.get_db)
):
    """
    Handles one step of the V2 AI-driven conversational onboarding flow.
    """
    try:
        response_data = await services.process_onboarding_step(db, current_user, step_data)
        
        # UPDATED: The logic now checks for the specific 'COMPLETE' step from our Enum
        if response_data.next_step == schemas.OnboardingStepName.COMPLETE:
            # When the conversation is over, we save the final HLA from the response
            # and officially start the user's streak.
            current_user.hla = response_data.final_hla
            services.update_user_streak(user=current_user)
            db.commit()

        return response_data

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during the onboarding process: {str(e)}"
        )

@app.post("/api/chat", response_model=schemas.ChatMessageResponse)
async def handle_chat_message(
    chat_input: schemas.ChatMessageInput,
    current_user: Annotated[models.User, Depends(security.get_current_user)],
    db: Session = Depends(database.get_db)
):
    """
    Handles a user's message to the general AI chat and returns a response.
    """
    try:
        # Call our new service function to get the AI's response
        ai_text = await services.generate_chat_response(
            db=db, user=current_user, message=chat_input.text
        )
        
        # We could add logic here to log the conversation to the database in the future
        # For now, we just return the response.

        return schemas.ChatMessageResponse(ai_response=ai_text)

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred with the AI chat."
        )


# --- DAILY INTENTION & EXECUTION LOOP ENDPOINTS ---

# Updated for Smart Detection! And now async!
@app.post("/api/intentions", response_model=schemas.IntentionCreationResponse, status_code=status.HTTP_200_OK) # No longer 201_CREATED!
async def create_daily_intention(
    intention_data: schemas.DailyIntentionCreate,
    current_user: Annotated[models.User, Depends(security.get_current_user)],
    stats: Annotated[models.CharacterStats, Depends(get_current_user_stats)],
    db: Session = Depends(database.get_db)
):
    """
    Handles the conversational creation of a Daily Intention.
    This endpoint is now a passthrough to the conversational service layer.
    """
    # 1. Check if today's Daily Intention for the currently logged in user already exists
    if crud.get_today_intention(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daily Intention already exists for today! Get going making progress on it!"
        )
    
    # 2. NEW: Delegate the entire conversational logic to the service layer.
    response = await services.create_and_process_intention(db, current_user, intention_data)

    # 3. NEW: If the conversation is complete, we now need to save the new intention. The needs_refinement flag is a thing of the past!
    if response.next_step == schemas.CreationStep.COMPLETE and response.intention_payload:
        try:
            # We can use the data from the final payload to create the DB object
            payload = response.intention_payload
            db_intention = models.DailyIntention(
                user_id=current_user.id,
                daily_intention_text=payload.daily_intention_text,
                target_quantity=payload.target_quantity,
                focus_block_count=payload.focus_block_count,
            )
            db.add(db_intention)
            stats.clarity += 1 # Award clarity for setting a good intention
            db.commit()
            db.refresh(db_intention)
            # We need to replace the placeholder ID in the payload with the real one
            response.intention_payload.id = db_intention.id

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save final intention: {e}")
            
    return response
            

@app.get("/api/intentions/today/me", response_model=schemas.DailyIntentionResponse)
def get_my_daily_intention(
    daily_intention: Annotated[models.DailyIntention, Depends(get_current_user_daily_intention)]
    ):
    """
    Get today's Daily Intention for the currently logged in user.
    The core of the Daily Commitment Screen!
    UPDATE: Now includes all associated Focus Blocks
    UPDATE: Now also potentially includes a Daily Result
    """

    # Now includes focus_blocks list. The 'intention.focus_blocks' attribute is already populated thanks
    # to our eager loading in crud.py. No extra database query is needed here
    # completion_percentage added automatically now thanks to our schema changes using computed_field
    # All we do is to simply return the Daily Intention from the dependency
    return daily_intention

@app.patch("/api/intentions/today/progress", response_model=schemas.DailyIntentionResponse)
def update_daily_intention_progress(
    progress_data: schemas.DailyIntentionUpdate,
    daily_intention: Annotated[models.DailyIntention, Depends(get_current_user_daily_intention)],
    db: Session = Depends(database.get_db),
):
    """
    Updates Daily Intention progress for the currently logged in user - the core of the Daily Execution Loop!
    - User reports progress after each Focus Block
    - System calculates completion percentage
    - Determines if intention is completed, in progress or failed
    """
    # Strict Forward Progress: Users should not be able to report less progress than already recorded
    if progress_data.completed_quantity < daily_intention.completed_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot report less progress than you have already recorded."
        )

    try:
        # Update progress: absolute, not incremental! Simpler mental model - "Where am I vs my goal?"
        daily_intention.completed_quantity = min(progress_data.completed_quantity, daily_intention.target_quantity)
        if daily_intention.completed_quantity >= daily_intention.target_quantity:
            daily_intention.status = 'completed'
        elif daily_intention.completed_quantity > 0:
            daily_intention.status = 'in_progress'
        else:
            daily_intention.status = 'pending'

        db.commit()
        db.refresh(daily_intention)

        # completion_percentage added automatically now thanks to our schema changes using computed_field
        return daily_intention
    
    except Exception as e:
        print(f"Database error: {e}") 
        db.rollback()  # Roll back on any error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Daily Intention progress: {str(e)}"
        )
    
    
# --- ATOMIC END-OF-DAY ENDPOINTS ---
@app.post("/api/intentions/today/complete", response_model=schemas.DailyResultCompletionResponse)
async def complete_daily_intention(
    daily_intention: Annotated[models.DailyIntention, Depends(get_current_user_daily_intention)],
    stats: Annotated[models.CharacterStats, Depends(get_current_user_stats)],
    db: Session = Depends(database.get_db)
    ):
    """
    Marks the Daily Intention as completed AND creates the corresponding Daily Result
    in a single, atomic operation.
    
    This triggers:
    - XP gain for the user
    - Discipline stat increase
    - Streak continuation; now implemented!
    """
    # The dependency guarantees Daily Intention that belongs to the currently logged in user

    if daily_intention.daily_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A result for this intention has already been created."
        )
    
    # Ensure the intention is actually ready to be completed
    if daily_intention.completed_quantity < daily_intention.target_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Intention progress is not yet complete."
        )
    
    try:
        # Mark as completed
        daily_intention.status = 'completed'

        # Call the service to get the reflection logic, Discipline stat gain and XP gain
        reflection_data = await services.create_daily_reflection(db=db, user=stats.user, daily_intention=daily_intention)
        discipline_gain = reflection_data.get("discipline_stat_gain", 0)
        xp_gain = reflection_data.get("xp_awarded", 0)

        # Create the DailyResult
        db_result = models.DailyResult(
            daily_intention_id=daily_intention.id,
            succeeded_failed=True, # Explicitly True
            ai_feedback=reflection_data["ai_feedback"],
            recovery_quest=None, # No recovery quest on success
            discipline_stat_gain=discipline_gain,
            xp_awarded=xp_gain # Save the XP gain to the database
        )
        db.add(db_result)

        # Update stats with BOTH rewards
        if discipline_gain > 0:
            stats.discipline += discipline_gain
        if xp_gain > 0:
            stats.xp += xp_gain

        # NEW: Streak implementation! This is a confirmed "successful action"
        services.update_user_streak(user=stats.user)

        # Explicitly add the user object to the session to ensure its changes are tracked 
        db.add(stats.user)

        # Commit all changes at once
        db.commit()
        db.refresh(db_result)
        db.refresh(stats)

        # We can't use schemas computed fields here since we've called the service layer
        # We manually construct the response with the calculated field using __dict__ and model_validate 
        response_data = db_result.__dict__
        response_data["xp_awarded"] = xp_gain
        response_data["discipline_stat_gain"] = discipline_gain

        return schemas.DailyResultCompletionResponse.model_validate(response_data)
    
    except Exception as e:
        print(f"Database error: {e}") 
        db.rollback()  # Roll back on any error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete Daily Intention: {str(e)}"
        )
    
@app.post("/api/intentions/today/fail", response_model=schemas.DailyResultCompletionResponse)
async def fail_daily_intention(
    daily_intention: Annotated[models.DailyIntention, Depends(get_current_user_daily_intention)],
    stats: Annotated[models.CharacterStats, Depends(get_current_user_stats)],
    db: Session = Depends(database.get_db)
    ):
    """
    Triggers the "Fail Forward" mechanism by marking the Daily Intention as
    failed AND creating the corresponding Daily Result in a single, atomic operation.
    
    - AI feedback on failure in order to re-frame failure
    - AI generates and initiates Recovery Quest
    - Opportunity to gain Resilience stat
    """
    # The dependency once again guarantees Daily Intention that belongs to the currently logged in user
    # But we still need to check if the Daily Intention already has a Daily Result
    if daily_intention.daily_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A Daily Result for this Daily Intention has alreayd been created."
        )
    
    try:
        # Mark as failed
        daily_intention.status = 'failed'

        # --- Start of new, integrated logic ---

        # 1. Call the service to get the reflection logic
        reflection_data = await services.create_daily_reflection(db=db, user=stats.user, daily_intention=daily_intention)
        discipline_gain = reflection_data.get("discipline_stat_gain", 0) # Should be 0 for failure
        xp_gain = reflection_data.get("xp_awarded", 0) # Should also be 0 for failure

        # 2. Create the DailyResult database object
        db_result = models.DailyResult(
            daily_intention_id=daily_intention.id,
            succeeded_failed=False, # Explicitly False for failure
            ai_feedback=reflection_data["ai_feedback"],
            recovery_quest=reflection_data["recovery_quest"],
            discipline_stat_gain=discipline_gain,
            xp_awarded=xp_gain
        )
        db.add(db_result)

        # 3. Update user stats (Discipline and XP shouldn't change, but this is good practice)
        if discipline_gain > 0:
            stats.discipline += discipline_gain
        if xp_gain > 0:
            stats.xp += xp_gain
        
        # Commit all changes at once (status change and new result)
        db.commit()
        db.refresh(db_result)
        db.refresh(stats)

        # We can't use schemas computed fields here since we've called the service layer
        # We manually construct the response with the calculated field using __dict__ and model_validate 
        response_data = db_result.__dict__
        response_data["xp_awarded"] = xp_gain
        response_data["discipline_stat_gain"] = discipline_gain

        return schemas.DailyResultCompletionResponse.model_validate(response_data)
    
    except Exception as e:
        print(f"Database error: {e}") 
        db.rollback()  # Roll back on any error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark Daily Intention as failed: {str(e)}"
        )
    
    
# --- FOCUS BLOCK ENDPOINTS ---

@app.post("/api/focus-blocks", response_model=schemas.FocusBlockResponse, status_code=status.HTTP_201_CREATED)
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

@app.patch("/api/focus-blocks/{block_id}", response_model=schemas.FocusBlockCompletionResponse)
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

        # We can't use schemas computed fields here since we've called the service layer
        # We manually construct the response with the calculated field using __dict__ and model_validate 
        response_data = block.__dict__
        response_data["xp_awarded"] = xp_awarded

        return schemas.FocusBlockCompletionResponse.model_validate(response_data)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Focus Block: {str(e)}"
        )


# --- DAILY RESULTS ENDPOINTS ---
# The old POST Daily Result creation endpoint /daily-results is no longer needed; 
# it is all taken care of by the /complete and /fail endpoints!

@app.get("/api/daily-results/{intention_id}", response_model=schemas.DailyResultResponse)
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

@app.post("/api/daily-results/{result_id}/recovery-quest", response_model=schemas.RecoveryQuestResponse)
async def respond_to_recovery_quest(
    quest_response: schemas.RecoveryQuestInput,
    result: Annotated[models.DailyResult, Depends(get_owned_daily_result_by_result_id)],
    stats: Annotated[models.CharacterStats, Depends(get_current_user_stats)],
    db: Session = Depends(database.get_db)
):
    """Submits user's reflection on a failed day and receives AI coaching via the service layer."""
    # The dependency already guarantees user-owned DailyResult.
    
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
        
    try:
        # Call the service to get the simulated AI coaching and stat gains
        coaching_data = await services.process_recovery_quest_response(
            db=db,
            user=stats.user,
            result=result,
            response_text=quest_response.recovery_quest_response
        )
        resilience_gain = coaching_data.get("resilience_stat_gain", 0)
        xp_awarded = coaching_data.get("xp_awarded", 0)

        # Apply the user's input and the service's results to the models
        result.recovery_quest_response = quest_response.recovery_quest_response.strip()
        result.xp_awarded = xp_awarded
        if resilience_gain > 0:
            stats.resilience += resilience_gain
        if xp_awarded > 0:
            stats.xp += xp_awarded
        
        # The user has successfully learned from failure. This is a "successful action",
        # so we call the Streak Guardian to preserve their streak.
        services.update_user_streak(user=stats.user)

        db.commit()
        db.refresh(result)
        if resilience_gain > 0:
            db.refresh(stats)
        if xp_awarded > 0:
            db.refresh(stats)

        # Return the data, using the coaching feedback from the service
        return schemas.RecoveryQuestResponse(
            recovery_quest_response=result.recovery_quest_response,
            ai_coaching_feedback=coaching_data["ai_coaching_feedback"],
            resilience_stat_gain=resilience_gain,
            xp_awarded=xp_awarded
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to respond to Recovery Quest: {str(e)}"
        )