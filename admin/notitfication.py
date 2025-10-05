import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"  # Use app-specific password if Gmail

def send_email_notification(to_email, subject, message):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")


from twilio.rest import Client

TWILIO_SID = "your_twilio_sid"
TWILIO_AUTH = "your_twilio_auth_token"
TWILIO_PHONE = "+1234567890"  # Twilio phone number

client = Client(TWILIO_SID, TWILIO_AUTH)

def send_sms_notification(to_phone, message):
    try:
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=to_phone
        )
        print(f"✅ SMS sent to {to_phone}")
    except Exception as e:
        print(f"❌ Error sending SMS: {e}")

import time, threading
from passenger.model.ride_model import Ride 
from driver.drivermodel import Driver

def dispatch_ride(ride_id):
    ride = Ride.objects.get(id=ride_id)
    available_drivers = Driver.objects.filter(
        status="available",
        vehicle_type=ride.vehicle_type
    ).order_by("distance")[:3]  # take closest 3

    def try_driver(index=0):
        if index >= len(available_drivers):
            ride.update(status="no_driver")
            # notify passenger to retry
            return

        driver = available_drivers[index]
        ride.update(status="waiting_driver", candidate_driver=driver.id)

        # notify driver (push / socket)
        notify_driver(driver, ride)

        # wait for N seconds
        def wait_response():
            time.sleep(15)  # 15 second timeout
            ride.reload()
            if ride.status == "waiting_driver":  
                # driver did not respond
                try_driver(index + 1)

        threading.Thread(target=wait_response).start()

    try_driver()



