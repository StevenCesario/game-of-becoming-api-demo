from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, joinedload

import app.models as models
import app.schemas as schemas
import app.utils as utils

def create_user(db: Session, user_data: schemas.UserCreate) -> models.User:
    """Creates a new user and all associated records in a single transaction"""
    # Create the User record
    new_user = models.User(
        name=user_data.name.strip(),
        email=user_data.email.strip(),
        hrga=user_data.hrga.strip()
    )
    db.add(new_user)
    db.flush() # Assigns ID without committing

    # Create the UserAuth record
    user_auth = models.UserAuth(
        user_id=new_user.id,
        password_hash=utils.get_password_hash(user_data.password.strip())
    )
    db.add(user_auth)

    # Create the CharacterStats record
    new_stats = models.CharacterStats(user_id=new_user.id)
    db.add(new_stats)

    # We don't commit here! The endpoint will handle the commit/rollback
    return new_user

def get_user(db: Session, user_id: int) -> models.User | None:
    """
    Get a user by their unique ID, and eagerly load their auth and stats.
    Returns None if not found.
    """
    return db.query(models.User).options(
        joinedload(models.User.auth),
        joinedload(models.User.character_stats)
    ).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> models.User | None:
    """Get a user by email. Returns None if not found."""
    return db.query(models.User).filter(models.User.email == email).first()

def get_or_create_user_stats(db: Session, user_id: int) -> models.CharacterStats:
    """Fetches a user's stats, creating a new record if one doesn't exist"""
    stats = db.query(models.CharacterStats).filter(models.CharacterStats.user_id == user_id).first()
    if not stats:
        stats = models.CharacterStats(user_id=user_id)
        db.add(stats)
        # We don't commit here; we let the calling fuction handle the commit!
    return stats

def get_today_intention(db: Session, user_id: int) -> models.DailyIntention | None:
    """Get today's Daily Intention for a user. Returns None if not found."""
    today = datetime.now(timezone.utc).date()
    return db.query(models.DailyIntention).filter(
        models.DailyIntention.user_id == user_id,
        models.DailyIntention.created_at >= datetime.combine(today, datetime.min.time()),
        models.DailyIntention.created_at < datetime.combine(today + timedelta(days=1), datetime.min.time())
    ).first()