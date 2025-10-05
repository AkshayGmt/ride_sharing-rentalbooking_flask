# models.py (append)
from mongoengine import Document, StringField, DictField, DateTimeField, BooleanField
from datetime import datetime

class Notification(Document):
    passenger_id = StringField(required=True)        # who receives the notification
    category = StringField(required=True)            # ride / rental / payment
    event = StringField(required=True)               # e.g. "ride_confirmed", "driver_arriving"
    title = StringField(required=True)
    message = StringField()
    data = DictField()                                # structured payload e.g. {"ride_id": "...", "driver": {...}}
    is_read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
