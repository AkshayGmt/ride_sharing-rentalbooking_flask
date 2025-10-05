# routes/navigation.py
from flask import Blueprint, render_template, current_app, jsonify
from passenger.model import RideBooking
import os
import requests
from datetime import datetime
from socket_event import socketio  # we will use socketio.emit for live events if needed

navigation_bp = Blueprint("navigation", __name__)

GOOGLE_JS_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")     # JS key for client
GOOGLE_SERVER_KEY = os.environ.get("GOOGLE_MAPS_SERVER_KEY")  # server key for webservice calls

@navigation_bp.route("/driver/navigation/<ride_id>")
def driver_navigation(ride_id):
    booking = RideBooking.objects.get(id=ride_id)
    pickup = {"lat": booking.pickup_lat, "lng": booking.pickup_lng}
    drop   = {"lat": booking.drop_lat, "lng": booking.drop_lng}
    return render_template("driver_navigation.html",
                           booking_id=str(booking.id),
                           pickup=pickup,
                           drop=drop,
                           google_js_key=GOOGLE_JS_KEY)

# Server-side Directions call to get traffic-aware ETA & route polyline
@navigation_bp.route("/api/directions/<ride_id>")
def api_directions(ride_id):
    booking = RideBooking.objects.get(id=ride_id)
    origin = f"{booking.pickup_lat},{booking.pickup_lng}"
    dest   = f"{booking.drop_lat},{booking.drop_lng}"

    if not GOOGLE_SERVER_KEY:
        return jsonify({"error": "GOOGLE_MAPS_SERVER_KEY not configured"}), 500

    # Use departure_time=now to get duration_in_traffic
    params = {
        "origin": origin,
        "destination": dest,
        "key": GOOGLE_SERVER_KEY,
        "departure_time": "now",   # important for traffic
        "traffic_model": "best_guess",
        "alternatives": "true"
    }
    url = "https://maps.googleapis.com/maps/api/directions/json"
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    if data.get("status") != "OK":
        return jsonify({"error": data.get("status"), "raw": data}), 400

    routes = []
    for r in data.get("routes", []):
        summary = r.get("summary")
        legs = r.get("legs", [])
        total_distance_m = 0
        total_duration_s = 0
        duration_in_traffic_s = 0
        steps = []

        for leg in legs:
            total_distance_m += leg.get("distance", {}).get("value", 0)
            # some responses include duration_in_traffic inside leg
            duration_in_traffic_s += leg.get("duration_in_traffic", {}).get("value", leg.get("duration", {}).get("value", 0))
            total_duration_s += leg.get("duration", {}).get("value", 0)
            for step in leg.get("steps", []):
                steps.append({
                    "html_instructions": step.get("html_instructions"),
                    "distance": step.get("distance"),
                    "duration": step.get("duration"),
                    "start_location": step.get("start_location"),
                    "end_location": step.get("end_location")
                })

        polyline = r.get("overview_polyline", {}).get("points")
        routes.append({
            "summary": summary,
            "distance_m": total_distance_m,
            "duration_s": total_duration_s,
            "duration_in_traffic_s": duration_in_traffic_s,
            "polyline": polyline,
            "steps": steps
        })

    # return best route (index 0) and alternatives
    return jsonify({"routes": routes, "status": "OK"})
