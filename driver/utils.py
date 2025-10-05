from datetime import datetime, timedelta

# Earnings cap per vehicle type for Basic drivers
BASIC_CAP = {
    "Bike": 200,
    "Auto": 250,
    "Car": 350,
    "Cargo": 500
}

# Premium active hours per day
PREMIUM_HOURS_LIMIT = 10  # hours

def check_daily_reset(subscription):
    today = datetime.datetime.utcnow().date()
    if subscription.last_reset_date.date() < today:
        subscription.daily_earnings_today = 0
        subscription.active_hours_today = 0
        subscription.last_reset_date = datetime.datetime.utcnow()
        subscription.save()

def can_accept_ride(subscription, vehicle_type):
    check_daily_reset(subscription)
    if subscription.subscription_type == "Basic":
        cap = BASIC_CAP.get(vehicle_type, 350)
        if subscription.daily_earnings_today >= cap:
            return False, f"Daily earnings cap reached ({cap}). Upgrade to Premium for unlimited earnings."
    elif subscription.subscription_type == "Premium":
        hours = subscription.active_hours_today / 60
        if hours >= PREMIUM_HOURS_LIMIT:
            return False, "You’ve reached the 10-hour driving limit for today. Please rest."
    return True, ""

from flask import session
from driver.drivermodel import Driver  # your Driver model

def get_current_driver():
    driver_id = session.get('driver_id')
    if not driver_id:
        return None
    return Driver.objects(id=driver_id).first()

from geopy.distance import geodesic
import datetime

def calculate_eta(rental, avg_speed_kmh=40):
    """
    rental.current_gps = "lat,lng"
    rental.end_location = "lat,lng" (add this field in model)
    """
    if not rental.current_gps or not hasattr(rental, "end_location"):
        return None

    start_lat, start_lng = map(float, rental.current_gps.split(','))
    end_lat, end_lng = map(float, rental.end_location.split(','))

    distance_km = geodesic((start_lat, start_lng), (end_lat, end_lng)).km
    eta_hours = distance_km / avg_speed_kmh
    eta_datetime = datetime.datetime.utcnow() + datetime.timedelta(hours=eta_hours)
    return eta_datetime


def check_route_deviation(rental):
    """
    rental.allowed_route = list of coordinates [(lat1,lng1), (lat2,lng2), ...]
    """
    if not rental.allowed_route or not rental.current_gps:
        return False

    curr_lat, curr_lng = map(float, rental.current_gps.split(','))
    # Simple check: deviation if outside bounding box
    lats = [lat for lat, lng in rental.allowed_route]
    lngs = [lng for lat, lng in rental.allowed_route]

    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)

    if curr_lat < min_lat or curr_lat > max_lat or curr_lng < min_lng or curr_lng > max_lng:
        return True
    return False

def notify_admin(message):
    # For now, just print. Replace with email/SMS/socket notifications.
    print(f"[ADMIN ALERT]: {message}")


