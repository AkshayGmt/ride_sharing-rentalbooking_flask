from mongoengine import Document, StringField, DecimalField, DateTimeField, ReferenceField
from datetime import datetime
from decimal import Decimal

class Wallet(Document):
    passenger_id = StringField(required=True, unique=True)
    balance = DecimalField(precision=2, default=Decimal("0.00"))
    updated_at = DateTimeField(default=datetime.utcnow)

class WalletTransaction(Document):
    wallet = ReferenceField(Wallet, required=True)
    txn_type = StringField(required=True, choices=["add", "send", "receive"])
    amount = DecimalField(precision=2, required=True)
    to = StringField()     # receiver id (for send)
    from_user = StringField()  # sender id (for receive)
    status = StringField(default="success")  # success/failure
    created_at = DateTimeField(default=datetime.utcnow)
