from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional
from app.database import SessionLocal
from app.models import User
from app.utils.auth import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        
async def get_current_user(token : str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail= "Could not Validate Credentials",
        headers = {"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, SECRET_KEY,algorithms=[ALGORITHM])
        username : str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception
        return user
    finally:
        db.close()

async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme_optional)):
    
    # CASE A: Guest (No Token)
    if not token:
        print("DEBUG AUTH: No token found. Guest Mode.")
        return None
    
    # CASE B: User (Token Found)
    # Note: 'token' is ALREADY the clean string. No .split() needed!
    try:
        print(f"DEBUG AUTH: Token received: {token[:10]}...")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            return None
        
        db = SessionLocal()
        user = db.query(User).filter(User.username == username).first()
        db.close()
        
        if user:
            print(f"DEBUG AUTH: Success! User is {user.username}")
            return user
            
    except Exception as e:
        print(f"DEBUG AUTH: Token Invalid -> {e}")
        return None
    
    return None
