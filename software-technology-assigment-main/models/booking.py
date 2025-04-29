from beanie import Document
from pydantic import BaseModel
from typing import Optional, List

class CreateBookingRequest(BaseModel):
    room_id: str
    student_id: str
    student_name: str
    purpose: str
    selected_periods: List[int]
    date: str
    email: str
    phone: str


class UpdateBookingRequest(BaseModel):
    room_id: Optional[str] = None
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    purpose: Optional[str] = None
    selected_periods: Optional[List[int]] = None
    date: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None


class Booking(Document):
    booking_id: Optional[str] = None
    room_id: Optional[str] = None
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    purpose: Optional[str] = None
    selected_periods: Optional[List[int]] = None
    date: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    qr_code: Optional[str] = None  # Base64 encoded QR code

    class Settings:
        name = "Booking"