from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.database import SessionLocal
from app.models import User
from app.schemas import UserCreate
from app.utils.auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

@router.post("/signup")
def signup(user : UserCreate):
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="The user already exists")
        
        # Hash the password
        hashed_pw = get_password_hash(user.password)

        new_user = User(
            username = user.username,
            hashed_password = hashed_pw
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "User created successfully", "username": new_user.username}
    
    finally: 
        db.close()

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == form_data.username).first()
    
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect username or Password", headers={"WWW-Authenticate":"Bearer"})
        
        # 3. Create Token
        access_token_expires = timedelta(minutes= ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    finally:
        db.close()
