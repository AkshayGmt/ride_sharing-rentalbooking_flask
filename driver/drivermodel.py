from mongoengine import Document, StringField, DateTimeField, FileField, EmbeddedDocument, EmbeddedDocumentField,IntField,StringField, IntField, ListField, DateTimeField
from datetime import datetime
from mongoengine import Document, StringField, FloatField, DateTimeField, ReferenceField, BooleanField

class Driver(Document):
    username = StringField(required=True, unique=True)
    password = StringField(required=True)
    license_number = StringField(required=True)
    referral_code = StringField(required=False) 

    vehicle_type = StringField()
    vehicle_number = StringField()
    profile_photo = StringField()
    email = StringField(unique=True, required=True)


    license_doc = StringField()  # path/URL
    insurance_doc = StringField()
    docs_expiry = DateTimeField()  # expiry date for insurance/license
    status = StringField(default="Pending")  # Pending, Approved, Rejected
    rejection_reason = StringField()
    approved_on = DateTimeField()

# Status & activity
    active_ride_id = StringField()             # Current ride/rental ID
    rides_completed = IntField(default=0)
    rides_rejected = IntField(default=0)
    rides_accepted = IntField(default=0)

    # Location (updated by driver app)

    name = StringField(required=True)
    phone = StringField()
    online = BooleanField(default=False)
    available = BooleanField(default=True)   # True if not on trip
    rating = FloatField(default=0.0)
    last_seen = DateTimeField(default=datetime.utcnow)
    latitude = FloatField()
    longitude = FloatField()
    is_online = BooleanField(default=True)
    is_available = BooleanField(default=True)
    total_ratings = IntField(default=0)
    rating_sum = IntField(default=0)
    avg_rating = FloatField(default=0.0)
    def update_rating(self, new_rating: int):
        self.total_ratings += 1
        self.rating_sum += new_rating
        self.avg_rating = round(self.rating_sum / self.total_ratings, 2)
        self.save()

