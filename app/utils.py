from passlib.context import CryptContext

# --- Password Hashing ---
# Create a CryptContext instance; tells passlib to use bcrypt for hasing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to verify a plain password against a hashed one
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to hash a plain password
def get_password_hash(password):
    return pwd_context.hash(password)