from mongoengine import Document, StringField, DateTimeField, BooleanField
import datetime
from mongoengine import Document, StringField, EmailField,ReferenceField
from .drivermodel import Driver
class DriverNotification(Document):
    driver_id = StringField(required=True)
    title = StringField(required=True)
    message = StringField(required=True)
    driver = ReferenceField(Driver, required=True)   # link to driver
    type = StringField(required=True, choices=["Email", "SMS", "System"])
    title = StringField(required=True)               # e.g. "Document Update"
    message = StringField(required=True)             # notification content
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    is_read = BooleanField(default=False)  
    type = StringField(choices=[
        "payout", "ride", "rental", "payment", "rating", "system"
    ])
    is_read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.datetime.utcnow)


    