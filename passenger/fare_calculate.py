from datetime import datetime

def calculate_fare(distance_km, duration_min, ride_option, vehicle_type, coupon=None):
    # Base rates (example values)
    base_fare = 30
    per_km = 10
    per_min = 2

    # Vehicle multipliers
    vehicle_multipliers = {
        "car": 1.0,
        "van": 1.5,
        "bike": 0.7,
        "auto": 0.8
    }
    multiplier = vehicle_multipliers.get(vehicle_type, 1.0)

    # Calculate raw fare
    fare = (base_fare + (per_km * distance_km) + (per_min * duration_min)) * multiplier

    # Shared ride discount
    if ride_option == "shared":
        fare *= 0.75  # 25% discount

    # Surge pricing (peak hours 7–10 AM, 5–8 PM)
    now = datetime.now().hour
    if (7 <= now <= 10) or (17 <= now <= 20):
        fare *= 1.3  # 30% surge

    # Coupon discount
    discount = 0
    if coupon == "FIRST50":
        discount = min(50, fare * 0.5)  # Max ₹50 discount
    elif coupon == "SAVE20":
        discount = fare * 0.2  # 20% off

    final_fare = fare - discount
    return round(fare, 2), discount, round(final_fare, 2)
