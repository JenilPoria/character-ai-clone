from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    characters = relationship("Character", back_populates="creator")

class Character(Base):
    __tablename__ = "characters"
    id = Column(String, primary_key=True, index = True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    prompt_data = Column(JSON)
    creator = relationship("User", back_populates="characters")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    thread_id = Column(String, primary_key=True, index=True)
    character_id = Column(String, ForeignKey("characters.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    character = relationship("Character")
    user = relationship("User")
