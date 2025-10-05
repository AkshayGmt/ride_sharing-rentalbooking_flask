from mongoengine import Document, StringField, FloatField, DateTimeField, ReferenceField, DictField, BooleanField,EmailField
from datetime import datetime
class Passenger(Document):
    name = StringField(required=True)
    email = EmailField(required=True, unique=True)
    phone = StringField()
    username = StringField(required=True, unique=True)
    password = StringField(required=True)
    referral_code = StringField(required=False)  # ✅ optional
   #name = StringField(required=True)
    emergency_contact_1 = StringField()  # phone numbers as strings
    emergency_contact_2 = StringField()