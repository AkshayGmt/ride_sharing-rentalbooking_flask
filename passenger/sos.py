# utils/sos.py
import os
from twilio.rest import Client

TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN")
TWILIO_FROM = os.environ.get("TWILIO_FROM")  # Twilio phone number

def send_sos_sms(phone, passenger_name, lat, lng):
    if not TWILIO_SID or not TWILIO_TOKEN or not TWILIO_FROM:
        raise RuntimeError("Twilio not configured")
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    loc_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
    body = f"SOS from {passenger_name}. Live location: {loc_link}"
    message = client.messages.create(body=body, from_=TWILIO_FROM, to=phone)
    return message.sid

def place_call(phone, twiml_url=None):
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    call = client.calls.create(to=phone, from_=TWILIO_FROM, url=twiml_url)  # TwiML instructs call flow
    return call.sid
