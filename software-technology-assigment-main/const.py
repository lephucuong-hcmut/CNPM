class RoomState:
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    BOOKED = "BOOKED"


class BookingState:
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    IN_USE = "IN_USE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"