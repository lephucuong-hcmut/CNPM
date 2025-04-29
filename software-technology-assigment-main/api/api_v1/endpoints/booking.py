from fastapi import APIRouter, HTTPException, Header
from models.booking import CreateBookingRequest, UpdateBookingRequest, Booking
from models.room import Room
from models.user import User
from const import RoomState, BookingState
from typing import List, Dict, Tuple
import random
from datetime import datetime, timedelta
import random
import qrcode
import base64
import json
from io import BytesIO
import pytz
from fastapi import Query
from pydantic import BaseModel

def get_period_time_range(period: int) -> Tuple[int, int]:
    """
    Convert period number to actual time range (24-hour format)
    Period 1: 6:00-7:00
    Period 2: 7:00-8:00
    ...and so on
    """
    start_hour = 5 + period  # Period 1 starts at 6:00
    end_hour = start_hour + 1
    return start_hour, end_hour

def is_valid_booking_time(date: str, periods: List[int]) -> bool:
    """
    Check if the booking time is valid based on current time in GMT+7
    - Can't book past periods
    - Can't book periods that start in less than 15 minutes
    """
    try:
        # Set timezone to GMT+7
        gmt7 = pytz.timezone('Asia/Bangkok')
        current_time = datetime.now(gmt7)
        
        booking_date = datetime.strptime(date, "%Y-%m-%d")
        # Convert booking date to GMT+7 timezone
        booking_date = gmt7.localize(booking_date)
        
        # Can't book past dates
        if booking_date.date() < current_time.date():
            return False
            
        # If booking for future date, it's valid
        if booking_date.date() > current_time.date():
            return True
            
        # For today's booking, check each period
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        for period in periods:
            start_hour, end_hour = get_period_time_range(period)
            # If the period starts in less than 15 minutes or has already started, it's invalid
            # if start_hour <= current_hour or (current_hour == start_hour - 1 and current_minute > 45):
            if end_hour <= current_hour or (current_hour == end_hour & current_minute > 0):
                return False
                
        return True
    except:
        return False

def get_current_period() -> int:
    """
    Get current period number based on current time
    Returns 0 if current time is not in any period
    """
    current_hour = datetime.now().hour
    if 6 <= current_hour <= 17:  # We have periods from 6AM to 6PM  
        return current_hour - 5  # 6AM is period 1
    return 0


router = APIRouter(prefix="/booking")


@router.post(
    "/{room_id}",
    response_model=Booking
)
async def create_booking_room(
    room_id: str,
    create_booking_request: CreateBookingRequest,
):
    try:
        # Validate booking time
        if not is_valid_booking_time(create_booking_request.date, create_booking_request.selected_periods):
            raise HTTPException(
                status_code=400,
                detail="Invalid booking time. Cannot book past periods"
            )

        # Get room and check if it's available
        room = await Room.find_one(Room.room_id == room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        if room.room_state != RoomState.AVAILABLE:
            raise HTTPException(status_code=400, detail="Room is not available for booking")

        # Check if room is already booked for the requested date and periods
        existing_bookings = await Booking.find({
            "room_id": room_id,
            "date": create_booking_request.date,
            "status": {"$in": [BookingState.PENDING, BookingState.IN_USE]}
        }).to_list()

        # Check for period conflicts
        requested_periods = set(create_booking_request.selected_periods)
        for booking in existing_bookings:
            existing_periods = set(booking.selected_periods)
            if requested_periods & existing_periods:  # If there's any overlap
                status_text = "in use" if booking.status == BookingState.IN_USE else "booked"
                raise HTTPException(
                    status_code=400,
                    detail=f"Room is already {status_text} for some of the booked/in_use"
                )

        # Create new booking
        booking_data = create_booking_request.dict()
        booking_data["room_id"] = room_id  # Override room_id from path parameter
        
        booking = Booking(
            **booking_data,
            booking_id=str(random.randint(1000000, 9999999)),
            status=BookingState.PENDING,
        )
        await booking.save()

        # Generate QR code
        qr_data = f"{booking.booking_id}|{booking.email}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert QR code to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # Add QR code to booking
        booking.qr_code = qr_base64
        await booking.save()

        return booking
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{booking_id}",
    response_model=Booking
)
async def update_booking_room(
    booking_id: str,
    update_booking_request: UpdateBookingRequest,
):
    try:
        # Get booking by ID
        booking = await Booking.find_one(Booking.booking_id == booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        # Update booking with new data
        update_data = update_booking_request.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(booking, key, value)

        await booking.save()
        return booking
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{room_id}",
    response_model=List[Booking]
)
async def get_list_booking_of_room(
    room_id: str
):
    try:
        # Get all bookings for specific room
        bookings = await Booking.find({"room_id": room_id}).to_list()
        return bookings
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/cancel/{booking_id}",
    response_model=Booking
)
async def cancel_booking(
    booking_id: str,
):
    try:
        # Get booking by ID
        booking = await Booking.find_one(Booking.booking_id == booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        # Check if booking can be cancelled (not already cancelled)
        if booking.status == BookingState.CANCELLED:
            raise HTTPException(status_code=400, detail="Booking is already cancelled")

        # Update booking status to cancelled
        booking.status = BookingState.CANCELLED
        await booking.save()
        return booking
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/detail/{booking_id}",
    response_model=Booking
)
async def get_booking_detail(
    booking_id: str,
):
    try:
        booking = await Booking.find_one(Booking.booking_id == booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/user/{student_id}",
    response_model=List[Booking]
)
async def get_user_bookings(
    student_id: str,
):
    try:
        bookings = await Booking.find({"student_id": student_id}).to_list()
        return bookings
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/calendar/user")
async def get_user_calendar(email: str):
    try:
        # Get all active bookings (both pending and in-use) for the user
        query = {
            "email": email,
            "status": {"$in": [BookingState.PENDING, BookingState.IN_USE, BookingState.COMPLETED, BookingState.CANCELLED, BookingState.EXPIRED]}
        }
        
        bookings = await Booking.find(query).to_list()
        
        # Format data for calendar view
        calendar_data = []
        for booking in bookings:
            # Get room details
            room = await Room.find_one(Room.room_id == booking.room_id)
            room_name = f"Room {booking.room_id}" if not room else f"Room {room.room_id} (Capacity: {room.capacity})"
            
            calendar_event = {
                "date": booking.date,
                "room_id": booking.room_id,
                "room_name": room_name,
                "room_state": room.room_state if room else None,
                "booking_id": booking.booking_id,
                "purpose": booking.purpose,
                "selected_periods": booking.selected_periods,
                "student_name": booking.student_name,
                "status": booking.status,
                "email": booking.email,
                "qr_code": booking.qr_code if hasattr(booking, 'qr_code') else None
            }
            calendar_data.append(calendar_event)
        
        # Sort by date in descending order (newest first)
        calendar_data.sort(key=lambda x: x["date"], reverse=True)
        return calendar_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/checkin/{booking_id}",
    response_model=Booking
)
async def checkin_booking(
    booking_id: str,
    email: str,
):
    try:
        # Update booking status first
        await update_booking_status()

        # Get booking by ID
        booking = await Booking.find_one(Booking.booking_id == booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        # Verify user
        if booking.email != email:
            raise HTTPException(status_code=403, detail="This booking belongs to another user")

        # Check if booking is pending
        if booking.status != BookingState.PENDING:
            raise HTTPException(status_code=400, detail="Booking is not in pending state")

        # Check if current time is valid for checkin
        if not await is_valid_checkin_time(booking):
            raise HTTPException(
                status_code=400,
                detail="Cannot check in after the booking period has ended"
            )

        # Get room
        room = await Room.find_one(Room.room_id == booking.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # Update booking status
        booking.status = BookingState.IN_USE
        await booking.save()

        return booking
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/checkout/{booking_id}",
    response_model=Booking
)
async def checkout_booking(
    booking_id: str,
    email: str,
):
    try:
        # Update booking status first
        await update_booking_status()

        # Get booking by ID
        booking = await Booking.find_one(Booking.booking_id == booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        # Verify user
        if booking.email != email:
            raise HTTPException(status_code=403, detail="This booking belongs to another user")

        # Check if booking is in use
        if booking.status != BookingState.IN_USE:
            raise HTTPException(status_code=400, detail="Booking is not in use")

        # Update booking status
        booking.status = BookingState.COMPLETED
        await booking.save()

        return booking
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profile/{email}")
async def get_user_profile(email: str):
    try:
        user = await User.find_one(User.email == email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "user_name": user.user_name,
            "email": user.email,
            "phone_number": user.phone_number
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class QRData(BaseModel):
    qr_code: str

async def is_valid_checkin_time(booking: Booking) -> bool:
    """
    Check if current time is valid for checkin:
    - Must be on booking date
    - Must be before the end of the last period
    """
    try:
        # Get current time in GMT+7
        gmt7 = pytz.timezone('Asia/Bangkok')
        current_time = datetime.now(gmt7)
        current_date = current_time.strftime("%Y-%m-%d")
        
        # Must be on booking date
        if current_date != booking.date:
            return False
            
        # Get the latest period in the booking
        latest_period = max(booking.selected_periods)
        start_hour, end_hour = get_period_time_range(latest_period)
        
        # Current time must be before the end of the last period
        if current_time.hour > end_hour or (current_time.hour == end_hour and current_time.minute > 0):
            return False
            
        return True
    except:
        return False

async def update_booking_status():
    """
    Update booking status automatically:
    - If booking is PENDING and time is past the last period, set to EXPIRED
    - If booking is IN_USE and time is past the last period, set to COMPLETED
    """
    try:
        # Get current time in GMT+7
        gmt7 = pytz.timezone('Asia/Bangkok')
        current_time = datetime.now(gmt7)
        current_date = current_time.strftime("%Y-%m-%d")
        
        # Find all active bookings (PENDING or IN_USE)
        active_bookings = await Booking.find({
            "status": {"$in": [BookingState.PENDING, BookingState.IN_USE]}
        }).to_list()
        
        for booking in active_bookings:
            # Skip if booking is for future date
            if booking.date > current_date:
                continue
                
            # Get the latest period in the booking
            latest_period = max(booking.selected_periods)
            start_hour, end_hour = get_period_time_range(latest_period)
            
            # If current time is past the last period
            if current_time.hour > end_hour or (current_time.hour == end_hour and current_time.minute > 0):
                if booking.status == BookingState.PENDING:
                    booking.status = BookingState.EXPIRED
                elif booking.status == BookingState.IN_USE:
                    booking.status = BookingState.COMPLETED
                await booking.save()
                
    except Exception as e:
        print(f"Error updating booking status: {str(e)}")

@router.post(
    "/checkin-qr/qr",
    response_model=Booking
)
async def checkin_booking_by_qr(
    qr_data: QRData
):
    try:
        # Update booking status first
        await update_booking_status()

        # Split QR text into booking_id and email
        booking_id, email = qr_data.qr_code.split("|")

        # Get booking by ID
        booking = await Booking.find_one(Booking.booking_id == booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        # Verify user
        if booking.email != email:
            raise HTTPException(status_code=403, detail="This booking belongs to another user")

        # Check if booking is pending
        if booking.status != BookingState.PENDING:
            raise HTTPException(status_code=400, detail="Booking is not in pending state")

        # Check if current time is valid for checkin
        if not await is_valid_checkin_time(booking):
            raise HTTPException(
                status_code=400,
                detail="Cannot check in after the booking period has ended"
            )

        # Get room
        room = await Room.find_one(Room.room_id == booking.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # Update booking status
        booking.status = BookingState.IN_USE
        await booking.save()

        return booking
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid QR code format. Expected format: 'code|email'")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
