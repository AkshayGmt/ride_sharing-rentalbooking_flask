from datetime import datetime
from mongoengine import Document, StringField, DateTimeField, BooleanField, IntField, FloatField, ReferenceField,ListField,DictField
from driver.drivermodel import Driver
from mongoengine import Document, DateTimeField
import datetime
class RideBooking(Document):
    passenger_id = StringField(required=True)
    
    # Locations
    pickup_location = StringField(required=True)
    drop_location = StringField(required=True)
    
    # Ride type
    ride_type = StringField(choices=["on_demand", "scheduled"], required=True)
    scheduled_time = DateTimeField(null=True)
    
    # Ride option
    shared = BooleanField(default=False)  # True = shared, False = private
    
    # Vehicle
    vehicle_type = StringField(choices=["car", "van", "bike", "auto"], required=True)
    passenger_capacity = IntField(default=1)
    luggage = BooleanField(default=False)
    
    # Preferences
    ac_preference = BooleanField(default=False)
    female_driver_preferred = BooleanField(default=False)
    extra_luggage_space = BooleanField(default=False)
    
    # Meta info
    status = StringField(default="pending")  # pending, confirmed, completed, cancelled
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    passenger_id = StringField(required=True)

    # Locations
    pickup_location = StringField(required=True)
    drop_location = StringField(required=True)

    # Ride type
    ride_type = StringField(choices=["on_demand", "scheduled"], required=True)
    scheduled_time = DateTimeField(null=True)

    # Ride option
    shared = BooleanField(default=False)  # True = shared, False = private

    # Vehicle
    vehicle_type = StringField(choices=["car", "van", "bike", "auto"], required=True)
    passenger_capacity = IntField(default=1)
    luggage = BooleanField(default=False)

    # Preferences
    ac_preference = BooleanField(default=False)
    female_driver_preferred = BooleanField(default=False)
    extra_luggage_space = BooleanField(default=False)

    # Fare & Payment
    estimated_fare = FloatField(default=0.0)
    coupon_code = StringField(null=True)
    discount_applied = FloatField(default=0.0)
    final_fare = FloatField(default=0.0)
    payment_method = StringField(choices=["razorpay", "cod"], default="cod")
    payment_status = StringField(default="pending")  # pending, paid, failed

    # Meta info
    status = StringField(default="pending")  # pending, confirmed, completed, cancelled
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    rating = IntField(min_value=1, max_value=5, null=True)   # passenger rating for this ride
    feedback = StringField(null=True)  # passenger comment
    assigned_driver = ReferenceField(Driver, null=True)

 # Ride lifecycle
    start_time = DateTimeField()
    end_time = DateTimeField()
    fare = FloatField(default=0.0)
    driver_id = StringField()
    passenger_ids = ListField(StringField())   # multiple passengers
    ride_ids = ListField(StringField())        # linked RideBooking IDs
    pickup_points = ListField(StringField())
    drop_location = StringField()
    scheduled_time = DateTimeField()

    total_fare = FloatField(default=0.0)          # total combined fare
    fare_split = DictField()                      # { passenger_id: fare_amount }

    status = StringField(default="pending")       # pending / ongoing / completed
    created_at = DateTimeField(default=datetime.datetime.utcnow)

from mongoengine import Document, StringField, DateTimeField, FloatField, BooleanField,DictField

class Ride(Document):
    ride_id = StringField(required=True, unique=True)
    driver_id = StringField(required=True)
    driver_name = StringField()
    passenger_id = StringField(required=True)
    passenger_name = StringField()
    pickup_time = DateTimeField(required=True)
    time_of_day = StringField()  # Morning/Afternoon/Evening/Night
    status = StringField(default="Pending")  # Pending, Completed, Cancelled, Driver No-Show
    fare = FloatField(default=0.0)
    no_show_notes = StringField()
    driver_id = StringField(required=True)
    driver_name = StringField()
    passenger_id = StringField(required=True)
    passenger_name = StringField()
    pickup_time = DateTimeField(required=True)
    time_of_day = StringField()
    status = StringField(default="Pending")  # Completed, Cancelled, Driver No-Show, Delayed, etc.
    contact_attempts_driver = IntField(default=0)
    contact_attempts_passenger = IntField(default=0)
    unreachable_flag = BooleanField(default=False)
    no_show_notes = StringField()

    
    ride_id = StringField(required=True, unique=True)
    passenger_id = StringField(required=True)
    passenger_name = StringField()
    vehicle_type = StringField(required=True)
    pickup_lat = FloatField()
    pickup_lng = FloatField()
    drop_lat = FloatField()
    drop_lng = FloatField()
    status = StringField(default="searching")   # searching, driver_assigned, ongoing, completed, cancelled, scheduled_pending, scheduled_assigned
    ride_type = StringField(default="on_demand") # on_demand, cargo, scheduled
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    scheduled_at = DateTimeField()  # for scheduled rides
    driver_id = StringField()       # assigned driver id
    driver_name = StringField()
    fare_estimate = FloatField(default=0.0)
    search_attempts = IntField(default=0)   # number of driver attempts made
    request_tokens = ListField(StringField())  # list of driver ids currently pinged (for UI)
    bids = ListField(DictField())   
    driver_id = StringField()
    passenger_id = ListField(StringField())   # multiple passengers
    ride_id = ListField(StringField())        # linked RideBooking IDs
    pickup_points = ListField(StringField())   # list of pickup locations
    drop_location = StringField()
    scheduled_time = DateTimeField()
    status = StringField(default="pending")       # pending / ongoing / completed
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    # for cargo: [{'driver_id','driver_name','amount','eta'}]
    meta = {"collection": "rides"}