from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any

class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password(cls, v):
        if v == "string":
            raise ValueError("Password cannot be 'string'")
        return v

class ChatRequest(BaseModel):
    messages: str

class PromptData(BaseModel):
    CHAR_NAME: str
    CHAR_ROLE: str
    CHAR_AGE: str
    CHAR_APPEARANCE: str
    CHAR_PERSONALITY: str
    CHAR_BACKSTORY: str 
    SPEAKING_STYLE: str
    CHAR_QUIRKS: str
    CHAR_TONE: str
    CURRENT_SETTING: str
    USER_RELATIONSHIP: str
    CHAR_GOAL: str

class CharacterCreateRequest(BaseModel):
    char_id: str  # e.g. "batman"
    name: str     # e.g. "Batman"
    prompt_data: PromptData

class CharacterUpdateREquest(BaseModel):
    name : Optional[str] = None
    # We accept a Dictionary so they can update specific prompt fields
    # or replace the whole prompt blob.
    prompt_data : Optional[Dict[str,Any]]  = None
