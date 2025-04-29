from beanie import Document
from pydantic import BaseModel
from typing import Optional


class CreateRoomRequest(BaseModel):
    room_id: str
    capacity: int


class UpdateRoomRequest(BaseModel):
    room_id: Optional[str] = None
    capacity: Optional[int] = None
    current_reserved_by:  Optional[str] = None
    current_reserved_by_user_id: Optional[str] = None


class Room(Document):
    room_id: Optional[str] = None
    capacity: Optional[int] = None
    room_state: Optional[str] = None
    current_reserved_by_booking_id:  Optional[str] = None
    current_reserved_by_user_id: Optional[str] = None

    class Settings:
        name = "Room"

