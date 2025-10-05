from flask import Blueprint,  render_template, request, redirect, url_for, flash, session
import random
from app import db
from werkzeug.security import generate_password_hash
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine import Document, StringField, EmailField
passenger_bp = Blueprint("passenger", __name__, template_folder="templates")
otp_store = {}
from .model.passenger import Passenger
@passenger_bp.route("/register", methods=["GET", "POST"])
def register_passenger():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        referral_code = request.form.get("referral_code") or None  # ✅ optional

 # ✅ Check if user already exists
        existing = Passenger.objects(
            __raw__={"$or": [
                {"email": email},
                {"phone": phone},
                {"username": username}
            ]}
        ).first()

        if existing:
            flash("⚠️ You are already registered! Please login.", "error")
            return redirect(url_for("passenger.login_passenger"))

        # Check if username or email already exists
        if Passenger.objects(username=username).first() or Passenger.objects(email=email).first():
            flash("Username or Email already exists!", "error")
            return redirect(url_for("passenger.register_passenger"))

        Passenger(name=name, email=email, phone=phone, username=username, password=password, referral_code=referral_code).save()
        flash("✅ Registration successful! Please login.", "success")
        return redirect(url_for("passenger.login_passenger"))
    return render_template("passenger_register.html")



@passenger_bp.route("/login", methods=["GET", "POST"])

def login_passenger():
    
    if request.method == "POST":
        method = request.form.get("method")
        if method == "email":
            email = request.form.get("email")
            password = request.form.get("password")
            user = Passenger.objects(email=email).first()
            if user and check_password_hash(user.password, password):
                session["passenger_id"] = str(user.id)
                flash("Login Successful", "success")
                return redirect(url_for("passenger.passenger_dashboard"))
            else:
                flash("Invalid Email or Password", "error")
        elif method == "phone":
            phone = request.form.get("phone")
            user = Driver.objects(phone=phone).first()
            if user:
                otp = random.randint(100000, 999999)
                otp_store_driver[phone] = otp
                print(f"Driver OTP for {phone}: {otp}")  # In production, send via SMS/email
                return redirect(url_for("driver.verify_otp", phone=phone))
            else:
                flash("Phone not registered. Please register first.", "error")
    return render_template("passenger_login.html")


# -------------------
# Verify OTP
# -------------------
@passenger_bp.route("/verify", methods=["POST"])
def verify_otp():
    entered = request.form.get("otp")
    if entered == session.get("otp"):
        session["user"] = session.get("phone")
        flash("Login successful with Phone!")
        return redirect(url_for("passenger.passenger_dashboard"))
    else:
        flash("Invalid OTP, try again")
        return redirect(url_for("passenger.login"))




@passenger_bp.route("/dashboard")
def passenger_dashboard():
    if "passenger_id" not in session:
        flash("Please login first", "error")
        return redirect(url_for("passenger.login_passenger"))
    passenger = Passenger.objects(id=session["passenger_id"]).first()
    return render_template("passenger_dashboard.html",passenger=passenger)




from flask import request, render_template, redirect, url_for, flash, session
from datetime import datetime, timedelta
from .model.ride_model import RideBooking
from .fare_calculate import calculate_fare
from .utils import get_nearest_drivers 
@passenger_bp.route("/ride-booking", methods=["GET", "POST"])
def ride_booking():
    if "passenger_id" not in session:
        flash("Please login to book a ride", "error")
        return redirect(url_for("passenger.login_passenger"))
    
    if request.method == "POST":
        pickup = request.form.get("pickup")
        drop = request.form.get("drop")
        ride_type = request.form.get("ride_type")
        scheduled_time = request.form.get("scheduled_time")
        ride_option = request.form.get("ride_option")
        vehicle_type = request.form.get("vehicle_type")
        capacity = request.form.get("capacity")
        luggage = bool(request.form.get("luggage"))

        ac_pref = bool(request.form.get("ac_pref"))
        female_pref = bool(request.form.get("female_pref"))
        extra_luggage = bool(request.form.get("extra_luggage"))

        coupon_code = request.form.get("coupon_code")
        payment_method = request.form.get("payment_method")

        # Mock distance & duration (real: use Google Maps API)
        distance_km = 12
        duration_min = 25

        # Fare calculation
        estimated_fare, discount, final_fare = calculate_fare(
            distance_km, duration_min, ride_option, vehicle_type, coupon=coupon_code
        )

        # Save booking
        ride = RideBooking(
            passenger_id=session["passenger_id"],
            pickup_location=pickup,
            drop_location=drop,
            ride_type=ride_type,
            scheduled_time=None,  # add validation like before
            shared=(ride_option == "shared"),
            vehicle_type=vehicle_type,
            passenger_capacity=int(capacity or 1),
            luggage=luggage,
            ac_preference=ac_pref,
            female_driver_preferred=female_pref,
            extra_luggage_space=extra_luggage,
            estimated_fare=estimated_fare,
            coupon_code=coupon_code,
            discount_applied=discount,
            final_fare=final_fare,
            payment_method=payment_method,
            payment_status="pending"
            
        )
        ride.save()
        if ride.shared:
            trip_id = add_to_shared_trip(ride)
            ride.shared_trip_id = str(trip_id)

    # Update ride fare to distance-based share
            trip = SharedTrip.objects(id=trip_id).first()
            ride.fare_price = trip.fare_split[ride.passenger_id]
            ride.save()



        
        booking_id = str(ride.id) 
# Check for shared matches
        if ride.shared:
            matched = find_shared_rides(ride)
            if matched:
                flash(f"Your ride is matched with {len(matched)} passenger(s) for shared ride!", "info")

        # 🚀 If Razorpay → trigger payment gateway (API call here)
        if payment_method == "razorpay":
            flash(f"Proceeding to Razorpay payment. Fare: ₹{final_fare}", "info")
            # 🚀 Razorpay flow
        
          

            ride = RideBooking.objects(id=ride_id).first()
            if not ride:
                flash("Ride not found", "error")
                return redirect(url_for("passenger.my_rides"))

            amount_paise = int(ride.final_fare * 100)  # Razorpay expects paise
            order = razorpay_client.order.create({
                 "amount": amount_paise,
                "currency": "INR",
                "payment_capture": "1"
               })


            # Save payment record
            db.payments.insert_one({
                "booking_id": booking_id,
                "order_id": order["id"],
                "amount": order_amount,
                "currency": "INR",
                "status": "created",
                "created_at": datetime.datetime.utcnow()
            })

            # Show Razorpay payment page
            return render_template("payment.html",
                                   booking_id=booking_id,
                                   fare=final_fare,
                                   order=order,
                                   key_id=os.getenv("RAZORPAY_KEY_ID"))
            # TODO: Integrate Razorpay checkout
        else:
            flash(f"✅ Ride booked with COD. Fare: ₹{final_fare}", "success")

        flash("Booking is confirm. Waiting for confirm driver...", "info")
        return redirect(url_for("passenger.confirm_driver"))


    return render_template("ride_booking.html")

@passenger_bp.route("/razorpay/webhook", methods=["POST"])
def razorpay_webhook():
    payload = request.get_data(as_text=True)
    signature = request.headers.get("X-Razorpay-Signature")

    try:
        razorpay_client.utility.verify_webhook_signature(
            payload,
            signature,
            os.getenv("RAZORPAY_WEBHOOK_SECRET")
        )
    except:
        return "Invalid signature", 400

    event = request.json
    order_id = event["payload"]["payment"]["entity"]["order_id"]

    if event["event"] == "payment.captured":
        db.payments.update_one({"order_id": order_id},
                               {"$set": {"status": "captured",
                                         "payment_id": event["payload"]["payment"]["entity"]["id"]}})
        pay_doc = db.payments.find_one({"order_id": order_id})
        if pay_doc:
            booking_id = pay_doc["booking_id"]
            db.ridebookings.update_one({"_id": ObjectId(booking_id)},
                                       {"$set": {"payment_status": "paid"}})
            confirm_driver(booking_id)

    elif event["event"] == "payment.failed":
        db.payments.update_one({"order_id": order_id},
                               {"$set": {"status": "failed"}})

    return jsonify({"status": "ok"})



from driver.drivermodel import Driver
from socket_event import socketio
from .notification import notify_driver, notify_passenger


@passenger_bp.route("/confirm_driver/<booking_id>/<driver_id>", methods=["POST"])
def confirm_driver(booking_id, driver_id):
    booking = RideBooking.objects.get(id=booking_id)
    driver = Driver.objects.get(id=driver_id)
    booking.update(assigned_driver=driver, status="waiting_for_driver", updated_at=datetime.utcnow())
    # mark driver unavailable
    driver.update(is_available=0)
    # notify driver via socket to their room (driver should be in a room like driver:<id>)
    socketio.emit("ride_request", {"ride_id": str(booking.id), "pickup": {"lat": booking.pickup_lat, "lng": booking.pickup_lng}}, room=f"driver:{driver.id}")
    return redirect(url_for("passenger.ride_status", booking_id=booking_id))


@passenger_bp.route("/rate_ride/<ride_id>", methods=["GET", "POST"])
def rate_ride(ride_id):
    booking = RideBooking.objects.get(id=ride_id)

    # ✅ only allow rating after ride is completed
    if booking.status != "completed":
        flash("You can only rate a completed ride.")
        return redirect(url_for("passenger.ride_status", booking_id=ride_id))

    if request.method == "POST":
        rating = int(request.form.get("rating"))
        feedback = request.form.get("feedback")

        # update ride
        booking.rating = rating
        booking.feedback = feedback
        booking.save()

        # update driver average rating
        if booking.assigned_driver:
            driver = booking.assigned_driver
            driver.update_rating(rating)

        flash("Thanks for rating your ride!")
        return redirect(url_for("passenger.dashboard"))

    return render_template("rate_ride.html", booking=booking)



# from driver.model import Driver
# @passenger_bp.route("/confirm_driver/<booking_id>/<driver_id>", methods=["POST"])
# def confirm_driver(booking_id, driver_id):
#     booking = RideBooking.objects.get(id=booking_id)
#     driver = Driver.objects.get(id=driver_id)

#     # assign driver
#     booking.assigned_driver = driver
#     booking.status = "waiting_for_driver"
#     booking.save()

#     driver.is_available = False
#     driver.save()


#     flash("Driver request sent. Waiting for confirmation...", "info")
#     return redirect(url_for("passenger.passenger_dashboard"))

# from .utils import get_nearest_drivers   # if you put it in utils/location.py

# @passenger_bp.route("/ride_status/<booking_id>")
# def ride_status(booking_id):
#     booking = RideBooking.objects.get(id=booking_id)

#     #booking = RideBooking.objects.get(id=booking_id)

#     # 2. If driver rejected or no driver assigned, search nearest drivers
#     if booking.status == "driver_rejected" or not booking.assigned_driver:
#         drivers = get_nearest_drivers((booking.pickup_lat, booking.pickup_lng))
#         return render_template("select_driver.html", booking=booking, drivers=drivers)

#     return render_template("ride_status.html", booking=booking)



from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta

from .model.rental_model import RentalBooking
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from .rental_utils import validate_schedule, calculate_rental_cost, find_available_vehicles
import os
from .config import RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET



@passenger_bp.route("/booking", methods=["GET", "POST"])# routes/rental.py
def rental_booking():
    if "passenger_id" not in session:
        flash("Please login to book a rental", "error")
        return redirect(url_for("passenger.login_passenger"))

    if request.method == "POST":
        passenger_id = session["passenger_id"]
        ride_type = request.form.get("ride_type") or "on_demand"
        vehicle_type = request.form.get("vehicle_type")
        load_type = request.form.get("load_type")
        rental_duration = request.form.get("rental_duration") or "hourly"

        # times
        start_raw = request.form.get("start_time")
        end_raw   = request.form.get("end_time")
        try:
            start_dt = datetime.strptime(start_raw, "%Y-%m-%dT%H:%M")
            end_dt   = datetime.strptime(end_raw, "%Y-%m-%dT%H:%M")
        except Exception:
            flash("Invalid date/time format", "error")
            return redirect(url_for("rental.rental_booking"))

        ok, msg = validate_schedule(start_dt, end_dt)
        if not ok:
            flash(msg, "error")
            return redirect(url_for("rental.rental_booking"))

        # pickup / drop details (names + coords)
        pickup_name = request.form.get("pickup_name")
        pickup_coords = request.form.get("pickup_coords")  # "lat,lng"
        drop_name = request.form.get("drop_name")
        drop_coords = request.form.get("drop_coords")

        if not (pickup_name and pickup_coords and drop_name and drop_coords):
            flash("Pickup and drop location required", "error")
            return redirect(url_for("rental.rental_booking"))

        addons = request.form.getlist("addons")  # list
        payment_method = request.form.get("payment_method") or "cod"

        # price estimate
        subtotal, tax, final = calculate_rental_cost(vehicle_type, start_dt, end_dt, duration_unit=rental_duration, addons=addons)

        # (Optional) check availability
        available = find_available_vehicles(vehicle_type, start_dt, end_dt)
        if ride_type == "on_demand" and not available:
            flash("No vehicles available right now for the selected type.", "error")
            return redirect(url_for("rental.rental_booking"))

        # Save booking (status pending until payment/assignment)
        booking = RentalBooking(
            passenger_id=passenger_id,
            ride_type=ride_type,
            vehicle_type=vehicle_type,
            load_type=load_type,
            addons=addons,
            start_time=start_dt,
            end_time=end_dt,
            rental_duration_unit=rental_duration,
            pickup_name=pickup_name,
            pickup_coords=pickup_coords,
            drop_name=drop_name,
            drop_coords=drop_coords,
            estimated_fare=subtotal,
            taxes=tax,
            final_fare=final,
            payment_method=payment_method,
            payment_status="pending",
            status="pending"
        )
        booking.save()

        # If Razorpay chosen → create order and return checkout flow
        if payment_method == "razorpay" and RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
            import razorpay
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
            # amount in paise
            amt_paise = int(final * 100)
            order = client.order.create(dict(amount=amt_paise, currency="INR", payment_capture='1'))
            # store order_id somewhere (optional)
            booking.update(payment_status="pending", status="pending")
            return render_template("rental_payment.html", booking=booking, razorpay_order=order, razorpay_key=RAZORPAY_KEY_ID)

        # COD or no gateway: proceed to assignment flow
        flash("Rental request submitted. Waiting for vehicle assignment.", "success")
        return redirect(url_for("rental.rental_summary", booking_id=str(booking.id)))


    

    # GET - show booking form
    return render_template("rental_booking.html")


from .utils import get_nearest_drivers
@passenger_bp.route("/rental/confirm/<rental_id>", methods=["POST"])
def confirm_rental(rental_id):
    rental = RentalBooking.objects.get(id=rental_id)

    # 1. Mark payment success
    rental.status = "Paid"
    rental.save()

    # 2. If rental includes driver → assign driver
    if rental.with_driver:
        driver = get_nearest_drivers(rental.passenger)
        if driver:
            rental.driver = driver
            rental.status = "Driver Assigned"
            rental.save()

            # Notify driver
            notify_driver(driver, f"New rental booking assigned: {rental.id}")

            # Notify passenger
            notify_passenger(rental.passenger, f"Driver {driver.name} assigned to your rental")
        else:
            notify_passenger(rental.passenger, "Payment successful, but no drivers available right now")
    else:
        # Self-drive rental, no driver needed
        notify_passenger(rental.passenger, "Rental confirmed. Please pick up the vehicle at scheduled time.")

    flash("Rental confirmed successfully!", "success")
    return redirect(url_for("passenger.rental_history"))

@passenger_bp.route('/rental/request_extension/<rental_id>', methods=['POST'])
def request_extension(rental_id):
    rental = RentalBooking.objects.get(id=rental_id)
    new_end_time = request.form.get("new_end_time")  # from calendar input
    new_end_time = datetime.datetime.fromisoformat(new_end_time)

    # Validation: must be after current end_time
    if new_end_time <= rental.end_time:
        flash("New end time must be later than current end time.", "error")
        return redirect(url_for('passenger.rental_dashboard'))

    # Calculate extension fare (e.g. ₹200/hour extra)
    extra_hours = (new_end_time - rental.end_time).total_seconds() / 3600
    extra_fare = extra_hours * 200

    rental.extension_requested = True
    rental.extension_new_end = new_end_time
    rental.extension_fare = rental.fare + extra_fare
    rental.save()

    flash("Extension request sent. Awaiting approval.", "info")
    return redirect(url_for('passenger.rental_dashboard'))

# @passenger_bp.route("/ride-history")
# def ride_history():
#     if "passenger_id" not in session:
#         flash("Please login to view ride history.", "error")
#         return redirect(url_for("passenger.login_passenger"))
    
#     passenger_id = session["passenger_id"]
#     rides = RideBooking.objects(passenger_id=passenger_id).order_by("-created_at")
    
#     return render_template("ride_history.html", rides=rides)

# @passenger_bp.route("/rental_history")
# def rental_history():
#     if "passenger_id" not in session:
#         flash("Please login to view rental history.", "error")
#         return redirect(url_for("passenger.login_passenger"))
    
#     user_id = session["passenger_id"]
#     rentals = RentalBooking.query.filter_by(user_id=user_id).order_by(RentalBooking.created_at.desc()).all()
    
#     return render_template("rental_history.html", rentals=rentals)


# passenger/routes_history.py
from flask import Blueprint, render_template, request, session, redirect, url_for, send_file, flash
from .model.booking_model import Booking
from .utils import query_history, recalc_fare_estimate
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

#history_bp = Blueprint("passenger_history", __name__, template_folder="templates/passenger")

# History list + filters
@passenger_bp.route("/history", methods=["GET"])
def passenger_history():
    passenger_id = session.get("passenger_id")
    if not passenger_id:
        flash("Please log in to view your history.", "warning")
        return redirect(url_for("passenger.login_passenger"))

    # read filters from query params
    start = request.args.get("start_date")
    end = request.args.get("end_date")
    booking_type = request.args.get("booking_type")
    vehicle_type = request.args.get("vehicle_type")
    status = request.args.get("status")
    search = request.args.get("search")

    start_dt = datetime.fromisoformat(start) if start else None
    end_dt = datetime.fromisoformat(end) if end else None

    bookings = query_history(passenger_id, start_dt, end_dt, booking_type, vehicle_type, status, search)
    return render_template("history.html", bookings=bookings, filters=request.args)

# Invoice PDF generation
@passenger_bp.route("/history/invoice/<booking_id>")
def download_invoice(booking_id):
    passenger_id = session.get("passenger_id")
    if not passenger_id:
        return redirect(url_for("passenger.login_passenger"))

    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        flash("Booking not found", "error")
        return redirect(url_for("passenger.passenger_history"))

    if booking.passenger_id != passenger_id:
        flash("You are not authorized to download this invoice.", "error")
        return redirect(url_for("passenger.passenger_history"))

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, h-50, "Invoice")
    p.setFont("Helvetica", 10)
    p.drawString(40, h-70, f"Booking ID: {booking.id}")
    p.drawString(40, h-85, f"Date: {booking.created_at.strftime('%Y-%m-%d %H:%M')}")
    p.drawString(40, h-100, f"Booking Type: {booking.booking_type} / {booking.sub_type or ''}")
    p.drawString(40, h-115, f"Status: {booking.status}")

    y = h-140
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, "Passenger")
    p.setFont("Helvetica", 10)
    y -= 16
    p.drawString(50, y, f"Name: {booking.passenger_name or booking.passenger_id}")
    y -= 18

    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, "Driver")
    p.setFont("Helvetica", 10)
    y -= 16
    p.drawString(50, y, f"Name: {booking.driver_name or 'N/A'}")
    y -= 18

    if booking.booking_type == "ride":
        p.setFont("Helvetica-Bold", 12)
        p.drawString(40, y, "Trip Details")
        y -= 16
        p.setFont("Helvetica", 10)
        p.drawString(50, y, f"Pickup: {booking.pickup_name or ''}")
        y -= 14
        p.drawString(50, y, f"Drop: {booking.drop_name or ''}")
        y -= 18
    else:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(40, y, "Rental Details")
        y -= 16
        p.setFont("Helvetica", 10)
        if booking.vehicle_details:
            p.drawString(50, y, f"Vehicle: {booking.vehicle_type} {booking.vehicle_details.get('make','')}")
            y -= 14
            p.drawString(50, y, f"Plate: {booking.vehicle_details.get('plate','')}")
            y -= 18

    # Fare breakdown
    fb = booking.fare_breakdown or {}
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, "Fare Breakdown")
    y -= 16
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Base: ₹{fb.get('base', 0)}")
    y -= 14
    p.drawString(50, y, f"Distance charge: ₹{fb.get('distance_charge', 0)}")
    y -= 14
    p.drawString(50, y, f"Time charge: ₹{fb.get('time_charge', 0)}")
    y -= 14
    p.drawString(50, y, f"Taxes: ₹{fb.get('tax', 0)}")
    y -= 14
    p.drawString(50, y, f"Discounts: -₹{fb.get('discount', 0)}")
    y -= 20

    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, f"Total Paid: ₹{booking.fare} ({booking.payment_method} - {booking.payment_status})")

    p.showPage()
    p.save()
    buffer.seek(0)

    filename = f"invoice_{booking.id}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")

# # Rebook (GET shows confirm, POST creates new booking)
# @passenger_bp.route("/history/rebook/<int:booking_id>", methods=["GET","POST"])
# def rebook(booking_id):
#     passenger_id = session.get("passenger_id")
#     if not passenger_id:
#         return redirect(url_for("passenger.login_passenger"))

#     try:
#         booking = Booking.objects.get(id=booking_id)
#     except Booking.DoesNotExist:
#         flash("Booking not found", "error")
#         return redirect(url_for("passenger.passenger_history"))

#     if booking.passenger_id != passenger_id:
#         flash("Not authorized", "error")
#         return redirect(url_for("passenger.passenger_history"))

#     # GET: show pre-filled confirm page
#     if request.method == "GET":
#         return render_template("rebook_confirm.html", booking=booking)

#     # POST: create a new booking (recalculate fare with current rates)
#     current_rates = {
#         "base_per_km": 12.0,
#         "per_min": 1.5,
#         "tax": 0.18
#     }
#     estimate = recalc_fare_estimate(booking, current_rates)

#     new_b = Booking(
#         booking_type = booking.booking_type,
#         sub_type = booking.sub_type,
#         passenger_id = passenger_id,
#         passenger_name = booking.passenger_name,
#         pickup_name = booking.pickup_name,
#         pickup_lat = booking.pickup_lat,
#         pickup_lng = booking.pickup_lng,
#         drop_name = booking.drop_name,
#         drop_lat = booking.drop_lat,
#         drop_lng = booking.drop_lng,
#         vehicle_type = booking.vehicle_type,
#         vehicle_details = booking.vehicle_details,
#         start_time = None,
#         end_time = None,
#         fare = estimate["final"],
#         fare_breakdown = {
#             "distance_km": estimate["distance_km"],
#             "time_min": estimate["duration_min"],
#             "subtotal": estimate["subtotal"],
#             "tax": estimate["tax"],
#             "final": estimate["final"]
#         },
#         payment_method = request.form.get("payment_method", "cod"),
#         payment_status = "pending",
#         status = "pending"
#     )
#     new_b.save()
#     booking = RentalBooking.query.get_or_404(booking_id)
#     flash("Rebooking created. Proceed to payment if required.", "success")
#     return render_template("rebook.html", booking_id=new_b.id)


@passenger_bp.route("/summary/<int:booking_id>")
def rental_summary(booking_id):
    booking = RentalBooking.query.get_or_404(booking_id)
    return render_template("rental_summary.html", booking=booking)



# routes/notifications.py
from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for, flash
from .model.notification_model import Notification
from .notification import create_notification
from datetime import datetime
from mongoengine.queryset.visitor import Q


# GUI: list notifications (tabs: ride / rental / payment)
@passenger_bp.route("/notifications")
def notifications_view():
    passenger_id = session.get("passenger_id")
    if not passenger_id:
        flash("Please login to see notifications", "error")
        return redirect(url_for("passenger.login_passenger"))

    # Define categories
    categories = ["ride", "rental", "payment"]

    # Fetch notifications for all categories in one go
    all_notes = Notification.objects(passenger_id=passenger_id).order_by("-created_at")[:150]

    # Organize into categories
    notes_by_category = {cat: [] for cat in categories}
    for note in all_notes:
        if note.category in notes_by_category:
            notes_by_category[note.category].append(note)

    # Count unread
    unread_count = sum(1 for note in all_notes if not note.is_read)

    return render_template(
        "notification.html",
        ride_notes=notes_by_category.get("ride", []),
        rental_notes=notes_by_category.get("rental", []),
        payment_notes=notes_by_category.get("payment", []),
        unread_count=unread_count
    )

@passenger_bp.route("/notifications/mark_all_read", methods=["POST"])
def mark_all_notifications_read():
    passenger_id = session.get("passenger_id")
    if not passenger_id:
        flash("Please login to continue", "error")
        return redirect(url_for("passenger.login_passenger"))

    # Update all unread notifications for this passenger
    Notification.objects(passenger_id=passenger_id, is_read=False).update(set__is_read=True)

    flash("All notifications marked as read ✅", "success")
    return redirect(url_for("passenger.notifications_view"))


#I: fetch notifications (JSON) with optional category filter
# @passenger_bp.route("/notifications", methods=["GET"])
# def api_notifications():
#     passenger_id = request.args.get("passenger_id") or session.get("passenger_id")
#     if not passenger_id:
#         return jsonify({"error":"unauthenticated"}), 401
#     category = request.args.get("category")
#     q = Notification.objects(passenger_id=passenger_id)
#     if category:
#         q = q.filter(category=category)
#     notes = q.order_by("-created_at").limit(100)
#     return jsonify([{
#         "id": str(n.id),
#         "category": n.category,
#         "event": n.event,
#         "title": n.title,
#         "message": n.message,
#         "data": n.data,
#         "is_read": n.is_read,
#         "created_at": n.created_at.isoformat()
#     } for n in notes])

# # API: mark as read
# @passenger_bp.route("/notifications/mark_read", methods=["POST"])
# def api_mark_read():
#     passenger_id = session.get("passenger_id")
#     if not passenger_id:
#         return jsonify({"error":"unauthenticated"}), 401
#     payload = request.json or {}
#     ids = payload.get("ids", [])
#     if not ids:
#         return jsonify({"error":"no ids provided"}), 400
#     Notification.objects(passenger_id=passenger_id, id__in=ids).update(set__is_read=True)
#     return jsonify({"success":True})

# # API: general create endpoint (internal use)
# @passenger_bp.route("/notifications/create", methods=["POST"])
# def api_create_notification():
#     payload = request.json or {}
#     passenger_id = payload.get("passenger_id")
#     if not passenger_id:
#         return jsonify({"error":"passenger_id required"}), 400
#     category = payload.get("category", "ride")
#     event = payload.get("event", "generic")
#     title = payload.get("title", "")
#     message = payload.get("message", "")
#     data = payload.get("data", {})
#     create_notification(passenger_id, category, event, title, message, data, push=True)
#     return jsonify({"success": True})




from .wallet_utils import get_wallet, add_money, send_money, get_transactions
@passenger_bp.route("/wallet")
def wallet_home():
    passenger_id = session.get("passenger_id")
    if not passenger_id:
        flash("Login required", "error")
        return redirect(url_for("passenger.login_passenger"))

    wallet = get_wallet(passenger_id)
    transactions = get_transactions(passenger_id)
    return render_template("wallet.html", wallet=wallet, transactions=transactions)

@passenger_bp.route("/wallet/add", methods=["POST"])
def wallet_add():
    passenger_id = session.get("passenger_id")
    amount = request.form.get("amount")
    if amount:
        add_money(passenger_id, amount)
        flash(f"₹{amount} added to wallet!", "success")
    return redirect(url_for("passenger.wallet_home"))

@passenger_bp.route("/wallet/send", methods=["POST"])
def wallet_send():
    passenger_id = session.get("passenger_id")
    receiver_id = request.form.get("receiver_id")
    amount = request.form.get("amount")
    try:
        send_money(passenger_id, receiver_id, amount)
        flash(f"₹{amount} sent to {receiver_id}", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("passenger.wallet_home"))

@passenger_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if "passenger_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("passenger.login_passenger"))

    passenger = Passenger.objects(id=session["passenger_id"]).first()

    if request.method == "POST":
        # Update Profile
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")

        passenger.name = name
        passenger.email = email
        passenger.phone = phone

        # Update Password if provided
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if old_password and new_password:
            if not check_password_hash(passenger.password, old_password):
                flash("Old password is incorrect.", "error")
                return redirect(url_for("passenger.passenger_settings"))
            if new_password != confirm_password:
                flash("New password and confirm password do not match.", "error")
                return redirect(url_for("passenger.settings"))
            passenger.password = generate_password_hash(new_password)

        passenger.save()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("passenger.settings"))

    return render_template("passenger_setting.html", passenger=passenger)

@passenger_bp.route("/logout")
def logout():
    session.pop("passenger_id", None)
    flash("You have been logged out", "info")
    return redirect(url_for("core.home"))
