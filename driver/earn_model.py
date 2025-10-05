from mongoengine import Document, StringField, FloatField, DateTimeField, ReferenceField, IntField
import datetime

class DriverEarning(Document):
    driver_id = StringField(required=True)
    ride_type = StringField(choices=["ride", "rental"], required=True)
    base_fare = FloatField(default=0)
    distance_charge = FloatField(default=0)
    time_charge = FloatField(default=0)
    surge_charge = FloatField(default=0)
    commission = FloatField(default=0)
    bonus = FloatField(default=0)
    total_amount = FloatField(default=0)
    created_at = DateTimeField(default=datetime.datetime.utcnow)


class DriverPayout(Document):
    driver_id = StringField(required=True)
    amount = FloatField(required=True)
    method = StringField(choices=["Bank", "UPI", "Wallet"])
    status = StringField(choices=["Pending", "Completed", "Rejected"], default="Pending")
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    processed_at = DateTimeField()
    method = StringField(choices=['bank','upi','wallet','third_party'], required=True)
    status = StringField(choices=['requested','approved','rejected','processed'], default='requested')
    requested_at = DateTimeField(default=datetime.datetime.utcnow)
    admin_note = StringField()
    total_amount = FloatField(default=0.0)       # ride earnings
    wallet_topup = FloatField(default=0.0)       # added via Razorpay
    created_at = DateTimeField(default=datetime.datetime.utcnow)
