from datetime import time

def get_time_of_day(pickup_time):
    t = pickup_time.time()
    if time(5, 30) <= t < time(11, 0):
        return "Morning"
    elif time(11, 0) <= t < time(17, 0):
        return "Afternoon"
    elif time(17, 0) <= t < time(21, 0):
        return "Evening"
    else:
        return "Night"
