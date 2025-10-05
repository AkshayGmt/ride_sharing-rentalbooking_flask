from mongoengine import Document, StringField, DateTimeField, FileField, EmbeddedDocument, EmbeddedDocumentField,IntField,StringField, IntField, ListField, DateTimeField
from datetime import datetime
from mongoengine import Document, StringField, FloatField, DateTimeField, ReferenceField, BooleanField,DictField
from passenger.model.rental_model import  RentalBooking
from passenger.model.ride_model import RideBooking
from .drivermodel import Driver
class InsuranceDocument(EmbeddedDocument):
    insurance_type = StringField(required=True)
    provider = StringField(required=True)
    policy_number = StringField(required=True)
    policy_start = DateTimeField(required=True)
    policy_expiry = DateTimeField(required=True)
    vehicle_number = StringField(required=True)
    insurance_file = StringField(required=True)  # saved file path

class DriverDocuments(Document):
    driver_id = StringField(required=True)
    driving_license = StringField(required=True)
    vehicle_rc = StringField(required=True)
    id_proof = StringField(required=True)
    insurance = EmbeddedDocumentField(InsuranceDocument)
    profile_photo = StringField()  # optional
    police_clearance = StringField()  # optional
    created_at = DateTimeField(default=datetime.utcnow)
    # Document Uploads
    driving_license = StringField()   # file path / URL
    commercial_permit =StringField()
    rc_book = StringField()
    insurance = StringField()
    id_proof = StringField()

    # Document Verification Status
    doc_status = DictField(default={
        "driving_license": "Pending",
        "commercial_permit": "Pending",
        "rc_book": "Pending",
        "insurance": "Pending",
        "id_proof": "Pending"
    })

class Vehicle(Document):
    driver_id = StringField(required=True)
    vehicle_type = StringField(required=True)  # Car, Van, Truck, Bike
    make_model = StringField(required=True)
    year_of_manufacture = IntField(required=True)
    vehicle_number = StringField(required=True)
    capacity = StringField(required=True)  # number of passengers or cargo limit
    vehicle_images = ListField(StringField())  # list of uploaded image paths
    created_at = DateTimeField(default=datetime.utcnow)

    vehicle_type = StringField(required=True)   # Car, Van, Truck...
    make_model = StringField()
    year = IntField()
    capacity = IntField()
    fuel_type = StringField()
    luggage_space = StringField()
    images = ListField(StringField())           # URLs or paths
    status = StringField(default="Available")  # Available, Booked, Maintenance, Disabled, Offline
    current_ride_id = StringField()             # optional
    return_schedule = DateTimeField()           # optional
    overdue = BooleanField(default=False)      # if not returned on time
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    driver_id = StringField(required=True)            # driver who owns/operates vehicle
    vehicle_type = StringField(required=True)         # Car, Van, Truck, Bike, etc.
    make_model = StringField()
    year_of_manufacture = IntField()
    vehicle_number = StringField()
    capacity = StringField()                          # e.g. "1000 kg" or "3 pax"
    available = BooleanField(default=True)            # overall availability flag
    categories = ListField(StringField())             # e.g. ["cargo", "fragile", "two_wheeler"]
    created_at = DateTimeField(default=datetime.utcnow)
    attributes = StringField()  # e.g., Seats, AC, Fuel Type
    rental_price_per_hour = FloatField(default=0.0)
    commission_percent = FloatField(default=0.0)
    availability_count = IntField(default=0)
    vehicle_type = StringField(required=True)
    make_model = StringField(required=True)
    year = IntField()
    capacity = IntField()
    fuel_type = StringField()
    luggage_space = StringField()
    images = ListField(StringField())  # store image URLs
    status = StringField(default="Available")  # Available, Booked, Maintenance, Disabled
    rental_price_per_hour = FloatField(default=0.0)
    commission_percent = FloatField(default=0.0)

    meta = {"collection": "vehicles"}
    
    

from mongoengine import Document, StringField, IntField, DateTimeField, BooleanField
from datetime import datetime, timedelta

class DriverSubscription(Document):
    driver_id = StringField(required=True, unique=True)
    subscription_type = StringField(default="Basic")  # Basic or Premium
    premium_expiry = DateTimeField()  # Only relevant if Premium
    active_hours_today = IntField(default=0)  # minutes driven today for Premium
    daily_earnings_today = IntField(default=0)  # earnings today for Basic
    vehicle_addon = BooleanField(default=False)  # True if purchased "Other Vehicle Membership"
    addon_vehicle_type = StringField()  # optional vehicle type for addon
    created_at = DateTimeField(default=datetime.utcnow)
    last_reset_date = DateTimeField(default=datetime.utcnow)  # to reset daily counters
    plan_name = StringField()
    duration = StringField( choices=["Weekly", "Monthly", "Yearly"])  # example choices
    price = FloatField()
    status = StringField(default="Active")  # Active / Expired / Pending
   
class RideRating(Document):
    ride = ReferenceField(RideBooking, required=True)
    rental = ReferenceField(RentalBooking, required=True)
    driver = ReferenceField(Driver, required=True)
    passenger_id = StringField(required=True)
    rating = IntField(min_value=1, max_value=5, required=True)
    comment = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    passenger_name = StringField(required=True)
    driver_id = StringField(required=True)      # or ReferenceField(Driver) if you prefer

class DriverIncident(Document):
    driver_id = StringField(required=True)
    incident_type = StringField(choices=["No-show", "Late", "Other"])
    description = StringField()
    date = DateTimeField(default=datetime.utcnow)
