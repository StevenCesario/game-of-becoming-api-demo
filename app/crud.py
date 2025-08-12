from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from .models import User, UserAuth, CharacterStats, DailyIntention
from .schemas import UserCreate
from .utils import get_password_hash

def create_user(db: Session, user_data: UserCreate) -> User:
    """Creates a new user and all associated records in a single transaction"""
    # Create the User record
    new_user = User(
        name=user_data.name.strip(),
        email=user_data.email.strip(),
        hrga=user_data.hrga.strip()
    )
    db.add(new_user)
    db.flush() # Assigns ID without committing

    # Create the UserAuth record
    user_auth = UserAuth(
        user_id=new_user.id,
        password_hash=get_password_hash(user_data.password.strip())
    )
    db.add(user_auth)

    # Create the CharacterStats record
    new_stats = CharacterStats(user_id=new_user.id)
    db.add(new_stats)

    # We don't commit here! The endpoint will handle the commit/rollback
    return new_user

def get_user(db: Session, user_id: int) -> User | None:
    """Get a user by their unique ID. Returns None if not found"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> User | None:
    """Get a user by email. Returns None if not found."""
    return db.query(User).filter(User.email == email).first()

def get_or_create_user_stats(db: Session, user_id: int) -> CharacterStats:
    """Fetches a user's stats, creating a new record if one doesn't exist"""
    stats = db.query(CharacterStats).filter(CharacterStats.user_id == user_id).first()
    if not stats:
        stats = CharacterStats(user_id=user_id)
        db.add(stats)
        # We don't commit here; we let the calling fuction handle the commit!
    return stats

def get_today_intention(db: Session, user_id: int) -> DailyIntention | None:
    """Get today's Daily Intention for a user. Returns None if not found."""
    today = datetime.now(timezone.utc).date()
    return db.query(DailyIntention).filter(
        DailyIntention.user_id == user_id,
        DailyIntention.created_at >= datetime.combine(today, datetime.min.time()),
        DailyIntention.created_at < datetime.combine(today + timedelta(days=1), datetime.min.time())
    ).first()