from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from langchain_core.messages import HumanMessage
from app.database import SessionLocal
from app.models import ChatSession, User
from app.schemas import ChatRequest
from app.dependencies import get_optional_user,get_db
from app.services.chatbot import chatbot, get_character_info
from app.utils.memory import add_memory_to_db
from slowapi import Limiter
from slowapi.util import get_remote_address
import sqlite3

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# def get_internat_thread_id(char_id: str, thread_id: str, user_id: Optional[int]) -> str:
#     uid = str(user_id) if user_id else "guest"
#     return f"{uid}_{char_id}_{thread_id}"

# app/dependencies.py
def get_internal_thread_id(char_id: str, thread_id: str, user_identifier: str) -> str:
    # Ensure all parts are strings before joining
    return f"{str(user_identifier)}_{char_id}_{thread_id}"

# @router.post("/chat/{char_id}/{thread_id}")
# @limiter.limit("10/minute")
# async def chat(request : Request,char_id: str,thread_id: str, sms: ChatRequest,x_guest_id: Optional[str] = Header(None, alias="X-Guest-ID"), user : Optional[User] = Depends(get_optional_user)):
#     db = SessionLocal()
    
#     character_info = get_character_info(char_id)
#     user_db_id = user.id if user else None
#     if not character_info:
#         raise HTTPException(status_code=404, detail="Character not found in database")
        

#     db = SessionLocal()
#     try:
#         internal_id = get_internat_thread_id(char_id, thread_id, user_db_id)

#         existing_session = db.query(ChatSession).filter(ChatSession.thread_id == internal_id).first()

#         if not existing_session:
#                     # CREATE NEW SESSION RECORD
#                     print(f"Creating new session record for {internal_id}")
#                     new_session = ChatSession(
#                         thread_id=internal_id,
#                         character_id=char_id,
#                         # FIXME: Still hardcoded to 1 (Admin) until we add Auth next!
#                         user_id=user_db_id, 
#                         created_at=datetime.utcnow(),
#                         last_message_at=datetime.utcnow()
#                     )
#                     db.add(new_session)

#         else:
#             existing_session.last_message_at = datetime.utcnow()

#             if existing_session.user_id is None and user_db_id is not None:
#                 existing_session.user_id = user_db_id
#         db.commit()

#     except Exception as e:
#         print(f"⚠️ DB Sync Warning: {e}")
#         db.rollback()
#     finally:
#         db.close()

#     internal_id = get_internat_thread_id(char_id, thread_id,user_db_id)
#     config = {"configurable": {"thread_id": internal_id, "char_id": char_id}}
    
#     # Create the new HumanMessage object
#     new_message = HumanMessage(content=sms.messages)
    
#     # Invoke the graph. 
#     # LangGraph will automatically:
#     # 1. Pull existing history from SQLite for this thread_id
#     # 2. Add this 'new_message' to that history
#     # 3. Pass the full list to your chat_node
#     response = chatbot.invoke(
#         {"messages": [new_message]}, 
#         config=config
#     )
#     ai_response_text = response["messages"][-1].content

#     if user_db_id:
#         print("saving to the vector DB")
#         add_memory_to_db(user_db_id,char_id,sms.messages,"user")
#         add_memory_to_db(user_db_id,char_id,ai_response_text,"ai")
    
#     # Return the AI's last response
#     return ai_response_text

@router.post("/chat/{char_id}/{thread_id}")
@limiter.limit("10/minute")
async def chat(
    request: Request,
    char_id: str,
    thread_id: str,
    sms: ChatRequest,
    x_guest_id: Optional[str] = Header(None, alias="X-Guest-ID"),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)  # Use the dependency injection!
):
    # 1. IDENTIFY THE USER (Real or Guest)
    if user:
        user_identifier = str(user.id)  # e.g., "5"
        user_db_id = user.id            # Integer for SQL Foreign Key
    else:
        user_identifier = x_guest_id or "guest_unknown" # e.g., "guest_8a7b"
        user_db_id = None               # SQL column stays NULL for guests

    # 2. VALIDATE CHARACTER
    # (Optional: You might want to move this check to a dependency or simple query)
    character_info = get_character_info(char_id)
    if not character_info:
        raise HTTPException(status_code=404, detail="Character not found")

    # 3. GENERATE UNIQUE INTERNAL ID
    # This ensures Guest A and Guest B have totally different chat histories
    # internal_id becomes: "guest_8a7b_char1_thread1" OR "5_char1_thread1"
    internal_id = get_internal_thread_id(char_id, thread_id, user_identifier)

    # 4. SYNC WITH SQL DATABASE (Session Tracking)
    try:
        existing_session = db.query(ChatSession).filter(ChatSession.thread_id == internal_id).first()

        if not existing_session:
            print(f"📝 Creating new session record for {internal_id}")
            new_session = ChatSession(
                thread_id=internal_id,
                character_id=char_id,
                user_id=user_db_id,  # Will be None for guests (Correct!)
                created_at=datetime.utcnow(),
                last_message_at=datetime.utcnow()
            )
            db.add(new_session)
        else:
            # Update timestamp
            existing_session.last_message_at = datetime.utcnow()
            # If a guest logs in later, claim the session (Optional feature)
            if existing_session.user_id is None and user_db_id is not None:
                existing_session.user_id = user_db_id
        
        db.commit()
    except Exception as e:
        print(f"⚠️ DB Sync Warning: {e}")
        db.rollback()
    
    # 5. RUN AI (LangGraph)
    config = {"configurable": {"thread_id": internal_id, "char_id": char_id}}
    
    new_message = HumanMessage(content=sms.messages)
    
    response = chatbot.invoke(
        {"messages": [new_message]}, 
        config=config
    )
    ai_response_text = response["messages"][-1].content

    # 6. SAVE TO VECTOR MEMORY (RAG)
    # We now save memory for BOTH logged-in users AND guests
    print(f"🧠 Saving memory for: {user_identifier}")
    add_memory_to_db(user_identifier, char_id, sms.messages, "user")
    add_memory_to_db(user_identifier, char_id, ai_response_text, "ai")
    
    return ai_response_text

@router.get("/chat/{char_id}/{thread_id}")
async def get_messages_by_thread_id(char_id: str, thread_id: str,user: Optional[User] = Depends(get_optional_user)):
    user_db_id = user.id if user else None
    internal_id = get_internal_thread_id(char_id, thread_id,user_db_id)

    history = chatbot.get_state(config={"configurable": {"thread_id": internal_id, "char_id": char_id}})
    print(history)
    if not history[0]:
        return {"message": "No history found for this character/thread pair."}
    return history.values["messages"]

@router.delete("/chat/{char_id}/{thread_id}")
async def delete_messages_by_thread_id(char_id : str,thread_id: str,user: Optional[User] = Depends(get_optional_user)):
    user_db_id = user.id if user else None
    internal_id = get_internal_thread_id(char_id, thread_id,user_db_id)

    # chatbot.delete_state(config={"configurable": {"thread_id": internal_id}})
    # Note: We need to access the connection from somewhere. 
    # In the original code, 'conn' was global.
    # Here, we can create a new connection or import it.
    # Since 'chatbot' service has its own connection, we might need to expose it or create a new one.
    # For safety, let's create a new connection here to the same DB file.
    conn = sqlite3.connect('./character_ai.db', check_same_thread=False)
    cursor = conn.cursor()


    try:
        cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (internal_id,))
        deleted_counts = cursor.rowcount
# 2. Try to cleanup 'checkpoint_blobs' (Ignore if it doesn't exist)
        try:
            cursor.execute("DELETE FROM checkpoint_blobs WHERE thread_id = ?", (internal_id,))
        except sqlite3.OperationalError:
            pass # Table doesn't exist? No problem.

        # 3. Try to cleanup 'checkpoint_writes' (Ignore if it doesn't exist)
        try:
            cursor.execute("DELETE FROM checkpoint_writes WHERE thread_id = ?", (internal_id,))
        except sqlite3.OperationalError:
            pass # Table doesn't exist? No problem.
        
        conn.commit()

        if deleted_counts == 0:
            return {"message":"History not found to delete or history already has been deleted"}
        else:
            return {"message":f"Chat history for {char_id} (Thread {thread_id}) has been deleted."}
        
    except sqlite3.Error as e:
            return {"error": f"An database error occurred: {e}"}
    finally:
        conn.close()
