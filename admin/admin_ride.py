
# Dispatch logic for passenger on-demand
def dispatch_passenger_ride(ride_obj_id):
    ride = Ride.objects(id=ride_obj_id).first()
    if not ride:
        return
    pickup_lat, pickup_lng = ride.pickup_lat, ride.pickup_lng
    # find nearest drivers within 5km (limit 10 for population)
    nearby = find_nearest_drivers(pickup_lat, pickup_lng, ride.vehicle_type, radius_km=5.0, limit=10)
    # limit request population to 10
    population = nearby[:10]
    # attempt sequentially with up to 2 retries (i.e., try driver0, driver1)
    tried = 0
    MAX_TRIES = 2
    for driver in population:
        if tried >= MAX_TRIES:
            break
        # ping driver (emit event to that driver socket room)
        # assume driver.socket_room == f"driver_{driver.id}"
        driver_room = f"driver_{str(driver.id)}"
        payload = {
            'ride_id': str(ride.id),
            'ride_short': ride.ride_id,
            'pickup_lat': pickup_lat, 'pickup_lng': pickup_lng,
            'passenger_name': ride.passenger_name,
            'vehicle_type': ride.vehicle_type,
        }
        socketio.emit('ride_request', payload, to=driver_room, namespace='/drivers')
        # mark request token
        ride.update(push__request_tokens=str(driver.id))
        ride.reload()
        # now wait for a response — in production you'd implement an async wait with timeout.
        # Here, we mark that we've attempted (increasing search_attempts). The driver app should reply via socket event 'driver_response'.
        tried += 1
    # if no driver accepted, admin UI will show 'try again later' — set a timer or status:
    ride.update(search_attempts=tried)
    socketio.emit('dispatch_started', {'ride': ride.to_mongo()}, namespace='/admin')

