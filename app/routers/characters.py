from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Character, ChatSession, User
from app.schemas import CharacterCreateRequest, CharacterUpdateREquest
from app.dependencies import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()

# Note: Limiter needs to be initialized in main and passed here or used via dependency if we want global limiter.
# For now, I will re-instantiate a limiter or assume it's attached to app state if I were using the extension pattern.
# But since the original code used a global limiter variable, I'll create a local one or import it if I had a common place.
# Better approach: Create a common limiter in dependencies or utils.
# For this refactor, I will create a simple limiter instance here to match functionality, 
# but ideally it should be shared.
# Actually, let's put the limiter in dependencies or a new core module.
# For now, I'll just import get_remote_address and create a limiter.
limiter = Limiter(key_func=get_remote_address)

@router.get("/chat/all_characters")
def get_characters():
    db = SessionLocal()
    try: 
        characters = db.execute(select(Character)).scalars().all()

        char_list = []
    
        for char in characters:

            char_list.append({
                "id": char.id,
                "name": char.name,
                "prompt_data": char.prompt_data
            })
        return char_list
    finally:
        db.close() 


@router.post("/create-character")
@limiter.limit("5/minute")
async def create_character(request : Request,character : CharacterCreateRequest, current_user : User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        existing_char = db.query(Character).filter(Character.id == character.char_id).first()
        if existing_char:
            raise HTTPException(status_code=400,detail="The Character ID is already exists")
        
        new_char = Character(
            id = character.char_id.lower(),
            name = character.name.upper(),
            prompt_data = character.prompt_data.dict(),
            creator_id = current_user.id

        )
        db.add(new_char)
        db.commit()
        db.refresh(new_char)

        return {"message": f"Character '{character.name}' created successfully!", "id": character.char_id}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/character/delete-character/{char_id}")
async def delete_character(char_id: str, current_user: User = Depends(get_current_user)):
    db = SessionLocal() # Ensure this matches your import spelling
    try:
        # 1. Fetch the character first
        character = db.query(Character).filter(Character.id == char_id).first()

        # 2. CRITICAL FIX: Check if character exists BEFORE accessing properties
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        # 3. Check Ownership
        if character.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only delete your own characters.")
        
        # 4. Delete linked Sessions first (Clean up)
        db.query(ChatSession).filter(ChatSession.character_id == char_id).delete()

        # 5. Delete the Character
        db.delete(character)
        db.commit()

        return {"message": f"Character '{character.name}' (ID: {char_id}) and their sessions have been deleted."}

    except Exception as e:
        db.rollback()
        # If the error is already an HTTP exception (like the 403 or 404 above), re-raise it
        if isinstance(e, HTTPException):
            raise e
        # Otherwise, it's a server error
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.patch("/character/update_character/{char_id}")
async def update_character(char_id : str, update_data : CharacterUpdateREquest,current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try: 
        character = db.query(Character).filter(Character.id == char_id).first()

        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
        if character.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update your own characters.")
        
        if update_data.name:
            character.name = update_data.name
        
        if update_data.prompt_data:
            # character.prompt_data = update_data.prompt_data
            current_data = dict(character.prompt_data)
            current_data.update(update_data.prompt_data)
            character.prompt_data = current_data
        db.commit()
        db.refresh(character)

        return {
            "message": f"Character '{char_id}' updated successfully.",
            "updated_name": character.name,
            "updated_prompt": character.prompt_data
        }
    
    except Exception as e:
        db.rollback()
        # 1. If it is already a specific error (403 or 404), let it pass through!
        if isinstance(e, HTTPException):
            raise e
        # 2. Only turn unexpected errors into 500
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
