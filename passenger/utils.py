from math import radians, cos, sin, asin, sqrt
from driver.model import Driver   # adjust import path

# helper function to calculate distance between two lat/lng (Haversine formula)
def haversine(lon1, lat1, lon2, lat2):
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c   # Radius of earth in kilometers
    return km

def get_nearest_drivers(pickup_location, radius_km=5):
    """
    pickup_location: tuple (lat, lng)
    radius_km: search radius (default 5 km)
    """
    pickup_lat, pickup_lng = pickup_location
    nearby_drivers = []

    for driver in Driver.objects(is_online=True, is_available=True):
        if driver.latitude and driver.longitude:
            distance = haversine(
                pickup_lng, pickup_lat,
                driver.longitude, driver.latitude
            )
            if distance <= radius_km:
                nearby_drivers.append({
                    "id": str(driver.id),
                    "name": driver.name,
                    "vehicle": driver.vehicle_type,
                    "lat": driver.latitude,
                    "lng": driver.longitude,
                    "distance_km": round(distance, 2)
                })

    # sort by nearest first
    nearby_drivers.sort(key=lambda x: x["distance_km"])
    return nearby_drivers

# utils/history_utils.py
from datetime import datetime
from mongoengine.queryset.visitor import Q
from .model.booking_model import Booking

def query_history(passenger_id, start_date=None, end_date=None,
                  booking_type=None, vehicle_type=None, status=None, search=None):
    """Return passenger's bookings filtered by params"""
    q = Q(passenger_id=passenger_id)

    if booking_type:
        q &= Q(booking_type=booking_type)
    if vehicle_type:
        q &= Q(vehicle_type=vehicle_type)
    if status:
        q &= Q(status=status)
    if start_date:
        q &= Q(created_at__gte=start_date)
    if end_date:
        q &= Q(created_at__lte=end_date)
    if search:
        q &= (Q(pickup_name__icontains=search) |
              Q(drop_name__icontains=search) |
              Q(id__icontains=search))

    return Booking.objects(q).order_by('-created_at')

def recalc_fare_estimate(booking, current_rates):
    """
    Very basic recalculation.
    booking.fare_breakdown should have distance_km and duration_min for accuracy.
    """
    bd = booking.fare_breakdown or {}
    distance_km = bd.get("distance_km", 1)
    duration_min = bd.get("duration_min", 10)

    subtotal = (current_rates.get("base_per_km", 10.0) * distance_km +
                current_rates.get("per_min", 1.0) * duration_min)
    tax = round(subtotal * current_rates.get("tax", 0.18), 2)
    final = round(subtotal + tax, 2)

    return {
        "distance_km": distance_km,
        "duration_min": duration_min,
        "subtotal": round(subtotal, 2),
        "tax": tax,
        "final": final
    }
def send_email(to_email, subject, html_body):
    # TODO: use your SMTP or transactional provider (SendGrid, SES)
    pass
def send_sms(to_number, message):
    # TODO: integrate Twilio or other provider
    pass



def check_driver_delay(ride):
    # Waited max 5+5 minutes grace
    from datetime import datetime, timedelta
    pickup_time = ride.pickup_time
    now = datetime.utcnow()
    grace_period = timedelta(minutes=10)
    if now > pickup_time and now <= pickup_time + grace_period:
        return True  # Rider can cancel without charge
    return False

from .notification import notify_driver,notify_passenger
from .model.ride_model import Ride
def handle_vehicle_breakdown(ride_id):
    ride = Ride.objects(id=ride_id).first()
    if not ride:
        return {"error": "Ride not found"}
    
    ride.status = "Vehicle Breakdown"
    ride.save()

    # Dispatch new driver logic (pseudo)
    new_driver = assign_new_driver(ride)
    notify_driver(new_driver.id, f"New ride assigned: {ride.ride_id}")
    notify_passenger(ride.passenger_id, "Your ride will continue with a new driver.")
    
    # Adjust fare accordingly
    ride.fare = calculate_partial_fare(ride)
    ride.save()


def find_shared_rides(new_ride):
    rides = RideBooking.objects(shared=True, driver_assigned=None, payment_status="success")
    matched = []
    for ride in rides:
        if ride.id == new_ride.id:
            continue
        if haversine(ride.drop_lat, ride.drop_lng, new_ride.drop_lat, new_ride.drop_lng) <= 2:  # within 2 km drop
            if ride.scheduled_time and new_ride.scheduled_time:
                delta = abs((ride.scheduled_time - new_ride.scheduled_time).total_seconds())
                if delta <= 15 * 60:  # within 15 minutes
                    matched.append(ride)
            else:
                matched.append(ride)
    return matched
def add_to_shared_trip(new_ride):
    trips = RideBooking.objects(status="pending", drop_location=new_ride.drop_location)
    for ride in trips:
        if abs((ride.scheduled_time - new_ride.scheduled_time).total_seconds()) <= 15*60:
            # Add passenger
            ride.passenger_ids.append(new_ride.passenger_id)
            ride.ride_ids.append(str(new_ride.id))
            ride.pickup_points.append(new_ride.pickup_location)

            # Recalculate fares based on distance
            distances = {}
            total_distance = 0
            for ride_id in ride.ride_ids:
                ride = RideBooking.objects(id=ride_id).first()
                if ride:
                    dist = haversine(ride.pickup_lat, ride.pickup_lng, ride.drop_lat, ride.drop_lng)
                    distances[ride.passenger_id] = dist
                    total_distance += dist

            ride.total_fare = sum(RideBooking.objects(id__in=ride.ride_ids).values_list("fare_price"))
            
            # Split proportionally by distance
            fare_split = {}
            for pid, dist in distances.items():
                fare_split[pid] = round((dist / total_distance) * ride.total_fare, 2)

            ride.fare_split = fare_split
            ride.save()
            return ride.id

    # Otherwise, create a new SharedTrip
    dist = haversine(new_ride.pickup_lat, new_ride.pickup_lng, new_ride.drop_lat, new_ride.drop_lng)
    ride = RideBooking(
        passenger_ids=[new_ride.passenger_id],
        ride_ids=[str(new_ride.id)],
        pickup_points=[new_ride.pickup_location],
        drop_location=new_ride.drop_location,
        scheduled_time=new_ride.scheduled_time,
        total_fare=new_ride.fare_price,
        fare_split={new_ride.passenger_id: new_ride.fare_price}
    )
    ride.save()
    return ride.id



import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c
