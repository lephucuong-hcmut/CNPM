from fastapi import APIRouter, Header, HTTPException, Depends
from models.room import CreateRoomRequest, UpdateRoomRequest, Room
from models.booking import Booking
from const import RoomState, BookingState
from typing import List
from datetime import datetime
from ..deps import admin_required
from utils import decode_access_token

router = APIRouter(prefix="/room")


@router.post(
    "/",
    response_model=Room
)
async def create_room(
    create_room_request: CreateRoomRequest,
    user: dict = Depends(admin_required)
):
    try:
        # Check if room with same ID already exists
        existing_room = await Room.find_one(Room.room_id == create_room_request.room_id)
        if existing_room:
            raise HTTPException(status_code=400, detail="Room ID already exists")

        # Create new room with initial state as AVAILABLE
        room = Room(
            **create_room_request.dict(),
            room_state=RoomState.AVAILABLE,
            current_reserved_by_user_id=None,
            current_reserved_by_booking_id=None
        )
        await room.save()
        return room
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/",
    response_model=List[Room]
)
async def list_room():
    try:
        # Get all rooms
        rooms = await Room.find_all().to_list()
        return rooms
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/schedules"
)
async def get_room_schedules(
    date: str,
):
    try:
        rooms = await Room.find_all().to_list()
        room_schedules = []
        
        for room in rooms:
            # Initialize room schedule with all periods as available
            room_schedule = {
                "room_id": room.room_id,
                "status": [RoomState.AVAILABLE] * 12,  # 12 periods in a day
            }
            
            # Get all active bookings for this room on the specified date
            bookings = await Booking.find({
                "room_id": room.room_id,
                "date": date,
                "status": {"$in": [BookingState.PENDING, BookingState.IN_USE]}
            }).to_list()
            
            # Update status for each booking's selected periods
            for booking in bookings:
                for period in booking.selected_periods:
                    if booking.status == BookingState.IN_USE:
                        room_schedule["status"][period - 1] = RoomState.IN_USE
                    elif booking.status == BookingState.PENDING:
                        room_schedule["status"][period - 1] = RoomState.BOOKED
                    # COMPLETED and CANCELLED bookings will show as AVAILABLE (default state)
            
            room_schedules.append(room_schedule)
            
        return room_schedules
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{room_id}",
    response_model=Room
)
async def update_room(
    room_id: str,
    update_room_request: UpdateRoomRequest,
):
    try:
        # Get room by ID
        room = await Room.find_one(Room.room_id == room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # Don't allow updating room_id
        if "room_id" in update_room_request.dict(exclude_unset=True):
            raise HTTPException(status_code=400, detail="Cannot update room_id")

        # Update room with new data
        update_data = update_room_request.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(room, key, value)

        await room.save()
        return room
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{room_id}",
    response_model=dict
)
async def delete_room(
    room_id: str,
    user: dict = Depends(admin_required)
):
    try:
        # Get room by ID
        room = await Room.find_one(Room.room_id == room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # Check if room is in use
        if room.room_state == RoomState.IN_USE:
            raise HTTPException(status_code=400, detail="Cannot delete room that is in use")

        # Check if room has any future bookings
        current_date = datetime.now().strftime("%Y-%m-%d")
        future_bookings = await Booking.find({
            "room_id": room_id,
            "date": {"$gte": current_date},
            "status": BookingState.PENDING
        }).to_list()

        if future_bookings:
            raise HTTPException(status_code=400, detail="Cannot delete room with future bookings")

        # Delete room
        await room.delete()
        return {"message": "Room deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# @router.post(
#     "/checkin/{room_id}",
#     response_model=Room
# )
# async def checkin_room(
#     room_id: str,
#     user_id: str = Header(..., description="User ID"),
#     booking_id: str = Header(..., description="Booking ID"),
# ):
#     try:
#         # Get room by ID
#         room = await Room.find_one(Room.room_id == room_id)
#         if not room:
#             raise HTTPException(status_code=404, detail="Room not found")

#         # Get booking
#         booking = await Booking.find_one({
#             "booking_id": booking_id,
#             "student_id": user_id,
#             "room_id": room_id,
#             "status": BookingState.PENDING
#         })
#         if not booking:
#             raise HTTPException(status_code=404, detail="Booking not found")

#         # Check if room is available
#         if room.room_state != RoomState.AVAILABLE:
#             raise HTTPException(status_code=400, detail="Room is not available for check-in")

#         # Check if current time is within booking periods
#         current_time = datetime.now()
#         current_date = current_time.strftime("%Y-%m-%d")
#         current_period = (current_time.hour - 7) // 2 + 1  # Assuming periods start at 7:00 AM

#         if current_date != booking.date or current_period not in booking.selected_periods:
#             raise HTTPException(status_code=400, detail="Current time is not within booking periods")

#         # Update room state to IN_USE
#         room.room_state = RoomState.IN_USE
#         room.current_reserved_by_user_id = user_id
#         room.current_reserved_by_booking_id = booking_id
#         await room.save()
#         return room
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @router.post(
#     "/checkout/{room_id}",
#     response_model=Room
# )
# async def checkout_room(
#     room_id: str,
#     user_id: str = Header(..., description="User ID"),
#     booking_id: str = Header(..., description="Booking ID"),
# ):
#     try:
#         # Get room by ID
#         room = await Room.find_one(Room.room_id == room_id)
#         if not room:
#             raise HTTPException(status_code=404, detail="Room not found")

#         # Check if room is in use
#         if room.room_state != RoomState.IN_USE:
#             raise HTTPException(status_code=400, detail="Room is not in use")

#         # Verify user and booking
#         if room.current_reserved_by_user_id != user_id:
#             raise HTTPException(status_code=400, detail="User ID does not match current reservation")
#         if room.current_reserved_by_booking_id != booking_id:
#             raise HTTPException(status_code=400, detail="Booking ID does not match current reservation")

#         # Update room state to AVAILABLE
#         room.room_state = RoomState.AVAILABLE
#         room.current_reserved_by_user_id = None
#         room.current_reserved_by_booking_id = None
#         await room.save()
#         return room
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))