# utils/rental_utils.py
from datetime import datetime, timedelta
from driver.model import Vehicle
from .model.rental_model import RentalBooking

# Example base rates (configurable by admin)
BASE_RATES = {
    "hourly": {
        "car": 200,
        "van": 300,
        "truck": 600,
        "bike": 80,
        "cargo_van": 400
    },
    "daily": {
        "car": 1200,
        "van": 1800,
        "truck": 4000,
        "bike": 400,
        "cargo_van": 2500
    }
}

VEHICLE_MULTIPLIER = {
    "car": 1.0, "van": 1.1, "truck": 1.6, "bike": 0.6, "cargo_van": 1.3
}

def validate_schedule(start_dt: datetime, end_dt: datetime):
    now = datetime.utcnow()
    if start_dt < now + timedelta(minutes=15):
        return False, "Pickup time must be at least 15 minutes from now."
    if start_dt > now + timedelta(days=7):
        return False, "Pickup time cannot be more than 7 days in advance."
    if end_dt <= start_dt:
        return False, "End time must be after start time."
    return True, ""

def calculate_rental_cost(vehicle_type: str, start_dt: datetime, end_dt: datetime,
                          duration_unit: str="hourly", addons: list=None):
    """
    Returns (estimated_fare_before_tax, tax_amount, final_fare)
    - duration_unit: "hourly" or "daily"
    - addons: list e.g. ["gps", "insurance"]
    """
    addons = addons or []
    # compute duration
    delta = end_dt - start_dt
    if duration_unit == "hourly":
        hours = delta.total_seconds()/3600
        units = max(1, round(hours))  # at least 1 hour
    else:
        days = delta.total_seconds()/(3600*24)
        units = max(1, round(days))   # at least 1 day

    base_rate = BASE_RATES.get(duration_unit, {}).get(vehicle_type.lower(), 500)
    multiplier = VEHICLE_MULTIPLIER.get(vehicle_type.lower(), 1.0)
    raw = base_rate * units * multiplier

    addon_cost = 0
    if "gps" in addons: addon_cost += 50 * units
    if "insurance" in addons: addon_cost += 100 * units
    if "extra_hand" in addons: addon_cost += 200 * units

    subtotal = raw + addon_cost
    tax = round(subtotal * 0.18, 2)   # 18% GST (example)
    final = round(subtotal + tax, 2)
    return round(subtotal,2), tax, final

def find_available_vehicles(vehicle_type: str, start_dt: datetime, end_dt: datetime):
    """
    Basic availability check: here we filter on vehicle_type and available flag.
    In production you must check calendar bookings (overlap) for exact availability.
    """
    q = Vehicle.objects(vehicle_type__iexact=vehicle_type, available=True)
    return q  # list of vehicle documents (may be empty)



