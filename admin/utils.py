from passenger.notification import notify_driver,notify_passenger
from mongoengine import Document, StringField, DateTimeField, DictField,BooleanField,FloatField
from datetime import datetime

class Subscription(Document):
    driver_id = StringField()
    auto_renew = BooleanField(default=False)
    renewal_date = DateTimeField()
    amount = FloatField()

def send_renewal_reminder():
    upcoming = Subscription.objects(auto_renew=True, renewal_date__lte=datetime.utcnow() + timedelta(days=3))
    for sub in upcoming:
        notify_driver(sub.driver_id, f"Your Premium subscription will renew on {sub.renewal_date} for ₹{sub.amount}")

def handle_failed_payment(subscription):
    subscription.auto_renew = False
    subscription.save()
    notify_driver(subscription.driver_id, "Auto-renewal failed. Please manually renew.")


def compute_rental_price(vehicle_type, tier, hours=0, days=0, selected_addons=None, is_peak=False):
    selected_addons = selected_addons or {}
    p = RentalPricing.objects(vehicle_type=vehicle_type, tier=tier).first()
    if not p:
        raise ValueError("No pricing rule")
    base = p.base_fare_per_hour * hours + p.base_fare_per_day * days
    base *= p.vehicle_multiplier
    addons_amount = sum([float(p.addons.get(k, 0)) * (1 if val else 0) for k,val in selected_addons.items()]) if p.addons else 0
    subtotal = base + addons_amount
    if is_peak:
        subtotal *= p.peak_hour_multiplier
    tax = subtotal * (p.tax_percent/100.0)
    commission = subtotal * (p.commission_percent/100.0)
    total = subtotal + tax
    return {
        "subtotal": subtotal,
        "tax": tax,
        "commission": commission,
        "total": total
    }


# utils.py
import math
from datetime import datetime, timedelta


def haversine_km(lat1, lon1, lat2, lon2):
    # returns distance in kilometers
    R = 6371.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def find_nearest_drivers(pickup_lat, pickup_lng, vehicle_type, radius_km=5.0, limit=10):
    # naive approach: fetch drivers online & available with matching vehicle_type
    qs = Driver.objects(vehicle_type=vehicle_type, online=True, available=True)
    drivers = []
    for d in qs:
        if d.latitude is None or d.longitude is None:
            continue
        dist = haversine_km(pickup_lat, pickup_lng, d.latitude, d.longitude)
        if dist <= radius_km:
            drivers.append((dist, d))
    drivers.sort(key=lambda x: x[0])
    return [d for dist,d in drivers][:limit]

def driver_within_5km_exists(pickup_lat, pickup_lng, vehicle_type):
    return len(find_nearest_drivers(pickup_lat, pickup_lng, vehicle_type, radius_km=5.0, limit=1)) > 0


# scheduled_assign.py
from driver.drivermodel import Driver
from passenger.model.ride_model import Ride
from datetime import datetime, timedelta
from .admin_rides import dispatch_passenger_ride

def assign_scheduled_rides():
    now = datetime.utcnow()
    window = now + timedelta(minutes=30)
    rides = Ride.objects(status='scheduled_pending', scheduled_at__lte=window)
    for r in rides:
        # check drivers eligible (similar to auto-dispatch)
        dispatch_passenger_ride(r.id)
        r.update(set__status='scheduled_assigned')

def handle_rider_cancellation(ride, cancel_time, is_scheduled):
    if is_scheduled:
        # Scheduled ride: free if >30 min before
        if (ride.pickup_time - cancel_time).total_seconds() > 1800:
            return {"fee": 0, "reason": "Free (before 30 min)"}
        else:
            return {"fee": min(ride.fare * 0.1, 200), "reason": "Late cancellation"}
    else:
        # On-demand
        if (cancel_time - ride.assigned_time).total_seconds() <= 60:
            return {"fee": 0, "reason": "Grace period"}
        else:
            return {"fee": min(ride.fare * 0.1, 200), "reason": "Late cancellation"}
def handle_driver_cancellation(ride, cancel_time):
    # No fee to driver, rider never charged
    # Try auto-assign replacement
    replacement = find_replacement_driver(ride)
    if replacement:
        ride.update(driver=replacement.id, status="driver_assigned")
        notify_user(ride.passenger, f"Your ride has been reassigned to {replacement.name}")
    else:
        notify_user(ride.passenger, "No replacement driver found. You may cancel free or wait longer.")
    return {"fee": 0, "reason": "Driver cancelled, platform bears cost"}

from datetime import datetime

def calculate_cancellation_fee(ride, cancelled_by):
    now = datetime.utcnow()
    if cancelled_by == "rider":
        if ride.is_scheduled:
            diff = (ride.pickup_time - now).total_seconds()
            if diff > 1800:  # >30min free
                return {"fee": 0, "reason": "Free cancellation before 30 minutes"}
            else:
                return {"fee": min(ride.fare * 0.1, 200), "reason": "Late cancellation"}
        else:  # On-demand
            diff = (now - ride.assigned_time).total_seconds()
            if diff <= 60:
                return {"fee": 0, "reason": "Grace period (within 1 min)"}
            else:
                return {"fee": min(ride.fare * 0.1, 200), "reason": "Late cancellation"}
    elif cancelled_by == "driver":
        return {"fee": 0, "reason": "Driver cancelled — rider not charged"}
    return {"fee": 0, "reason": "Unknown case"}


def record_audit(admin_name, action, user_id, details=""):
    log = AuditLog(
        admin=admin_name,
        action=action,
        user_id=user_id,
        details=details,
        timestamp=datetime.now()
    )
    log.save()