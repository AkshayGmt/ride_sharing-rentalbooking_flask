class Config:
    SECRET_KEY = "3b340eb4de50295ba76cec8d8743581528d6101891039812c45503ad33ddc0c5"


razorpay_client = razorpay.Client(auth=(
    os.getenv("RAZORPAY_KEY_ID"), 
    os.getenv("RAZORPAY_SECRET")
))