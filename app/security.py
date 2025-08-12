import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .crud import get_user # To look up users in the database
from .database import get_db # Import our db session generator
from .schemas import TokenData # Import our token payload schema

# This object is what FastAPI uses to extract the token from the request header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- JWT (Token) Handling ---
# In production, load this from an env variable
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # A JWT token is valid for 30 minutes

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default expiration time in none is provided
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    # The 'sub' (subject) claim is standard for storing the user identifier
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    """
    The "Wristband Checker". A dependency that:
    1. Takes a token from the request's Authorization header.
    2. Validates and decodes it.
    3. Fetches the user from the database.
    4. Returns the user object if valid, or raises an error.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        # We validate that the payload has the data shape we expect
        token_data = TokenData(user_id=user_id)
    except JWTError: # Catches any error from jose: expiration, invalid signature, etc.
        raise credentials_exception
    
    # We have a valid token, now get the user from the DB
    user = get_user(db, user_id=int(token_data.user_id))

    if user is None: # In the rare case where the user might have been deleted after the token was issued
        raise credentials_exception
    
    # Return the full, valid, trusted user
    return user