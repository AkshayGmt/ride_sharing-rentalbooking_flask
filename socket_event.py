# socket_events.py
from flask_socketio import SocketIO, join_room, leave_room, emit
from datetime import datetime
from passenger.model.model import   ChatMessage
from driver.drivermodel import Driver
import os
from passenger.model.ride_model import RideBooking
socketio = SocketIO(cors_allowed_origins="*")  # init in app.py with app
from flask_socketio import SocketIO

# Only create socketio instance here

# Passenger or driver joins the ride room to get all events for that booking
@socketio.on("join_ride")
def on_join_ride(data):
    # data: { "ride_id": "<id>", "role": "passenger"|"driver", "user_id": "<id>" }
    ride_id = data.get("ride_id")
    join_room(ride_id)
    emit("system", {"msg": f"{data.get('role')} joined room"}, room=ride_id)

# Driver sends location update
@socketio.on("driver_location_update")
def on_driver_location(sid_data):
    # sid_data: { "ride_id": "...", "driver_id": "...", "lat": .., "lng": .., "speed": .. }
    ride_id = sid_data.get("ride_id")
    lat = sid_data.get("lat")
    lng = sid_data.get("lng")
    # Persist driver location on Driver doc (optional) and emit to room
    try:
        driver = Driver.objects.get(id=sid_data.get("driver_id"))
        driver.latitude = lat
        driver.longitude = lng
        driver.save()
    except Exception:
        pass
    # Emit to passenger(s) and driver in room
    emit("driver_location", {"lat": lat, "lng": lng, "ts": datetime.utcnow().isoformat()}, room=ride_id)

# Send chat messages
@socketio.on("send_message")
def on_send_message(data):
    # data: { "ride_id": "...", "sender": "passenger:xxx", "message": "..." }
    ride_id = data["ride_id"]
    sender = data["sender"]
    message = data["message"]
    msg = ChatMessage(ride_id=ride_id, sender=sender, message=message)
    msg.save()
    emit("new_message", {"sender": sender, "message": message, "created_at": msg.created_at.isoformat()}, room=ride_id)

# Driver accepts ride -> notify passenger & update DB
def driver_accepted(ride_id, driver):
    RideBooking.objects(id=ride_id).update(status="in_progress", assigned_driver=driver, updated_at=datetime.utcnow())
    socketio.emit("ride_update", {"status": "confirmed", "driver": {"id": str(driver.id), "name": driver.name}}, room=str(ride_id))

# Driver rejects/cancels -> free up driver & notify passenger
def driver_rejected(ride_id, driver_id):
    RideBooking.objects(id=ride_id).update(status="driver_rejected", assigned_driver=None, updated_at=datetime.utcnow())
    # mark driver available
    try:
        d = Driver.objects.get(id=driver_id)
        d.is_available = 1
        d.save()
    except Exception:
        pass
    socketio.emit("ride_update", {"status": "driver_rejected"}, room=str(ride_id))

# Ride completed -> cleanup chat & emit complete
def complete_ride(ride_id):
    RideBooking.objects(id=ride_id).update(status="completed", updated_at=datetime.utcnow())
    # delete chat history for that ride
    ChatMessage.objects(ride_id=ride_id).delete()
    socketio.emit("ride_update", {"status": "completed"}, room=str(ride_id))


# in socket_events.py
from passenger.sos import send_sos_sms, place_call
from passenger.routes import Passenger

@socketio.on('sos')
def handle_sos(data):
    ride_id = data.get('ride_id')
    passenger_id = data.get('passenger_id')
    lat = data.get('lat')
    lng = data.get('lng')
    # get passenger emergency contacts
    try:
        p = Passenger.objects.get(id=passenger_id)
        contacts = [p.emergency_contact_1, p.emergency_contact_2]
        for phone in contacts:
            if phone:
                try:
                    send_sos_sms(phone, p.name, lat, lng)
                except Exception as e:
                    print("Twilio SMS error", e)
        # optionally place call to local emergency number (country-specific)
        # place_call('100', twiml_url="http://your-server/twiml")  # caution: many restrictions
        emit("sos_sent", {"status": "ok"}, room=str(ride_id))
    except Exception as e:
        emit("sos_sent", {"status": "error", "error": str(e)}, room=str(ride_id))



def complete_ride(ride_id):
    """Cleanup chat + notify passenger"""
    ride = RideBooking.objects.get(id=ride_id)

    # 1. Delete chat history for this ride
    ChatMessage.objects(ride=ride).delete()

    # 2. Notify passenger in real-time
    emit("ride_completed", {
        "ride_id": str(ride.id),
        "driver_id": str(ride.assigned_driver.id),
        "fare": ride.fare
    }, room=f"passenger:{ride.passenger.id}")


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


@socketio.on("driver_location_update")
def handle_driver_location(data):
    # data: { ride_id, driver_id, lat, lng }
    ride_id = data.get("ride_id")
    lat = data.get("lat")
    lng = data.get("lng")

    # update driver/ride in DB (optional)
    try:
        rb = RideBooking.objects.get(id=ride_id)
        rb.update(current_gps=f"{lat},{lng}")
    except:
        pass

    # forward to passenger room(s)
    socketio.emit("driver_location", {"lat": lat, "lng": lng}, room=f"ride:{ride_id}")

@socketio.on('connect', namespace='/drivers')
def driver_connect():
    # drivers should send "auth" after connect with their driver_id to join room
    pass

@socketio.on('driver_auth', namespace='/drivers')
def driver_auth(data):
    driver_id = data.get('driver_id')
    if driver_id:
        room = f"driver_{driver_id}"
        join_room(room)
        # optionally set driver online true in DB
        d = Driver.objects(id=driver_id).first()
        if d:
            d.update(set__online=True, set__last_seen=datetime.utcnow())

@socketio.on('driver_response', namespace='/drivers')
def driver_response(data):
    # forward to handler
    handle_driver_response(data)

@socketio.on('driver_bid', namespace='/drivers')
def driver_bid(data):
    handle_driver_bid(data)

from flask_socketio import SocketIO, emit
socketio = SocketIO()

# When ride status changes → notify all admin dashboards
def broadcast_location_update(ride):
    socketio.emit("ride_location", {
        "ride_id": str(ride.id),
        "lat": ride.current_lat,
        "lng": ride.current_lng,
        "status": ride.status,
        "driver": ride.driver.name if ride.driver else None
    }, namespace="/admin")


# Handler when driver responds (SocketIO event) — to be registered in server
def handle_driver_response(data):
    # data should include: ride_id, driver_id, accepted (bool)
    ride = Ride.objects(id=data.get('ride_id')).first()
    driver = Driver.objects(id=data.get('driver_id')).first()
    if not ride or not driver:
        return
    accepted = data.get('accepted', False)
    if accepted:
        # assign driver
        ride.update(set__driver_id=str(driver.id), set__driver_name=driver.name, set__status='driver_assigned')
        # mark driver unavailable
        driver.update(set__available=False)
        # notify admin + passenger (through socket)
        socketio.emit('ride_assigned', {'ride_id': str(ride.id), 'driver_id': str(driver.id), 'driver_name': driver.name}, namespace='/admin')
        # notify other drivers who were pinged that ride is taken
        for dstr in ride.request_tokens:
            socketio.emit('ride_taken', {'ride_id': str(ride.id)}, to=f"driver_{dstr}", namespace='/drivers')
    else:
        # driver rejected -> increment attempts or try next; driver_response handler can trigger next driver search
        ride.update(inc__search_attempts=1)
        socketio.emit('driver_rejected', {'ride_id': str(ride.id), 'driver_id': str(driver.id)}, namespace='/admin')



# Driver places bid via socket event -> server appends to ride.bids and broadcasts to passenger/admin
def handle_driver_bid(data):
    # data: ride_id, driver_id, amount, eta
    ride = Ride.objects(id=data.get('ride_id')).first()
    if not ride:
        return
    bid = {'driver_id': data['driver_id'], 'driver_name': data.get('driver_name'), 'amount': float(data['amount']), 'eta': data.get('eta'), 'time': datetime.utcnow()}
    ride.update(push__bids=bid)
    socketio.emit('new_bid', {'ride_id': str(ride.id), 'bid': bid}, namespace='/admin')
    # optionally emit to passenger room
    socketio.emit('new_bid', {'ride_id': str(ride.id), 'bid': bid}, to=f"passenger_{ride.passenger_id}", namespace='/passenger')


from admin.model import AdminAlert


def handle_driver_offline(driver_id, ride_id):
    message = f"Driver {driver_id} went offline during active ride {ride_id}!"
    alert = AdminAlert(
        alert_type="offline_driver",
        severity="high",
        message=message
    ).save()

    socketio.emit("new_admin_alert", {
        "id": str(alert.id),
        "type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M"),
    }, broadcast=True)

def handle_payment_failure(user_id, txn_id, amount):
    message = f"Payment failure for User {user_id}, Transaction {txn_id}, Amount ₹{amount}"
    alert = AdminAlert(
        alert_type="payment_failure",
        severity="medium",
        message=message
    ).save()

    socketio.emit("new_admin_alert", {
        "id": str(alert.id),
        "type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M"),
    }, broadcast=True)

def handle_ride_issue(ride_id, issue_type):
    message = f"Ride {ride_id} reported issue: {issue_type}"
    alert = AdminAlert(
        alert_type="ride_issue",
        severity="medium" if issue_type != "critical" else "high",
        message=message
    ).save()

    socketio.emit("new_admin_alert", {
        "id": str(alert.id),
        "type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M"),
    }, broadcast=True)

def handle_dispute(ride_id, user_id, complaint_text):
    message = f"Dispute filed by User {user_id} on Ride {ride_id}: {complaint_text}"
    alert = AdminAlert(
        alert_type="dispute",
        severity="low",
        message=message
    ).save()

    socketio.emit("new_admin_alert", {
        "id": str(alert.id),
        "type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M"),
    }, broadcast=True)

    if alert.severity == "high":
        socketio.emit("critical_alert", {
        "id": str(alert.id),
        "message": alert.message
    }, broadcast=True)

    # Optionally email/sms senior admins
        send_email_to_admins(alert.message)


