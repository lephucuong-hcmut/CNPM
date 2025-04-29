from fastapi import APIRouter
from .endpoints.room import router as room_router
from .endpoints.booking import router as booking_router
from .endpoints.auth import router as auth_router

router = APIRouter()
router.include_router(room_router, tags=["Room Management"])
router.include_router(booking_router, tags=["Booking Management"])
router.include_router(auth_router, tags=["Authentication"])
