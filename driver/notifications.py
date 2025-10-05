from .m2 import Notifications
from twilio.rest import Client

TWILIO_SID = "your_twilio_sid"
TWILIO_AUTH = "your_twilio_auth_token"
TWILIO_PHONE = "+1234567890"  # Twilio phone number

client = Client(TWILIO_SID, TWILIO_AUTH)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"  # Use app-specific password if Gmail

def log_notification(driver, n_type, title, message):
    Notifications(
        driver=driver,
        type=n_type,
        title=title,
        message=message
    ).save()

def send_email_notification(to_email, subject, message, driver=None):
    try:
        msg = MIMEText(message, "plain")
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {to_email}")

        if driver:
            log_notification(driver, "Email", subject, message)

    except Exception as e:
        print(f"❌ Email error: {e}")

def send_sms_notification(to_phone, message, driver=None):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=to_phone
        )
        print(f"✅ SMS sent to {to_phone}")

        if driver:
            log_notification(driver, "SMS", "SMS Notification", message)

    except Exception as e:
        print(f"❌ SMS error: {e}")
