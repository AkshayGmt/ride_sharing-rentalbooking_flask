# models.py
from mongoengine import Document, StringField, FloatField, DateTimeField, ReferenceField, DictField, BooleanField
from datetime import datetime

class Booking(Document):
    booking_type = StringField(choices=("ride","rental"), required=True)  # ride or rental
    sub_type = StringField()   # e.g. shared/private or self-drive/with-driver
    passenger_id = StringField(required=True)
    driver_id = StringField()  # optional
    vehicle_type = StringField()   # car, van, truck etc for rentals
    vehicle_details = DictField()   # optional dict for rentals (make/model, plate)
    pickup_name = StringField()
    pickup_lat = FloatField()
    pickup_lng = FloatField()
    drop_name = StringField()
    drop_lat = FloatField()
    drop_lng = FloatField()
    start_time = DateTimeField()
    end_time = DateTimeField()
    fare = FloatField(default=0.0)
    fare_breakdown = DictField()  # {"base":..,"distance":..,"time":..,"tax":..,"discount":..}
    payment_method = StringField()
    payment_status = StringField(choices=("pending","paid","failed","refunded"), default="pending")
    status = StringField(choices=("completed","cancelled","ongoing","pending"), default="completed")
    created_at = DateTimeField(default=datetime.utcnow)
    # any other fields
