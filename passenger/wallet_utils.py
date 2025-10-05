from .model.wallet_model import Wallet, WalletTransaction
from decimal import Decimal
from datetime import datetime

def get_wallet(passenger_id):
    wallet = Wallet.objects(passenger_id=passenger_id).first()
    if not wallet:
        wallet = Wallet(passenger_id=passenger_id, balance=Decimal("0.00"))
        wallet.save()
    return wallet

def add_money(passenger_id, amount):
    wallet = get_wallet(passenger_id)
    wallet.balance += Decimal(amount)
    wallet.updated_at = datetime.utcnow()
    wallet.save()

    WalletTransaction(wallet=wallet, txn_type="add", amount=amount).save()
    return wallet.balance

def send_money(sender_id, receiver_id, amount):
    sender_wallet = get_wallet(sender_id)
    receiver_wallet = get_wallet(receiver_id)

    if sender_wallet.balance < Decimal(amount):
        raise ValueError("Insufficient balance")

    sender_wallet.balance -= Decimal(amount)
    sender_wallet.save()

    receiver_wallet.balance += Decimal(amount)
    receiver_wallet.save()

    WalletTransaction(wallet=sender_wallet, txn_type="send", amount=amount, to=receiver_id).save()
    WalletTransaction(wallet=receiver_wallet, txn_type="receive", amount=amount, from_user=sender_id).save()

    return sender_wallet.balance, receiver_wallet.balance

def get_transactions(passenger_id):
    wallet = get_wallet(passenger_id)
    return WalletTransaction.objects(wallet=wallet).order_by("-created_at")
