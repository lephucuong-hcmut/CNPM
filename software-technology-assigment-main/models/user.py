from beanie import Document
from pydantic import BaseModel
from typing import Dict, Optional

class CreateUserRequest(BaseModel):
    user_name: str
    email: str
    phone_number: str
    password: str

class User(Document):
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    email:  Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    ext_fields: Optional[Dict] = {}

    class Settings:
        name = "User"

