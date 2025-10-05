from datetime import datetime
from mongoengine import Document, StringField, DateTimeField, BooleanField, IntField, FloatField, ReferenceField,ListField
from driver.drivermodel import Driver
from mongoengine import Document, DateTimeField
import datetime
# class RideBooking(Document):
#     passenger_id = StringField(required=True)
    
#     # Locations
#     pickup_location = StringField(required=True)
#     drop_location = StringField(required=True)
    
#     # Ride type
#     ride_type = StringField(choices=["on_demand", "scheduled"], required=True)
#     scheduled_time = DateTimeField(null=True)
    
#     # Ride option
#     shared = BooleanField(default=False)  # True = shared, False = private
    
#     # Vehicle
#     vehicle_type = StringField(choices=["car", "van", "bike", "auto"], required=True)
#     passenger_capacity = IntField(default=1)
#     luggage = BooleanField(default=False)
    
#     # Preferences
#     ac_preference = BooleanField(default=False)
#     female_driver_preferred = BooleanField(default=False)
#     extra_luggage_space = BooleanField(default=False)
    
#     # Meta info
#     status = StringField(default="pending")  # pending, confirmed, completed, cancelled
#     created_at = DateTimeField(default=datetime.datetime.utcnow)

#     passenger_id = StringField(required=True)

#     # Locations
#     pickup_location = StringField(required=True)
#     drop_location = StringField(required=True)

#     # Ride type
#     ride_type = StringField(choices=["on_demand", "scheduled"], required=True)
#     scheduled_time = DateTimeField(null=True)

#     # Ride option
#     shared = BooleanField(default=False)  # True = shared, False = private

#     # Vehicle
#     vehicle_type = StringField(choices=["car", "van", "bike", "auto"], required=True)
#     passenger_capacity = IntField(default=1)
#     luggage = BooleanField(default=False)

#     # Preferences
#     ac_preference = BooleanField(default=False)
#     female_driver_preferred = BooleanField(default=False)
#     extra_luggage_space = BooleanField(default=False)

#     # Fare & Payment
#     estimated_fare = FloatField(default=0.0)
#     coupon_code = StringField(null=True)
#     discount_applied = FloatField(default=0.0)
#     final_fare = FloatField(default=0.0)
#     payment_method = StringField(choices=["razorpay", "cod"], default="cod")
#     payment_status = StringField(default="pending")  # pending, paid, failed

#     # Meta info
#     status = StringField(default="pending")  # pending, confirmed, completed, cancelled
#     created_at = DateTimeField(default=datetime.datetime.utcnow)
#     rating = IntField(min_value=1, max_value=5, null=True)   # passenger rating for this ride
#     feedback = StringField(null=True)  # passenger comment
#     assigned_driver = ReferenceField(Driver, null=True)

#  # Ride lifecycle
#     start_time = DateTimeField()
#     end_time = DateTimeField()
#     fare = FloatField(default=0.0)

from datetime import datetime, timedelta



class ChatMessage(Document):
    ride_id = StringField(required=True, index=True)
    sender = StringField(required=True)   # "passenger:<id>" or "driver:<id>"
    message = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    
# class RentalBooking(Document):
#     passenger_id = StringField(required=True)
#     ride_type = StringField(choices=["on_demand","scheduled"], required=True)
#     vehicle_type = StringField(required=True)         # Car/Van/Truck/Bike etc.
#     load_type = StringField(required=True)
#     addons = ListField(StringField())                 # gps, insurance, etc.

#     start_time = DateTimeField(required=True)
#     end_time = DateTimeField(required=True)
#     rental_duration_unit = StringField(choices=["hourly","daily"], default="hourly")

#     pickup_name = StringField(required=True)
#     pickup_coords = StringField(required=True)        # "lat,lng"
#     drop_name = StringField(required=True)
#     drop_coords = StringField(required=True)          # "lat,lng"

#     estimated_fare = FloatField(default=0.0)
#     taxes = FloatField(default=0.0)
#     final_fare = FloatField(default=0.0)

#     payment_method = StringField(choices=["razorpay","cod"], default="cod")
#     payment_status = StringField(default="pending")   # pending, paid, failed

#     assigned_vehicle_id = StringField()               # optional: which vehicle assigned
#     updated_at = DateTimeField(default=datetime.utcnow)
#     passenger = ReferenceField("Passenger", required=True)
#     driver = ReferenceField("Driver", null=True)  # optional if self-drive
#     load_type = StringField()
#     fare = FloatField(required=True)
#     with_driver = BooleanField(default=False)  # ✅ If rental includes driver

 
#     # Vehicle Handover Info
#     handover_done = BooleanField(default=False)
#     handover_timestamp = DateTimeField()
#     handover_gps = StringField()  # store "lat,long"
#     handover_photo = StringField()  # optional file upload

  
#     # Tracking fields
#     current_gps = StringField()  # "lat,long"
#     eta = DateTimeField()
#     kilometers_driven = FloatField(default=0.0)
#     hours_used = FloatField(default=0.0)
#     fuel_level = FloatField(default=0.0)  # optional
#     deviation_alert = BooleanField(default=False)

#     # Extension Info
#     extension_requested = BooleanField(default=False)
#     extension_new_end = DateTimeField()
#     extension_fare = FloatField()
#     extension_approved = BooleanField(default=False)
#     passenger_id = StringField(required=True)  # link to passenger session
#     ride_type = StringField(choices=["on_demand", "scheduled"], required=True)
#     vehicle_type = StringField(required=True)
#     load_type = StringField(required=True)
#     rental_duration = StringField(choices=["hourly", "daily"], required=True)
#     start_time = DateTimeField(required=True)
#     end_time = DateTimeField(required=True)
#     addons = ListField(StringField())
#     estimated_fare = FloatField(required=True)
#     payment_method = StringField(choices=["razorpay", "cod"], required=True)
#     pickup_lat = FloatField(required=True)
#     pickup_lng = FloatField(required=True)
#     drop_lat = FloatField(required=True)
#     drop_lng = FloatField(required=True)
#     assigned_driver = ReferenceField(Driver, null=True)
#     assenger_id = StringField(required=True)

#     # status: pending, assigned, waiting_for_driver, confirmed, arriving, in_progress, completed ...
#     status = StringField(default="pending")
#     assigned_driver_id = StringField()    # store driver id string
#     created_at = DateTimeField(default=datetime.utcnow)
