# admin_app/models.py
from mongoengine import Document, StringField, DateTimeField, DictField, FloatField,IntField,ListField, BooleanField, ReferenceField, EmailField
from datetime import datetime, timedelta

class AuditLog(Document):
    admin = StringField(required=True)
    action = StringField(required=True)
    user_id = StringField(required=True)
    details = StringField()
    timestamp = DateTimeField(default=datetime.utcnow)

from mongoengine import Document, StringField

class Admin(Document):
    username = StringField(required=True, unique=True)
    password = StringField(required=True)  # store hashed passwords
    email = EmailField(required=True)
    is_superuser=BooleanField(required=True)

class Config(Document):
    key = StringField(required=True, unique=True)
    value = DictField()

class AdminSettings(Document):
    daily_earning_cap = FloatField(default=1000.0)
    max_driving_hours = FloatField(default=10.0)




class RentalPricing(Document):
    # one doc per vehicle_type + tier (e.g., Car + tier1)
    vehicle_type = StringField(required=True)
    tier = StringField(default="tier1")               # tier1 / tier2 / tier3
    base_fare_per_hour = FloatField(default=0.0)
    base_fare_per_day = FloatField(default=0.0)
    vehicle_multiplier = FloatField(default=1.0)
    addons = DictField()          # e.g., {"GPS": 50, "Insurance": 100, "Driver":200}
    tax_percent = FloatField(default=18.0)
    commission_percent = FloatField(default=10.0)
    peak_hour_multiplier = FloatField(default=1.0)
    effective_from = DateTimeField()
    effective_to = DateTimeField()
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {"collection": "rental_pricing", "indexes": ["vehicle_type", "tier"]}


class EdgeCaseSettings(Document):
    daily_earning_cap = FloatField(default=0)
    max_rides_per_day = IntField(default=0)
    cancellation_penalty = FloatField(default=0)



class Complaint(Document):
    ride_id = ReferenceField("Ride", required=True)
    user_id = ReferenceField("User", required=True)
    user_role = StringField(choices=["rider", "driver"])

    category = StringField(max_length=50)   # e.g., "cancellation", "payment"
    details = StringField()

    auto_fee = FloatField(default=0.0)
    auto_reason = StringField()

    status = StringField(default="pending", choices=["pending", "resolved", "escalated"])
    override_action = StringField()
    applied_fee = FloatField(default=0.0)
    resolution_notes = StringField()

    resolved_by = ReferenceField("Admin", required=False)

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {"collection": "complaints"}

    def __str__(self):
        return f"Complaint({self.id}, {self.category}, {self.status})"


from datetime import datetime
from mongoengine import Document, StringField, FloatField, DateTimeField, ReferenceField

class AuditTrail(Document):
    complaint_id = ReferenceField("Complaint", required=True)
    admin_id = ReferenceField("Admin", required=False)

    action = StringField(max_length=100)   # system_auto_fee, override_refund_full, etc.
    notes = StringField()
    previous_fee = FloatField(default=0.0)
    new_fee = FloatField(default=0.0)
    timestamp = DateTimeField(default=datetime.utcnow)

    meta = {"collection": "audit_trail"}

    def __str__(self):
        return f"AuditTrail({self.complaint_id}, {self.action}, {self.timestamp})"

class CityTier(Document):
    city_name = StringField(required=True, unique=True)
    tier = StringField(choices=["Tier 1", "Tier 2", "Tier 3"], required=True)
    updated_at = DateTimeField(default=datetime.utcnow)

class FarePricing(Document):
    vehicle_type = StringField(required=True)  # Car, Bike, Van, etc.
    ride_type = StringField(required=True)     # Shared, Private, Cargo, Rental
    base_fare = FloatField(default=0.0)
    per_km = FloatField(default=0.0)
    per_minute = FloatField(default=0.0)
    tier = StringField(choices=["Tier 1", "Tier 2", "Tier 3"], required=True)
    updated_at = DateTimeField(default=datetime.utcnow)

from mongoengine import  IntField, DateTimeField, BooleanField, ListField

class Promotion(Document):
    promo_code = StringField(required=True, unique=True)
    discount_type = StringField(choices=['percentage', 'flat'], required=True)
    discount_value = FloatField(required=True)
    min_booking_amount = FloatField(default=0)
    max_discount = FloatField(default=0)
    expiration_date = DateTimeField(required=True)
    usage_limit_per_user = IntField(default=1)
    total_usage_limit = IntField(default=100)
    active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

class ReferralReward(Document):
    user_reward = FloatField(default=5)
    driver_reward = FloatField(default=10)
    active = BooleanField(default=True)
    updated_at = DateTimeField(default=datetime.utcnow)

class CommissionRule(Document):
    vehicle_type = StringField(required=True)  # e.g., Car, Van, Bike
    ride_type = StringField(required=True)     # e.g., On-Demand, Scheduled, Rental
    commission_percentage = FloatField(default=10.0)  # standard commission %
    first_time_user_extra = FloatField(default=2.0)   # extra commission for first-time rides
    promo_applies = BooleanField(default=True)        # discount/promo points affect commission
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

from datetime import datetime
from mongoengine import Document, StringField, IntField, FloatField, BooleanField, DateTimeField, ReferenceField, CASCADE

# ------------------------------
# Fare Rules & Audit
# ------------------------------

class FareRule(Document):
    city_tier = StringField(max_length=50, required=True)
    vehicle_type = StringField(max_length=50, required=True)
    ride_type = StringField(max_length=50, required=True)  # Shared, Private, On-Demand, Scheduled
    base_fare = FloatField(default=0)
    per_km = FloatField(default=0)
    per_minute = FloatField(default=0)
    surge_percentage = FloatField(default=0)
    platform_commission = FloatField(default=10)  # %
    active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

class FareRuleAudit(Document):
    fare_rule = ReferenceField(FareRule, reverse_delete_rule=CASCADE)
    changed_by = StringField(max_length=50)
    old_values = StringField()  # could store JSON as string
    new_values = StringField()
    timestamp = DateTimeField(default=datetime.utcnow)

# ------------------------------
# Referral System
# ------------------------------

class ReferralSetting(Document):
    user_reward = FloatField(default=5)   # ₹5 for rider referral
    driver_reward = FloatField(default=10)  # ₹10 for driver referral
    active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

class ReferralCode(Document):
    user_type = StringField(max_length=20, choices=['rider', 'driver'], required=True)
    user_id = IntField(required=True)
    code = StringField(max_length=20, unique=True, required=True)
    created_at = DateTimeField(default=datetime.utcnow)

class ReferralRewardLog(Document):
    referrer_id = IntField(required=True)
    referred_id = IntField(required=True)
    user_type = StringField(max_length=20, choices=['rider', 'driver'], required=True)
    reward_amount = FloatField(required=True)
    status = StringField(max_length=20, choices=['pending', 'credited', 'revoked'], default='pending')
    revoked_by_admin = BooleanField(default=False)
    revoked_reason = StringField(max_length=255, null=True)
    created_at = DateTimeField(default=datetime.utcnow)



class Transaction(Document):
    transaction_type = StringField(choices=['ride', 'rental', 'wallet_topup', 'driver_payout', 'refund'])
    user_id = StringField()
    user_type = StringField(choices=['rider','driver'])
    payment_method = StringField()
    amount = FloatField(default=0)
    platform_commission = FloatField(default=10)  # %
    status = StringField(choices=['pending','completed','failed'], default='pending')
    created_at = DateTimeField(default=datetime.utcnow)


    meta = {'collection': 'payments'}  # optional: your MongoDB collection name
    type = StringField(required=True, choices=['success', 'refund', 'failed', 'pending'])
    amount = FloatField(required=True)
    user_name = StringField(required=True)   # Rider or Driver name
    description = StringField()              # Optional description
    created_at = DateTimeField(default=datetime.utcnow)
    type = StringField(required=True, choices=['success', 'refund', 'failed', 'pending'])
    amount = FloatField(required=True)
    read = BooleanField(default=False)  # New field for "mark as read"


class RefundRequest(Document):
    booking_id = StringField(required=True)       # Ride or rental ID
    passenger_id = StringField(required=True)     # Passenger requesting refund
    driver_id = StringField()                     # If applicable
    amount_requested = FloatField(required=True)
    amount_approved = FloatField(default=0)
    reason = StringField()
    status = StringField(choices=['requested','approved','rejected','processed','partial'], default='requested')
    created_at = DateTimeField(default=datetime.utcnow)
    processed_at = DateTimeField()
    admin_note = StringField()

class RideRentalHistory(Document):
    passenger = StringField(required=True)
    driver = StringField(required=True)
    vehicle = StringField()
    pickup = StringField()
    drop = StringField()
    fare = FloatField()
    status = StringField(choices=["Completed", "Cancelled", "Ongoing"])
    ride_type = StringField(choices=["Ride", "Rental"])
    date = DateTimeField(default=datetime.utcnow)

class DriverPerformance:
    def __init__(self, driver_id, name, total_rides, total_rentals,
                 acceptance_rate, rejection_rate, avg_rating, earnings,
                 incentives, online_hours, utilization):
        self.driver_id = driver_id
        self.name = name
        self.total_rides = total_rides
        self.total_rentals = total_rentals
        self.acceptance_rate = acceptance_rate
        self.rejection_rate = rejection_rate
        self.avg_rating = avg_rating
        self.earnings = earnings
        self.incentives = incentives
        self.online_hours = online_hours
        self.utilization = utilization

from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField, BooleanField, IntField

class Notification(Document):
    target_users = ListField(StringField(choices=["passengers", "renters", "drivers", "all"]))
    notification_type = StringField(choices=["announcement", "promotion", "service_update", "maintenance"])
    delivery_methods = ListField(StringField(choices=["push", "email", "sms"]))
    message = StringField(required=True)
    scheduled_time = DateTimeField(default=datetime.utcnow)
    sent = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    
    # Tracking
    total_users = IntField(default=0)
    delivered_count = IntField(default=0)
    read_count = IntField(default=0)
    passenger_id = StringField(required=True)        # who receives the notification
    category = StringField(required=True)            # ride / rental / payment
    event = StringField(required=True)               # e.g. "ride_confirmed", "driver_arriving"
    title = StringField(required=True)
    message = StringField()
    data = DictField()                                # structured payload e.g. {"ride_id": "...", "driver": {...}}
    is_read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)

from datetime import datetime
from mongoengine import Document, StringField, DateTimeField, BooleanField

class AdminAlert(Document):
    alert_type = StringField(choices=[
        "ride_issue",
        "dispute",
        "payment_failure",
        "offline_driver"
    ], required=True)
    severity = StringField(choices=["high", "medium", "low"], default="medium")
    message = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    resolved = BooleanField(default=False)
    resolved_at = DateTimeField()
