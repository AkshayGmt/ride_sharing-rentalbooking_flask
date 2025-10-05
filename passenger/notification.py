from socket_event import socketio

def notify_driver(driver, message):
    socketio.emit(
        "driver_notification",
        {"message": message},
        room=str(driver.id) if hasattr(driver, "id") else None
    )

def notify_passenger(passenger, message):
    socketio.emit(
        "passenger_notification",
        {"message": message},
        room=str(passenger.id) if hasattr(passenger, "id") else None
    )


# socket_event.py
from flask_socketio import SocketIO

# Create single instance (app will init_app it)
socketio = SocketIO(cors_allowed_origins="*")

def push_to_passenger(passenger_id, payload):
    """
    payload: dict with keys like {category,event,title,message,data}
    Passenger clients should join room "passenger:<id>"
    """
    room = f"passenger:{passenger_id}"
    socketio.emit("notification", payload, room=room)

# small helper wrappers for convenience
def notify_ride(passenger_id, event, title, message, data=None):
    push_to_passenger(passenger_id, {"category":"ride","event":event,"title":title,"message":message,"data":data or {}})

def notify_rental(passenger_id, event, title, message, data=None):
    push_to_passenger(passenger_id, {"category":"rental","event":event,"title":title,"message":message,"data":data or {}})

def notify_payment(passenger_id, event, title, message, data=None):
    push_to_passenger(passenger_id, {"category":"payment","event":event,"title":title,"message":message,"data":data or {}})
# utils/notifications.py
from admin.model import Notification


def create_notification(passenger_id, category, event, title, message, data=None, push=True):
    """
    Create notification record and optionally push via SocketIO.
    Returns Notification object.
    """
    #from utils.notifications import create_notification

# after booking saved, driver assigned
#     create_notification(
#   passenger_id=passenger_id,
#   category="ride",
#   event="ride_confirmed",
#   title="Ride Confirmed",
#   message=f"Driver {driver.name} assigned ({driver.vehicle_type} - {driver.vehicle_number}). ETA {eta_minutes} mins",
#   data={"ride_id": str(ride.id), "driver": {"id":str(driver.id),"name":driver.name,"vehicle":driver.vehicle_number}}
 #   )

    n = Notification(
        passenger_id=str(passenger_id),
        category=category,
        event=event,
        title=title,
        message=message,
        data=data or {}
    )
    n.save()
    if push:
        if category == "ride":
            notify_ride(passenger_id, event, title, message, data)
        elif category == "rental":
            notify_rental(passenger_id, event, title, message, data)
        elif category == "payment":
            notify_payment(passenger_id, event, title, message, data)
    return n



