from datetime import date, datetime
from freezegun import freeze_time
from app import services
from app import models

@freeze_time("2025-08-27")
def test_update_user_streak_first_time():
    """Verify that the first successful action sets the streak to 1."""
    user = models.User()
    services.update_user_streak(user)
    assert user.current_streak == 1
    assert user.longest_streak == 1
    assert user.last_streak_update.date() == date(2025, 8, 27)

@freeze_time("2025-08-27")
def test_update_user_streak_continuation():
    """Verify a successful action on a consecutive day continues the streak."""
    user = models.User(current_streak=3, longest_streak=3, last_streak_update=datetime(2025, 8, 26))
    services.update_user_streak(user)
    assert user.current_streak == 4
    assert user.longest_streak == 4

@freeze_time("2025-08-27")
def test_update_user_streak_broken_chain():
    """Verify a streak is broken after one missed day."""
    user = models.User(current_streak=5, longest_streak=5, last_streak_update=datetime(2025, 8, 25))
    services.update_user_streak(user)
    assert user.current_streak == 1
    assert user.longest_streak == 5

@freeze_time("2025-08-27")
def test_update_user_streak_already_updated_today():
    """Verify multiple actions on the same day do not increase the streak."""
    user = models.User(current_streak=2, longest_streak=2, last_streak_update=datetime(2025, 8, 27))
    updated = services.update_user_streak(user)
    assert updated is False
    assert user.current_streak == 2