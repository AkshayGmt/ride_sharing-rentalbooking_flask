from flask import Blueprint, render_template, request, redirect, url_for, flash,session
import random
from app import db
from mongoengine import Document, StringField, EmailField,ReferenceField
from .drivermodel import Driver
from werkzeug.security import generate_password_hash,check_password_hash

driver_bp = Blueprint("driver", __name__, template_folder="templates")
otp_store_driver = {}

@driver_bp.route("/register", methods=["GET", "POST"])
def register_driver():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        phone = request.form.get("phone")

        #license_number = request.form.get("license_number")
        referral_code = request.form.get("referral_code") or None  # ✅ optional

  # ✅ Check if user already exists
        existing = Driver.objects(
            __raw__={"$or": [
                {"email": email},
                {"phone": phone},
                {"username": username}
            ]}
        ).first()

        if existing:
            flash("⚠️ You are already registered! Please login.", "error")
            return redirect(url_for("driver.login_driver"))

        if Driver.objects(username=username).first() or Driver.objects(email=email).first():
            flash("Username or Email already exists!", "error")
            return redirect(url_for("driver.register_driver"))

        Driver(name=name, email=email, username=username, password=password,referral_code=referral_code).save()
        flash("Driver Registered Successfully!", "success")
        return redirect(url_for("driver.login_driver"))

    return render_template("driver_register.html")


@driver_bp.route("/login", methods=["GET", "POST"])
def login_driver():
    if request.method == "POST":
        method = request.form.get("method")
        if method == "email":
            email = request.form.get("email")
            password = request.form.get("password")
            user = Driver.objects(email=email).first()
            if user and check_password_hash(user.password, password):
                session["driver_id"] = str(user.id)
                flash("Login Successful", "success")
                return redirect(url_for("driver.driver_dashboard"))
            else:
                flash("Invalid Email or Password", "error")
        elif method == "phone":
            phone = request.form.get("phone")
            user = Driver.objects(phone=phone).first()
            if user:
                otp = random.randint(100000, 999999)
                otp_store_driver[phone] = otp
                print(f"Driver OTP for {phone}: {otp}")  # In production, send via SMS/email
                return redirect(url_for("driver.verify_driver_otp", phone=phone))
            else:
                flash("Phone not registered. Please register first.", "error")
    return render_template("driver_login.html")


@driver_bp.route("/verify-otp/<phone>", methods=["GET", "POST"])
def verify_driver_otp(phone):
    if request.method == "POST":
        user_otp = request.form.get("otp")
        if str(otp_store_driver.get(phone)) == str(user_otp):
            user = Driver.objects(phone=phone).first()
            session["driver_id"] = str(user.id)
            otp_store_driver.pop(phone, None)
            flash("Login Successful with OTP", "success")
            return redirect(url_for("driver.driver_dashboard"))
        else:
            flash("Invalid OTP", "error")
    return render_template("driver_verify_otp.html", phone=phone)



@driver_bp.route("/dashboard")
def driver_dashboard():
    driver_id = session.get("driver_id")
    if not driver_id:
        return redirect(url_for("driver.login_driver"))  # ✅ check session
    
    driver = Driver.objects.get(id=driver_id)
    return render_template("driver_dashboard.html", driver=driver)



from flask import Blueprint, render_template, request, redirect, url_for, flash, session,jsonify
from werkzeug.utils import secure_filename
import os
from .model import DriverDocuments, InsuranceDocument
from werkzeug.utils import secure_filename
import os
from datetime import datetime




UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    if file and allowed_file(file.filename):
        if len(file.read()) > MAX_FILE_SIZE:
            raise ValueError("File too large")
        file.seek(0)
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        return path
    else:
        raise ValueError("Invalid file type")


@driver_bp.route("/upload_documents", methods=["GET", "POST"])
def upload_documents():
    if "driver_id" not in session:
        flash("Please login first", "error")
        return redirect(url_for("driver.login_driver"))

    if request.method == "POST":
        try:
            driver_id = session["driver_id"]

            # Mandatory files
            driving_license_path = save_file(request.files.get("driving_license"))
            vehicle_rc_path = save_file(request.files.get("vehicle_rc"))
            id_proof_path = save_file(request.files.get("id_proof"))
            insurance_file_path = save_file(request.files.get("insurance_file"))

            # Optional files
            profile_photo_path = None
            police_clearance_path = None
            if "profile_photo" in request.files:
                profile_photo_path = save_file(request.files.get("profile_photo"))
            if "police_clearance" in request.files:
                police_clearance_path = save_file(request.files.get("police_clearance"))

            # Create insurance document
            insurance_doc = InsuranceDocument(
                insurance_type=request.form.get("insurance_type"),
                provider=request.form.get("provider"),
                policy_number=request.form.get("policy_number"),
                policy_start=datetime.strptime(request.form.get("policy_start"), "%Y-%m-%d"),
                policy_expiry=datetime.strptime(request.form.get("policy_expiry"), "%Y-%m-%d"),
                vehicle_number=request.form.get("vehicle_number"),
                insurance_file=insurance_file_path
            )

            # Save driver documents
            doc = DriverDocuments(
                driver_id=driver_id,
                driving_license=driving_license_path,
                vehicle_rc=vehicle_rc_path,
                id_proof=id_proof_path,
                insurance=insurance_doc,
                profile_photo=profile_photo_path,
                police_clearance=police_clearance_path
            )
            doc.save()
            flash("Documents uploaded successfully!", "success")
            return redirect(url_for("driver.driver_dashboard"))

        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            #return redirect(url_for("driver.upload_documents"))
            return redirect(url_for("driver.driver_dashboard"))

    return render_template("upload_documents.html")



UPLOAD_FOLDER = "static/uploads/vehicles"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    if file and allowed_file(file.filename):
        if len(file.read()) > MAX_FILE_SIZE:
            raise ValueError("File too large")
        file.seek(0)
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        return path
    else:
        raise ValueError("Invalid file type")
from .model import Vehicle

@driver_bp.route("/vehicle_registration", methods=["GET", "POST"])
def vehicle_registration():
    if "driver_id" not in session:
        flash("Please login first", "error")
        return redirect(url_for("driver.login_driver"))

    if request.method == "POST":
        try:
            driver_id = session["driver_id"]
            vehicle_type = request.form.get("vehicle_type")
            make_model = request.form.get("make_model")
            year_of_manufacture = int(request.form.get("year_of_manufacture"))
            vehicle_number = request.form.get("vehicle_number")
            capacity = request.form.get("capacity")

            # Upload multiple images
            image_files = request.files.getlist("vehicle_images")
            image_paths = []
            for f in image_files:
                if f.filename:
                    path = save_file(f)
                    image_paths.append(path)

            vehicle = Vehicle(
                driver_id=driver_id,
                vehicle_type=vehicle_type,
                make_model=make_model,
                year_of_manufacture=year_of_manufacture,
                vehicle_number=vehicle_number,
                capacity=capacity,
                vehicle_images=image_paths
            )
            vehicle.save()
            flash("Vehicle registered successfully!", "success")
            return redirect(url_for("driver.driver_dashboard"))

        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("driver.vehicle_registration"))

    return render_template("vehicle_registration.html")

from .model import DriverSubscription
from .utils import can_accept_ride, check_daily_reset
from datetime import datetime, timedelta
import razorpay
@driver_bp.route("/subscription", methods=["GET", "POST"])
def driver_subscription():
    if "driver_id" not in session:
        flash("Please login first", "error")
        return redirect(url_for("driver.login_driver"))

    driver_id = session["driver_id"]
    subscription = DriverSubscription.objects(driver_id=driver_id).first()
    if not subscription:
        subscription = DriverSubscription(driver_id=driver_id)
        subscription.save()

    # Fetch wallet balance
    wallet_earnings = DriverEarning.objects(driver_id=driver_id)
    wallet_balance = sum(e.wallet_topup for e in wallet_earnings) - sum(e.total_amount for e in wallet_earnings)  # simplify: total top-ups minus payouts

    if request.method == "POST":
        action = request.form.get("action")
        if action == "upgrade_premium":
            subscription_price = 500  # Example: Premium subscription price

            if wallet_balance >= subscription_price:
                # Deduct from wallet
                DriverEarning(driver_id=driver_id, wallet_topup=-subscription_price).save()
                subscription.subscription_type = "Premium"
                subscription.premium_expiry = datetime.datetime.utcnow() + timedelta(days=30)
                subscription.save()
                flash("Premium subscription activated using wallet!", "success")
            else:
                # Remaining amount to pay via Razorpay
                amount_to_pay = subscription_price - wallet_balance
                # Create Razorpay order
                order = razorpay_client.order.create(dict(
                    amount=int(amount_to_pay * 100),
                    currency="INR",
                    payment_capture="1"
                ))

                # Optionally store pending wallet deduction
                session["pending_wallet_deduction"] = wallet_balance

                return render_template("razorpay_checkout.html",
                                       order=order,
                                       key_id=os.getenv("RAZORPAY_KEY_ID"),
                                       amount=amount_to_pay,
                                       driver_id=driver_id,
                                       subscription="premium")

        elif action == "vehicle_addon":
            addon_price = 200  # Example: Vehicle addon price
            vehicle_type = request.form.get("addon_vehicle_type")

            if wallet_balance >= addon_price:
                DriverEarning(driver_id=driver_id, wallet_topup=-addon_price).save()
                subscription.vehicle_addon = True
                subscription.addon_vehicle_type = vehicle_type
                subscription.save()
                flash(f"Vehicle addon activated using wallet!", "success")
            else:
                amount_to_pay = addon_price - wallet_balance
                order = razorpay_client.order.create(dict(
                    amount=int(amount_to_pay * 100),
                    currency="INR",
                    payment_capture="1"
                ))

                session["pending_wallet_deduction"] = wallet_balance

                return render_template("razorpay_checkout.html",
                                       order=order,
                                       key_id=os.getenv("RAZORPAY_KEY_ID"),
                                       amount=amount_to_pay,
                                       driver_id=driver_id,
                                       subscription="vehicle_addon",
                                       addon_vehicle_type=vehicle_type)

        return redirect(url_for("driver.driver_subscription"))

    check_daily_reset(subscription)
    return render_template("driver_subscription.html", subscription=subscription, wallet_balance=wallet_balance)

@driver_bp.route("/subscription/payment-success", methods=["POST"])
def subscription_payment_success():
    data = request.form
    driver_id = session.get("driver_id")
    subscription_type = data.get("subscription")
    addon_vehicle_type = data.get("addon_vehicle_type", None)

    # Verify Razorpay payment signature
    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]
        })
    except:
        flash("Payment verification failed!", "error")
        return redirect(url_for("driver.driver_subscription"))

    # Deduct wallet if any pending
    pending_wallet = session.get("pending_wallet_deduction", 0)
    if pending_wallet > 0:
        DriverEarning(driver_id=driver_id, wallet_topup=-pending_wallet).save()
        session.pop("pending_wallet_deduction")

    # Activate subscription
    subscription = DriverSubscription.objects(driver_id=driver_id).first()
    if subscription_type == "premium":
        subscription.subscription_type = "Premium"
        subscription.premium_expiry = datetime.datetime.utcnow() + timedelta(days=30)
    elif subscription_type == "vehicle_addon":
        subscription.vehicle_addon = True
        subscription.addon_vehicle_type = addon_vehicle_type
    subscription.save()

    flash("Subscription activated successfully!", "success")
    return redirect(url_for("driver.driver_subscription"))


from passenger.model.ride_model import  RideBooking
from socket_event import driver_accepted, driver_rejected, socketio

@driver_bp.route("shared_rides/<ride_id>/")
def shared_rides():
    if "driver_id" not in session:
        flash("Please login first", "error")
        return redirect(url_for("driver.login_driver"))

    rides = RideBooking.objects(status="pending", driver_id=None)
    return render_template("driver_shared_rides.html", trips=trips)


# @driver_bp.route("/accept_ride/<ride_id>", methods=["POST"])
# def accept_ride(ride_id):
#     # verify driver ownership etc
#     driver_id = request.form.get("driver_id")
#     driver = Driver.objects.get(id=driver_id)
#     driver_accepted(ride_id, driver)
#     flash("Ride accepted")
#     return redirect(url_for("driver.driver_dashboard"))




@driver_bp.route("/accept-trip/<ride_id>", methods=["POST"])
def accept_ride(ride_id):
    driver_id = session.get("driver_id")
    trip = RideBooking.objects(id=trip_id).first()
    if trip and not trip.driver_id:
        trip.driver_id = driver_id
        trip.status = "ongoing"
        trip.save()

        # Update rides inside trip
        for ride_id in trip.ride_id:
            ride = RideBooking.objects(id=ride_id).first()
            ride.driver_assigned = driver_id
            ride.save()

        flash("You have accepted this shared trip!", "success")
    return redirect(url_for("driver.shared_trips"))


@driver_bp.route("/reject_ride/<ride_id>", methods=["POST"])
def reject_ride(ride_id):
    driver_id = request.form.get("driver_id")
    driver_rejected(ride_id, driver_id)
    flash("Ride rejected")
    return redirect(url_for("driver.driver_dashboard"))






@driver_bp.route("/ride/<ride_id>")
def manage_ride(ride_id):
    ride = RideBooking.objects.get(id=ride_id)
    return render_template("driver_manage_ride.html", ride=ride)



@driver_bp.route("/ride/<ride_id>/start", methods=["POST"])
def start_ride(ride_id):
    ride = RideBooking.objects.get(id=ride_id)
    ride.status = "in_progress"
    ride.start_time = datetime.utcnow()
    ride.save()

    socketio.emit("ride_update", {"status": "in_progress"}, room=str(ride.id))
    flash("Ride started")
    return redirect(url_for("driver.manage_ride", ride_id=ride_id))

#from socket_event import complete_ride
from socket_event import complete_ride
# @driver_bp.route("/ride/<ride_id>/complete", methods=["POST"])
# def complete_ride_route(ride_id):
#     ride = .objects.get(id=ride_id)
#     ride.status = "completed"
#     ride.end_time = datetime.utcnow()

#     # Calculate fare (basic example: Rs.10/km + Rs.2/min)
#     import math
#     duration_minutes = (ride.end_time - ride.start_time).seconds // 60
#     distance_km = 10  # placeholder – ideally compute via Maps API
#     ride.fare = (distance_km * 10) + (duration_minutes * 2)

#     ride.save()

#     # trigger auto-delete of chat + notify passenger
   

#     flash(f"Ride completed. Fare: ₹{ride.fare}")
#     return redirect(url_for("driver.dashboard"))


@driver_bp.route("/ride/<ride_id>/complete", methods=["POST"])
def complete_ride(ride_id):
    trip = RideBooking.objects(id=ride_id).first()
    if not trip:
        flash("Trip not found", "error")
        return redirect(url_for("driver.shared_trips"))

    trip.status = "completed"
    trip.save()

    # Driver earning = total fare collected
    driver_earning = trip.total_fare
    # add to driver wallet
    driver = Driver.objects(id=trip.driver_id).first()
    driver.wallet_balance += driver_earning
    driver.save()
    complete_ride(ride_id)

    flash(f"Trip completed! You earned ₹{driver_earning}", "success")
    return redirect(url_for("driver.dashboard"))

# from app import notify_driver_accept,notify_driver_reject
# from passenger.model import R
# @driver_bp.route("/accept_ride/<ride_id>", methods=["POST"])
# def accept_ride(ride_id):
#     ride = RideBooking.objects.get(id=ride_id)
#     ride.status = "confirmed"
#     ride.save()

#     # real-time notify passenger
#     notify_driver_accept(ride.id, ride.assigned_driver.name)

#     return redirect(url_for("driver.driver_dashboard"))

# @driver_bp.route("/reject_ride/<ride_id>", methods=["POST"])
# def reject_ride(ride_id):
#     ride = RideBooking.objects.get(id=ride_id)

#     if ride.assigned_driver:
#         ride.assigned_driver.is_available = True
#         ride.assigned_driver.save()

#     ride.status = "driver_rejected"
#     ride.assigned_driver = None
#     ride.save()

#     # real-time notify passenger
#     notify_driver_reject(ride.id)

#     return redirect(url_for("driver.driver_dashboard"))


from passenger.model.rental_model import RentalBooking
@driver_bp.route("/ride_management")
def ride_management():
    return render_template("ride_management.html")



from bson import ObjectId, errors

@driver_bp.route("/navigation/<ride_id>")
def driver_navigation(ride_id):
    try:
        ride = RideBooking.objects(id=ObjectId(ride_id)).first()
    except errors.InvalidId:
        return "❌ Invalid Ride ID", 400

    if not ride:
        return "Ride not found", 404

    return render_template("driver_navigation.html", ride=ride)

from .model import RideRating
from passenger.notification import notify_driver, notify_passenger
@driver_bp.route("/ride/<int:ride_id>/rate", methods=["POST"])
def rate_driver(ride_id):
    data = request.json
    rating_val = data.get("rating")
    comments = data.get("comments", "")
    passenger_id = data.get("passenger_id")

    ride = RideBooking.objects.get(id=ride_id)
    driver = Driver.objects.get(id=ride.driver_id)

    # save rating
    ride_rating = RideRating(
        ride=ride,
        driver=driver,
        passenger_id=passenger_id,
        rating=rating_val,
        comments=comments
    )
    ride_rating.save()

    # update driver's average rating
    all_ratings = RideRating.objects(driver=driver)
    total = all_ratings.count()
    avg = sum(r.rating for r in all_ratings) / total
    driver.total_ratings = total
    driver.avg_rating = round(avg, 2)
    driver.save()

    # notify driver via socket
    notify_driver(driver, f"You received a new rating: {rating_val}⭐")

    #return jsonify({"success": True, "avg_rating": driver.avg_rating, "total_ratings": driver.total_ratings, ride_id=ride_id})
    return render_template("rate_driver.html", 
                       avg_rating=driver.avg_rating, 
                       total_ratings=driver.total_ratings, 
                       ride_id=ride_id)

@driver_bp.route("/ride/ride-status")
def ride_status():
    return render_template("driver_ride_status.html")
@driver_bp.route("/ride/<ride_id>/update_status", methods=["POST"])
def update_ride_status(ride_id):
    data = request.json
    new_status = data.get("driver_status")  # pending, en_route, started, completed

    ride = RideBooking.objects.get(id=ride_id)
    ride.driver_status = new_status
    ride.save()

    # Notify passenger in real-time
    notify_passenger(ride.passenger_id, f"Driver status updated: {new_status}")

    #return jsonify({"success": True, "driver_status": new_status})
    return render_template("driver_ride_status.html")



@driver_bp.route('/rental-management')
def rental_management_dashboard():
    return render_template('rental_management.html')




@driver_bp.route('/rental/vehicle_handover')
def vehicle_handover():
    current_driver = get_current_driver()
    if not current_driver:
        flash("Please login first.", "error")
        return redirect(url_for('driver.login_driver'))
    # Show driver-assigned rentals pending handover
    rentals = RentalBooking.objects(driver=current_driver, with_driver=True, handover_done=False)
    return render_template('vehicle_handover.html', rentals=rentals)

@driver_bp.route('/rental/vehicle_handover/<rental_id>/complete', methods=['POST'])
def complete_handover(rental_id):
    rental = RentalBooking.objects.get(id=rental_id)
    
    # Capture timestamp and GPS location
    rental.handover_done = True
    rental.handover_timestamp = datetime.datetime.utcnow()
    rental.handover_gps = request.form.get('gps_coords')  # "lat,long"
    
    # Optional photo upload
    if 'handover_photo' in request.files:
        photo = request.files['handover_photo']
        filename = secure_filename(photo.filename)
        photo.save(f"static/uploads/{filename}")
        rental.handover_photo = f"uploads/{filename}"
    
    rental.status = "Ongoing"
    rental.save()
    
    flash("Vehicle handover completed successfully.", "success")
    return redirect(url_for('driver.vehicle_handover'))

from .utils import get_current_driver,calculate_eta,check_route_deviation,notify_admin
@driver_bp.route('/rental/tracking')
def rental_tracking():
    current_driver = get_current_driver()
    if not current_driver:
        flash("Please login first.", "error")
        return redirect(url_for('driver.login_driver'))
    # Show ongoing rentals for this driver
    rentals = RentalBooking.objects(driver=current_driver, status="Ongoing")
    return render_template('rental_tracking.html', rentals=rentals)

@driver_bp.route('/rental/update_location/<rental_id>', methods=['POST'])
def update_location(rental_id):
    current_driver = get_current_driver()
    rental = RentalBooking.objects.get(id=rental_id, driver=current_driver)
    gps = request.form.get('gps_coords')
    rental.current_gps = gps

    # Calculate ETA
    rental.eta = calculate_eta(rental)
    

    # Check route deviation
    if check_route_deviation(rental):
        rental.deviation_alert = True
        notify_admin(f"Rental {rental.id} deviated from allowed route!")

    rental.save()
    
    return "OK"



@driver_bp.route('/rental/return/<rental_id>', methods=['POST'])
def complete_return(rental_id):
    rental = RentalBooking.objects.get(id=rental_id)
    
    rental.return_done = True
    rental.return_timestamp = datetime.datetime.utcnow()
    rental.return_gps = request.form.get("gps_coords")
    rental.return_condition = request.form.get("condition")

    # Calculate extra charges (late return)
    if rental.return_timestamp > rental.end_time:
        extra_hours = (rental.return_timestamp - rental.end_time).total_seconds() / 3600
        late_fee = extra_hours * 100  # example: ₹100 per extra hour
    else:
        late_fee = 0

    rental.final_fare = rental.fare + late_fee
    rental.status = "Completed"
    rental.save()

    flash(f"Vehicle returned. Final Fare: ₹{rental.final_fare}", "success")
    return redirect(url_for('driver.rental_management_dashboard'))

@driver_bp.route('/rental/approve_extension/<rental_id>', methods=['POST'])
def approve_extension(rental_id):
    rental = RentalBooking.objects.get(id=rental_id)
    if not rental.extension_requested:
        flash("No extension request found.", "error")
        return redirect(url_for('driver.rental_management_dashboard'))

    rental.end_time = rental.extension_new_end
    rental.fare = rental.extension_fare
    rental.extension_approved = True
    rental.extension_requested = False
    rental.save()

    flash("Extension approved and schedule updated.", "success")
    return redirect(url_for('driver.rental_management_dashboard'))

@driver_bp.route('/rental/returns_extensions', methods=["GET", "POST"])
def returns_extensions():
    if request.method == "POST":
        condition = request.form.get("condition")
        gps_coords = request.form.get("gps_coords")

        if condition == "Good":
            # ✅ Directly process return
            # (Here you can update DB, mark vehicle as returned, etc.)
            flash("Vehicle returned successfully!", "success")
            return redirect(url_for("driver.rental_management_dashboard"))  # example redirect

        elif condition == "Damaged":
            # 🚨 If damaged, go to extension/inspection page
            flash("Vehicle reported as Damaged, requires inspection.", "warning")
            return redirect(url_for("driver.rental_management_dashboard"))  # example extension flow

    return render_template("extension_return.html")






from flask import Blueprint, render_template, request, redirect, url_for, flash
from .earn_model import DriverEarning, DriverPayout
import datetime


# Earnings dashboard
@driver_bp.route('/earnings')

def earnings_dashboard():
    driver_id = session.get("driver_id")  # fetch from session
    if not driver_id:
        flash("Please login first", "error")
        return redirect(url_for("driver.login_driver"))

    # Fetch all earnings (ride + wallet)
    earnings = DriverEarning.objects(driver_id=driver_id)

    today = datetime.date.today()
    week_no = today.isocalendar()[1]

    # Daily / Weekly / Monthly totals (combined)
    daily = sum((e.total_amount or 0) + (e.wallet_topup or 0) for e in earnings if e.created_at.date() == today)
    weekly = sum((e.total_amount or 0) + (e.wallet_topup or 0) for e in earnings if e.created_at.isocalendar()[1] == week_no)
    monthly = sum((e.total_amount or 0) + (e.wallet_topup or 0) for e in earnings if e.created_at.month == today.month)

    # Prepare breakdown for chart
    earnings_day = [
        {"created_at": e.created_at, "total_amount": (e.total_amount or 0) + (e.wallet_topup or 0)}
        for e in earnings
    ]
    earnings_week = [
        {"week": e.created_at.isocalendar()[1], "total_amount": (e.total_amount or 0) + (e.wallet_topup or 0)}
        for e in earnings
    ]
    earnings_month = [
        {"month_name": e.created_at.strftime("%b"), "total_amount": (e.total_amount or 0) + (e.wallet_topup or 0)}
        for e in earnings
    ]

    return render_template("driver_earnings.html",
                           earnings=earnings,
                           daily=daily,
                           weekly=weekly,
                           monthly=monthly,
                           earnings_day=earnings_day,
                           earnings_week=earnings_week,
                           earnings_month=earnings_month)


@driver_bp.route("/add-wallet-money", methods=["POST"])
def add_wallet_money():
    if "driver_id" not in session:
        flash("Please login first", "error")
        return redirect(url_for("driver.login_driver"))

    driver_id = session["driver_id"]
    amount = int(request.form.get("amount"))

    # Create Razorpay order (amount is in paise)
    order = razorpay_client.order.create(dict(
        amount=amount * 100,
        currency="INR",
        payment_capture="1"
    ))

    # Save transaction in DB (pending status)
    db.driver_wallet.insert_one({
        "driver_id": driver_id,
        "order_id": order["id"],
        "amount": amount,
        "status": "created",
        "created_at": datetime.datetime.utcnow()
    })

    # Redirect to Razorpay checkout page
    return render_template("wallet_payment.html", 
                           order=order, 
                           key_id=os.getenv("RAZORPAY_KEY_ID"),
                           amount=amount,
                           driver_id=driver_id)


# ✅ Webhook/Callback to verify payment
@driver_bp.route("/wallet/payment-success", methods=["POST"])
def wallet_payment_success():
    data = request.form
    payment_id = data.get("razorpay_payment_id")
    order_id = data.get("razorpay_order_id")
    signature = data.get("razorpay_signature")

    # Verify signature
    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        })
    except:
        flash("Payment verification failed!", "error")
        return redirect(url_for("driver.earnings_dashboard"))

    # ✅ Update DB: mark success and update wallet
    txn = db.driver_wallet.find_one({"order_id": order_id})
    if txn:
        db.driver_wallet.update_one({"order_id": order_id}, {"$set": {"status": "paid"}})

        # Add money to DriverEarning wallet_topup
        DriverEarning(
            driver_id=txn["driver_id"],
            wallet_topup=txn["amount"],
            created_at=datetime.datetime.utcnow()
        ).save()

    flash("Wallet money added successfully!", "success")
    return redirect(url_for("driver.earnings_dashboard"))
@driver_bp.route("/driver/wallet", methods=["GET", "POST"])
def driver_wallet():
    if "driver_id" not in session:
        return redirect(url_for("driver.login_driver"))

    driver = db.drivers.find_one({"_id": ObjectId(session["driver_id"])})

    if request.method == "POST":
        amount = int(request.form.get("amount", 0))
        if amount < 100:
            flash("Minimum add money is ₹100", "error")
            return redirect(url_for("driver.driver_wallet"))

        order = razorpay_client.order.create(dict(
            amount=amount * 100,  # Razorpay needs paise
            currency="INR",
            receipt=f"wallet_{driver['_id']}_{datetime.datetime.utcnow().timestamp()}",
            payment_capture="1"
        ))

        # Save payment record
        db.wallet_transactions.insert_one({
            "driver_id": str(driver["_id"]),
            "order_id": order["id"],
            "amount": amount,
            "currency": "INR",
            "status": "created",
            "type": "wallet_topup",
            "created_at": datetime.datetime.utcnow()
        })

        # Redirect to payment page
        return render_template("wallet_payment.html",
                               order=order,
                               driver=driver,
                               key_id=os.getenv("RAZORPAY_KEY_ID"))

    return render_template("wallet.html", driver=driver)


# ✅ Webhook / success route
@driver_bp.route("/driver/wallet/success", methods=["POST"])
def wallet_success():
    data = request.form
    order_id = data.get("razorpay_order_id")
    payment_id = data.get("razorpay_payment_id")
    signature = data.get("razorpay_signature")

    try:
        # Verify payment
        params_dict = {
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        }
        razorpay_client.utility.verify_payment_signature(params_dict)

        # Update wallet
        txn = db.wallet_transactions.find_one({"order_id": order_id})
        if txn and txn["status"] == "created":
            db.wallet_transactions.update_one({"order_id": order_id}, {
                "$set": {"status": "success", "payment_id": payment_id}
            })
            db.drivers.update_one({"_id": ObjectId(txn["driver_id"])}, {
                "$inc": {"wallet_balance": txn["amount"]}
            })

        flash("Wallet topped up successfully!", "success")
    except:
        flash("Payment verification failed", "error")

    return redirect(url_for("driver.driver_wallet"))

# Request payout
@driver_bp.route("/payout/request", methods=["POST"])
def request_payout():
    driver_id = "123"  # TODO: fetch from session
    amount = float(request.form.get("amount"))
    method = request.form.get("method")

    payout = DriverPayout(driver_id=driver_id, amount=amount, method=method)
    payout.save()
    flash("✅ Payout request submitted!", "success")
    return redirect(url_for("driver.earnings_dashboard"))


# Payout history
@driver_bp.route("/payout/history")
def payout_history():
    driver_id = "123"  # TODO: fetch from session
    history = DriverPayout.objects(driver_id=driver_id)
    return render_template("driver_payout_history.html", history=history)





from flask import Blueprint, render_template, request, jsonify
from flask_socketio import emit
from .drivernotification import DriverNotification


# Get all notifications
@driver_bp.route("/notifications")
def notifications_dashboard():
    driver_id = session.get("driver_id")
    if not driver_id:
        flash("Please log in first.", "danger")
        return redirect(url_for("driver.login"))
    notifications = DriverNotification.objects(driver_id=driver_id).order_by("-created_at")
    return render_template("driver_notification.html", notifications=notifications)

# API to mark as read
@driver_bp.route("/notifications/read/<notif_id>", methods=["POST"])
def mark_notification_read(notif_id):
    notif = DriverNotification.objects(id=notif_id).first()
    if notif:
        notif.is_read = True
        notif.save()
    return jsonify({"success": True})

# Utility function to send notification (push + DB)
def send_driver_notification(driver_id, title, message, notif_type="system"):
    # Save in DB
    notif = DriverNotification(
        driver_id=driver_id, title=title, message=message, type=notif_type
    )
    notif.save()

    # Push to Socket.IO
    emit("driver_notification", {
        "title": title,
        "message": message,
        "type": notif_type,
        "created_at": notif.created_at.strftime("%Y-%m-%d %H:%M")
    }, to=f"driver_{driver_id}", namespace="/notifications")

    return notif





@driver_bp.route("/settings", methods=["GET", "POST"])
def driver_settings():
    driver_id = session.get("driver_id")
    if not driver_id:
        flash("Please log in first.", "danger")
        return redirect(url_for("driver.login"))

    driver = Driver.objects(id=driver_id).first()

    if request.method == "POST":
        driver.name = request.form.get("name")
        driver.email = request.form.get("email")
        driver.phone = request.form.get("phone")
        driver.vehicle_type = request.form.get("vehicle_type")
        driver.vehicle_number = request.form.get("vehicle_number")
        driver.license_number = request.form.get("license_number")
        driver.address = request.form.get("address")
        driver.save()
        flash("✅ Profile updated successfully!", "success")
        return redirect(url_for("driver.driver_settings"))

    return render_template("driver_settings.html", driver=driver)


# broadcast driver updates
@driver_bp.route('/update_location', methods=['POST'])
def driver_update_location():
    driver_id = session.get("driver_id")
    lat = request.json.get("latitude")
    lon = request.json.get("longitude")
    online = request.json.get("online")

    driver = Driver.objects(id=driver_id).first()
    if driver:
        driver.latitude = lat
        driver.longitude = lon
        driver.online = online
        driver.save()

        # push to admin dashboard instantly
        socketio.emit("driver_update", {
            "id": str(driver.id),
            "name": driver.name,
            "latitude": lat,
            "longitude": lon,
            "online": online,
            "active_ride_id": driver.active_ride_id,
            "rides_completed": driver.rides_completed,
            "rides_accepted": driver.rides_accepted,
            "rides_rejected": driver.rides_rejected,
        }, broadcast=True)

        return {"success": True}
    return {"success": False}, 404

@driver_bp.route("/logout")
def logout_driver():
    session.pop("driver_id", None)
    flash("You have been logged out", "info")
    return redirect(url_for("core.home"))
