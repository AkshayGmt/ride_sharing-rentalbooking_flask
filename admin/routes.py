from flask import Blueprint
from functools import wraps
admin_bp = Blueprint("admin", __name__,  template_folder="templates", static_folder="static", url_prefix="/admin")

from flask import render_template, request, redirect, url_for, session, current_app, flash
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from passenger.model.passenger import Passenger
from .model import AuditLog, Config  
from datetime import datetime, timedelta
from .model import AuditLog, Admin
from werkzeug.security import check_password_hash
from .model import Admin 
# Create first admin (run once or add in shell)
# @admin_bp.route("/create_superuser")
# def create_superuser():
#     if Admin.objects(username="admin").first():
#         return "Admin already exists ✅"
    
#     admin = Admin(
#         username="admin",
#         password=generate_password_hash("admin123")
#     )
#     admin.save()
#     return "Superuser created: username=admin, password=admin123 ✅"
# #----------------- Admin Login ------------------

from flask import app
@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        admin = Admin.objects(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session["admin_id"] = str(admin.id)
            flash("Logged in successfully ✅", "success")
            return redirect(url_for("admin.admin_dashboard"))
        else:
            flash("Invalid username or password ❌", "danger")

    return render_template("login.html")


def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Please log in to access this page", "warning")
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function
# ------------------ Admin Logout ------------------

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash("You have been logged out", "success")
    return redirect(url_for('core.home'))

@admin_bp.route("/dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for("admin.login"))
    return render_template("dashboard.html")

@admin_bp.route("/users")
def user_management():
    return render_template("user_management.html")

@admin_bp.route('/user/manage', methods=['GET'])
def manage_users():
    search_query = request.args.get("search", "").lower()
    filter_status = request.args.get("status", "")

    # Fetch all passengers/renters from Passenger app database
    users = Passenger.objects()  # Replace with your DB query

    # Filter/search
    filtered_users = []
    for u in users:
        if (search_query in u.name.lower() or search_query in u.email.lower() 
            or search_query in u.phone):
            if filter_status == "" or filter_status.lower() == u.status.lower():
                filtered_users.append(u)

    return render_template("manage.html",
                           users=filtered_users,
                           search_query=search_query,
                           filter_status=filter_status)


# -------------------------------
# Edit User Details
# -------------------------------
@admin_bp.route('/user/edit/<user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = Passenger.objects(id=user_id).first()
    if request.method == 'POST':
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        user.status = request.form.get('status')
        user.save()
        return redirect(url_for('admin.manage_users'))

    return render_template('edit_user.html', user=user)


# -------------------------------
# Activity Monitoring
# -------------------------------
@admin_bp.route('/user_management/activity/<user_id>')
def user_activity(user_id):
    user = Passenger.objects(id=user_id).first()

    # Fetch activity from rides/rentals/payments collections
    ride_history = user.get_ride_history()  # Implement in Passenger app
    rental_history = user.get_rental_history()
    payments = user.get_payment_history()
    complaints = user.get_complaints()

    return render_template('user_activity.html',
                           user=user,
                           rides=ride_history,
                           rentals=rental_history,
                           payments=payments,
                           complaints=complaints)

@admin_bp.route('/user_management/suspend', methods=['GET', 'POST'])
def suspend_users():
    users = Passenger.objects()  # Fetch all users
    
    if request.method == "POST":
        user_id = request.form.get("user_id")
        action = request.form.get("action")
        reason = request.form.get("reason", "")
        user = Passenger.objects(id=user_id).first()

        if action == "suspend":
            user.status = "Suspended"
            user.suspension_reason = reason
            # TODO: send notification via email/SMS
        elif action == "deactivate":
            user.status = "Deactivated"
            user.deactivation_reason = reason
            # TODO: send notification via email/SMS
        elif action == "reactivate":
            user.status = "Active"
            user.suspension_reason = ""
            user.deactivation_reason = ""
        user.save()
        return redirect(url_for('admin.suspend_users'))

    return render_template("suspend_users.html", users=users)


# -------------------------------
# Security & Audit (View Logs)
# -------------------------------
@admin_bp.route('/user_management/audit')
def audit_logs():
    logs = AuditLog.objects().order_by('-timestamp')  # Fetch logs
    return render_template('audit_logs.html', logs=logs)


# -------------------------------
# Record Admin Actions (utility)
# -------------------------------



# -------------------------------
# Rider No-Show Policy
# -------------------------------
@admin_bp.route('/settings/no_show', methods=['GET', 'POST'])
def no_show_settings():
    config = Config.objects(key="no_show_policy").first()

    if request.method == "POST":
        wait_time = int(request.form.get("wait_time"))
        wait_fee = float(request.form.get("wait_fee"))
        no_show_fee = float(request.form.get("no_show_fee"))

        config.value = {
            "wait_time": wait_time,
            "wait_fee": wait_fee,
            "no_show_fee": no_show_fee
        }
        config.save()
        return redirect(url_for('admin.no_show_settings'))

    return render_template('no_show_settings.html', config=config)


@admin_bp.route('/driver_management')
def driver_management():
    
    return render_template('driver_management.html')


from .notitfication import send_email_notification,send_sms_notification
from driver.drivermodel import Driver
@admin_bp.route('/driver_management/registrations', methods=['GET', 'POST'])
def driver_registrations():
     # --- Filters ---
    search_name = request.args.get("name", "").strip()
    search_vehicle = request.args.get("vehicle", "").strip()
    search_phone = request.args.get("phone", "").strip()

    # Base query (pending drivers)
    query = {"status": "Pending"}
    if search_name:
        query["name__icontains"] = search_name
    if search_vehicle:
        query["vehicle_type__icontains"] = search_vehicle
    if search_phone:
        query["phone__icontains"] = search_phone

    drivers = Driver.objects(**query)
    # Fetch all drivers waiting for approval
   # drivers = Driver.objects(status="Pending")

    # Handle Approve/Reject
    if request.method == "POST":
        driver_id = request.form.get("driver_id")
        action = request.form.get("action")
        reason = request.form.get("reason", "")

        driver = Driver.objects(id=driver_id).first()

        if action == "approve":
            driver.status = "Approved"
            driver.approved_on = datetime.now()
            flash(f"Driver {driver.name} approved!", "success")
            send_email_notification(driver.email,
        "Driver Registration Approved",
        f"Dear {driver.name}, your registration has been approved. You can now accept rides.")
            send_sms_notification(driver.phone,
        f"Hi {driver.name}, your driver account has been approved. You can now accept rides!")


            # send_notification(driver, "approved")
        elif action == "reject":
            driver.status = "Rejected"
            driver.rejection_reason = reason
            flash(f"Driver {driver.name} rejected!", "danger")
            send_email_notification(driver.email,
        "Driver Registration Rejected",
        f"Dear {driver.name}, unfortunately your registration was rejected. Reason: {reason}")
            send_sms_notification(driver.phone,
        f"Hi {driver.name}, your driver account was rejected. Reason: {reason}")


            # send_notification(driver, "rejected", reason)

        driver.save()

        # Audit log
        log = AuditLog(
            admin="Admin1",  # get from session
            action=action,
            user_id=str(driver.id),
            details=f"Driver {driver.name} {action}. Reason: {reason}",
            timestamp=datetime.now()
        )
        log.save()

        return redirect(url_for('admin.driver_registrations'))

    # Check for documents nearing expiry (14 days)
    soon_expiring = []
    for d in drivers:
        if d.docs_expiry and d.docs_expiry <= datetime.now() + timedelta(days=14):
            soon_expiring.append(d.id)

    return render_template(
        'driver_registration.html',
        drivers=drivers,
        soon_expiring=soon_expiring,
        search_name=search_name,
        search_vehicle=search_vehicle,
        search_phone=search_phone
    )

from driver.model import DriverDocuments
@admin_bp.route('/driver_management/documents/<driver_id>', methods=['GET', 'POST'])
def verify_documents(driver_id):
    driver = Driver.objects(id=driver_id).first()
    documents = DriverDocuments.objects(driver=driver).first()

    if not driver or not documents:
        flash("Driver or documents not found", "danger")
        return redirect(url_for("admin.driver_registrations"))

    if request.method == "POST":
        doc_type = request.form.get("doc_type")
        action = request.form.get("action")  # Verify / Reject / Resubmit
        notes = request.form.get("notes", "")

        if doc_type == "license":
            documents.license_status = action
            documents.license_notes = notes
        elif doc_type == "rc":
            documents.rc_status = action
            documents.rc_notes = notes
        elif doc_type == "insurance":
            documents.insurance_status = action
            documents.insurance_notes = notes
        elif doc_type == "id_proof":
            documents.id_proof_status = action
            documents.id_proof_notes = notes

        documents.last_updated = datetime.utcnow()
        documents.save()

        # Update driver status if all verified
        statuses = [
            documents.license_status,
            documents.rc_status,
            documents.insurance_status,
            documents.id_proof_status
        ]
        if all(s == "Verified" for s in statuses):
            driver.status = "Approved"
        elif any(s == "Rejected" for s in statuses):
            driver.status = "Rejected"
        else:
            driver.status = "Pending"

        driver.save()
        # --- Notifications ---
        subject = f"Document Update: {doc_type.capitalize()}"
        message = f"Dear {driver.name},\n\nYour {doc_type.replace('_', ' ').capitalize()} has been marked as {action}.\nNotes: {notes or 'No additional remarks.'}\n\n- Admin Team"

        send_email_notification(driver.email, subject, message)
        send_sms_notification(driver.phone, f"Your {doc_type.capitalize()} has been {action}. {notes or ''}")

        flash(f"{doc_type.capitalize()} marked as {action} and driver notified.", "success")
        return redirect(url_for("admin.verify_documents", driver_id=driver.id))

        flash(f"{doc_type.capitalize()} marked as {action}", "success")
        return redirect(url_for("admin.verify_documents", driver_id=driver.id))

    return render_template("verify_documents.html", driver=driver, documents=documents)


@admin_bp.route('/driver_management/driver_activity')
def api_driver_activity():
    query = Driver.objects()

    # Apply filters
    name = request.args.get("name", "").strip()
    vehicle_type = request.args.get("vehicle_type", "").strip()
    online_status = request.args.get("online_status", "").strip()

    if name:
        query = query.filter(name__icontains=name)
    if vehicle_type:
        query = query.filter(vehicle_type__icontains=vehicle_type)
    if online_status == "online":
        query = query.filter(online=True)
    elif online_status == "offline":
        query = query.filter(online=False)

    data = []
    for d in query:
        data.append({
            "id": str(d.id),
            "name": d.name,
            "vehicle_type": d.vehicle_type,
            "online": d.online,
            "active_ride_id": d.active_ride_id,
            "rides_completed": d.rides_completed,
            "rides_accepted": d.rides_accepted,
            "rides_rejected": d.rides_rejected,
            "latitude": d.latitude,
            "longitude": d.longitude
        })
    context = {"drivers": data}
    return render_template("driver_activity.html", **context)

    #return render_template("driver_activity.html",{"drivers": data})
    
@admin_bp.route('/driver_management/additional_controls')
def driver_additional_controls():
    drivers = Driver.objects()
    return render_template("driver_aditional_control.html", drivers=drivers)


@admin_bp.route('/driver_management/suspend/<driver_id>', methods=['POST'])
def suspend_driver(driver_id):
    reason = request.form.get("reason")
    driver = Driver.objects(id=driver_id).first()
    if driver:
        driver.suspended = True
        driver.suspend_reason = reason
        driver.save()
        return {"message": "Driver suspended successfully"}
    return {"message": "Driver not found"}, 404

@admin_bp.route('/driver_management/deactivate/<driver_id>', methods=['POST'])
def deactivate_driver(driver_id):
    driver = Driver.objects(id=driver_id).first()
    if driver:
        driver.active = False
        driver.save()
        return {"message": "Driver deactivated successfully"}
    return {"message": "Driver not found"}, 404

@admin_bp.route('/driver_management/assign_vehicle/<driver_id>', methods=['POST'])
def assign_vehicle(driver_id):
    vehicle = request.form.get("vehicle")
    driver = Driver.objects(id=driver_id).first()
    if driver:
        driver.vehicle_type = vehicle
        driver.save()
        return {"message": f"Vehicle {vehicle} assigned successfully"}
    return {"message": "Driver not found"}, 404

from driver.model import RideRating
@admin_bp.route('/driver_management/feedback/<driver_id>')
def driver_feedback(driver_id):
    feedbacks = RideRating.objects(driver_id=driver_id)  # example Feedback model
    html = "<table class='table table-striped'><tr><th>Passenger</th><th>Rating</th><th>Comment</th></tr>"
    for f in feedbacks:
        html += f"<tr><td>{f.passenger_name}</td><td>{f.rating}</td><td>{f.comment}</td></tr>"
    html += "</table>"
    return {"html": html}

from flask import request, redirect, url_for, flash


@admin_bp.route("/driver_management/subscription/<driver_id>", methods=["GET", "POST"])
def driver_subscription(driver_id):
    if request.method == "POST":
        # Get form data
        plan_name = request.form.get("plan_name")
        duration = request.form.get("duration")  # Weekly, Monthly, Yearly
        price = float(request.form.get("price"))

        # Save to DB via MongoEngine
        subscription = DriverSubscription(
            plan_name=plan_name,
            duration=duration,
            price=price,
            status="Active"
        )
        subscription.save()

        flash("New subscription plan created successfully!", "success")
        return redirect(url_for("admin.driver_subscription"))

    # For GET: fetch all subscriptions
    subscription = DriverSubscription.objects(driver_id=driver_id, status="Active").order_by("-start_date").first()
    return render_template("driver_subscription.html", subscription=subscription)

    
@admin_bp.route("/driver_management/subscription/<sub_id>/renew")
def renew_subscription(sub_id):
    subscription = DriverSubscription.objects(id=sub_id).first()
    if subscription:
        subscription.status = "Active"
        subscription.save()
        flash("Subscription renewed successfully!", "success")
    else:
        flash("Subscription not found!", "danger")

    return redirect(url_for("admin.driver_subscription"))

from driver.model import DriverSubscription
@admin_bp.route("/driver_management/subscription/<sub_id>/cancel")
def cancel_subscription(sub_id):
    # Update subscription using MongoEngine
    subscription = DriverSubscription.objects(id=sub_id).first()
    if subscription:
        subscription.update(set__status="Expired")
        flash("Subscription cancelled!", "danger")
    else:
        flash("Subscription not found!", "warning")

    return redirect(url_for("admin.driver_subscription"))


from datetime import datetime, time

def get_time_of_day(pickup_time):
    """Return time-of-day block"""
    morning_start = time(5, 30)
    afternoon_start = time(11, 0)
    evening_start = time(17, 0)
    night_start = time(21, 0)

    t = pickup_time.time()
    if morning_start <= t < afternoon_start:
        return "Morning"
    elif afternoon_start <= t < evening_start:
        return "Afternoon"
    elif evening_start <= t < night_start:
        return "Evening"
    else:
        return "Night"
from driver.model import DriverIncident
@admin_bp.route("/driver_management/time_tagging")
def time_tagging():
    # Fetch rides with pickup time
    rides = Ride.objects.order_by("-pickup_time")
    
    # Annotate each ride with time-of-day
    for ride in rides:
        pickup_dt = ride.get("pickup_time")
        if pickup_dt:
            ride["time_of_day"] = get_time_of_day(pickup_dt)
        else:
            ride["time_of_day"] = "Unknown"
    
    # Fetch driver no-show/late incidents
    incidents = DriverIncident.objects.order_by("-date")    
    return render_template("time_tagging.html", rides=rides, incidents=incidents)


from admin.model import EdgeCaseSettings
from admin.forms import EdgeCaseForm

@admin_bp.route("/driver_management/edge_cases", methods=["GET", "POST"])
def edge_cases():
    settings = EdgeCaseSettings.objects.first()
    if not settings:
        settings = EdgeCaseSettings().save()  # default doc

    form = EdgeCaseForm(obj=settings)  # pre-fill with current settings

    if form.validate_on_submit():
        settings.daily_earning_cap = form.daily_earning_cap.data
        settings.max_rides_per_day = form.max_rides_per_day.data
        settings.cancellation_penalty = form.cancellation_penalty.data
        settings.save()

        flash("Edge case settings updated successfully!", "success")
        return redirect(url_for("admin.edge_cases"))

    return render_template("edge_cases.html", form=form)


@admin_bp.route('/ride_management')
def ride_management():
    rides = Ride.objects().order_by('-pickup_time')  # Fetch all rides/rentals
    return render_template("ride_management.html", rides=rides)

# Fetch filtered rides (for AJAX)
@admin_bp.route('/ride_management/rides')
def api_rides():
    driver = request.args.get("driver")
    passenger = request.args.get("passenger")
    time_of_day = request.args.get("time_of_day")
    status = request.args.get("status")
    
    query = Ride.objects()
    if driver:
        query = query.filter(driver_name__icontains=driver)
    if passenger:
        query = query.filter(passenger_name__icontains=passenger)
    if time_of_day:
        query = query.filter(time_of_day=time_of_day)
    if status:
        query = query.filter(status=status)
    
    rides = query.order_by("-pickup_time")
    
    html = render_template("ride_table_rows.html", rides=rides)
    return {"html": html}

# Resolve No-Show
from passenger.model.ride_model import Ride
@admin_bp.route('/ride_management/no_show/<ride_id>', methods=['POST'])
def resolve_no_show(ride_id):
    notes = request.form.get("notes")
    ride = Ride.objects(id=ride_id).first()
    if ride and ride.status == "Driver No-Show":
        ride.status = "Completed"
        ride.no_show_notes = notes
        ride.save()
        return {"message": "No-Show resolved successfully"}
    return {"message": "Ride not found or not a no-show"}, 404


from passenger.notification import notify_driver,notify_passenger
@admin_bp.route('/ride_management/unreachable/<ride_id>/<action>', methods=['POST'])
def handle_unreachable(ride_id, action):
    ride = Ride.objects(id=ride_id).first()
    if not ride:
        return {"message": "Ride not found"}, 404
    
    if action == "cancel":
        ride.status = "Cancelled - Unreachable"
        ride.save()
        notify_driver(ride.driver_id, "Ride cancelled due to unreachable contact")
        notify_passenger(ride.passenger_id, "Ride cancelled due to unreachable contact")
        return {"message": "Ride cancelled successfully"}
    
    elif action == "reassign":
        new_driver = assign_new_driver(ride)
        notify_driver(new_driver.id, f"New ride assigned: {ride.ride_id}")
        notify_passenger(ride.passenger_id, f"Your ride will continue with a new driver")
        return {"message": "Driver reassigned successfully"}
    
    elif action == "notify_support":
        notify_support_team(f"Ride {ride.ride_id} unreachable. Check immediately.")
        return {"message": "Support team notified"}
    
    return {"message": "Invalid action"}, 400

#from passenger.model import Vehicle


# admin_vehicle.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from driver.model import Vehicle
from .model import RentalPricing
from datetime import datetime
from bson import ObjectId  # if using ObjectId strings elsewhere

# -------------- Main GUI --------------
@admin_bp.route('/vehicle_management')
def vehicle_management():
    vehicles = Vehicle.objects().order_by('vehicle_type', 'make_model')
    pricing = RentalPricing.objects().order_by('vehicle_type', 'tier')
    return render_template('vehicle_management.html', vehicles=vehicles, pricing=pricing)


# -------------- Vehicle CRUD --------------
@admin_bp.route('/vehicle_management/add', methods=['POST'])
def add_vehicle():
    data = request.form.to_dict()
    # images to be handled separately (file upload) - placeholder
    v = Vehicle(
        vehicle_type=data.get('vehicle_type'),
        make_model=data.get('make_model'),
        year=int(data.get('year') or 0),
        capacity=int(data.get('capacity') or 0),
        fuel_type=data.get('fuel_type'),
        luggage_space=data.get('luggage_space'),
        status=data.get('status') or 'Available'
    )
    v.save()
    return jsonify({"success": True, "message": "Vehicle added", "id": str(v.id)})


@admin_bp.route('/vehicle_management/<vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    v = Vehicle.objects(id=vehicle_id).first()
    if not v:
        return jsonify({"error": "Not found"}), 404
    return jsonify(v.to_mongo().to_dict())


@admin_bp.route('/vehicle_management/<vehicle_id>/update', methods=['POST'])
def update_vehicle(vehicle_id):
    v = Vehicle.objects(id=vehicle_id).first()
    if not v:
        return jsonify({"error": "Not found"}), 404
    data = request.form.to_dict()
    v.update(
        vehicle_type=data.get('vehicle_type'),
        make_model=data.get('make_model'),
        year=int(data.get('year') or 0),
        capacity=int(data.get('capacity') or 0),
        fuel_type=data.get('fuel_type'),
        luggage_space=data.get('luggage_space'),
        status=data.get('status') or v.status,
        updated_at=datetime.utcnow()
    )
    return jsonify({"success": True, "message": "Vehicle updated"})


@admin_bp.route('/vehicle_management/<vehicle_id>/delete', methods=['POST'])
def delete_vehicle(vehicle_id):
    v = Vehicle.objects(id=vehicle_id).first()
    if not v:
        return jsonify({"error": "Not found"}), 404
    v.delete()
    return jsonify({"success": True, "message": "Vehicle deleted"})


# -------------- Pricing CRUD --------------
@admin_bp.route('/vehicle_management/pricing/add', methods=['POST'])
def add_pricing():
    data = request.form.to_dict()
    addons = {}
    # expected format: addons as JSON string or key-value pairs; keep simple here
    # admin UI will send JSON in addons field
    import json
    try:
        addons = json.loads(data.get('addons') or "{}")
    except Exception:
        addons = {}
    p = RentalPricing(
        vehicle_type=data.get('vehicle_type'),
        tier=data.get('tier') or 'tier1',
        base_fare_per_hour=float(data.get('base_fare_per_hour') or 0),
        base_fare_per_day=float(data.get('base_fare_per_day') or 0),
        vehicle_multiplier=float(data.get('vehicle_multiplier') or 1.0),
        addons=addons,
        tax_percent=float(data.get('tax_percent') or 18.0),
        commission_percent=float(data.get('commission_percent') or 10.0),
        peak_hour_multiplier=float(data.get('peak_hour_multiplier') or 1.0),
        effective_from=None,
        effective_to=None
    )
    p.save()
    return jsonify({"success": True, "message": "Pricing rule added", "id": str(p.id)})


@admin_bp.route('vehicle_management/pricing/<pricing_id>/update', methods=['POST'])
def update_pricing(pricing_id):
    p = RentalPricing.objects(id=pricing_id).first()
    if not p:
        return jsonify({"error": "Not found"}), 404
    data = request.form.to_dict()
    import json
    try:
        addons = json.loads(data.get('addons') or "{}")
    except Exception:
        addons = {}
    p.update(
        base_fare_per_hour=float(data.get('base_fare_per_hour') or p.base_fare_per_hour),
        base_fare_per_day=float(data.get('base_fare_per_day') or p.base_fare_per_day),
        vehicle_multiplier=float(data.get('vehicle_multiplier') or p.vehicle_multiplier),
        addons=addons,
        tax_percent=float(data.get('tax_percent') or p.tax_percent),
        commission_percent=float(data.get('commission_percent') or p.commission_percent),
        peak_hour_multiplier=float(data.get('peak_hour_multiplier') or p.peak_hour_multiplier),
    )
    return jsonify({"success": True, "message": "Pricing updated"})


@admin_bp.route('vehicle_management/pricing/<pricing_id>/delete', methods=['POST'])
def delete_pricing(pricing_id):
    p = RentalPricing.objects(id=pricing_id).first()
    if not p:
        return jsonify({"error": "Not found"}), 404
    p.delete()
    return jsonify({"success": True, "message": "Pricing deleted"})


# -------------- Availability / status change --------------
@admin_bp.route('vehicle_management/<vehicle_id>/set_status', methods=['POST'])
def set_vehicle_status(vehicle_id):
    v = Vehicle.objects(id=vehicle_id).first()
    if not v:
        return jsonify({"error": "Not found"}), 404
    status = request.form.get('status')
    v.update(status=status, updated_at=datetime.utcnow())
    return jsonify({"success": True, "message": "Status updated"})

@admin_bp.route("/ride_rental_management")
def ride_rental_management():
    return render_template("ride_rental_management.html")


# admin_rides.py
from flask import Blueprint, render_template, request, jsonify
from .model import AuditLog
from driver.drivermodel import  Driver
from passenger.model.ride_model import Ride
from .utils import find_nearest_drivers, haversine_km, driver_within_5km_exists
from datetime import datetime, timedelta
import uuid


# SocketIO will be attached in app factory; we'll use `socketio` imported in app context
socketio = None  # replaced in app init

@admin_bp.route('/ride_rental_management/monitor')
def monitor_ui():
    # main monitor page: server will load template which opens socket and receives updates
    return render_template('monitor.html')

# REST to create an on-demand ride (passenger app would call)
@admin_bp.route('/ride_rental_management/create_ride', methods=['POST'])
def create_ride():
    data = request.json
    ride = Ride(
        ride_id = str(uuid.uuid4())[:8],
        passenger_id = data['passenger_id'],
        passenger_name = data.get('passenger_name'),
        vehicle_type = data['vehicle_type'],
        pickup_lat = float(data['pickup_lat']),
        pickup_lng = float(data['pickup_lng']),
        drop_lat = float(data.get('drop_lat') or 0),
        drop_lng = float(data.get('drop_lng') or 0),
        status = 'searching',
        ride_type = data.get('ride_type', 'on_demand'),
        fare_estimate = float(data.get('fare_estimate') or 0)
    )
    ride.save()

    # push new ride to admin monitors + initiate dispatch
    socketio.emit('new_ride', {'ride': ride.to_mongo()}, namespace='/admin')
    # start dispatch procedure (synchronous call — will ping drivers via socket)
    dispatch_passenger_ride(ride.id)
    return jsonify({'ride_id': ride.ride_id})


# Cargo: broadcast and bids
@admin_bp.route('/ride_rental_management/create_cargo_request', methods=['POST'])
def create_cargo_request():
    data = request.json
    ride = Ride(
        ride_id = str(uuid.uuid4())[:8],
        passenger_id = data['passenger_id'],
        passenger_name = data.get('passenger_name'),
        vehicle_type = data['vehicle_type'],  # "Truck" etc
        pickup_lat = float(data['pickup_lat']), pickup_lng = float(data['pickup_lng']),
        drop_lat = float(data.get('drop_lat') or 0), drop_lng = float(data.get('drop_lng') or 0),
        status = 'bidding',
        ride_type = 'cargo',
        created_at = datetime.utcnow()
    )
    ride.save()
    # broadcast to nearby cargo drivers (within 10km perhaps)
    nearby = find_nearest_drivers(ride.pickup_lat, ride.pickup_lng, ride.vehicle_type, radius_km=10.0, limit=50)
    for d in nearby:
        socketio.emit('cargo_request', {'ride_id': str(ride.id), 'details': ride.to_mongo()}, to=f"driver_{str(d.id)}", namespace='/drivers')
    # push to admin monitors
    socketio.emit('cargo_created', {'ride': ride.to_mongo()}, namespace='/admin')
    return jsonify({'ride_id': ride.ride_id})

# Admin selects a bid (API)
@admin_bp.route('/ride_rental_management/cargo/select_bid', methods=['POST'])
def select_cargo_bid():
    ride_id = request.form.get('ride_id')
    driver_id = request.form.get('driver_id')
    ride = Ride.objects(id=ride_id).first()
    if not ride:
        return jsonify({'error':'ride not found'}), 404
    # assign driver_id
    ride.update(set__driver_id=driver_id, set__status='driver_assigned')
    # notify driver and passenger
    socketio.emit('cargo_bid_selected', {'ride_id': str(ride.id), 'driver_id': driver_id}, to=f"driver_{driver_id}", namespace='/drivers')
    socketio.emit('ride_assigned', {'ride_id': str(ride.id), 'driver_id': driver_id}, to=f"passenger_{ride.passenger_id}", namespace='/passenger')
    return jsonify({'success': True})


# returns JSON list of ongoing rides & drivers for initial populate
@admin_bp.route('/ride_rental_management/ongoing_rides')
def api_ongoing_rides():
    rides = Ride.objects(status__in=['searching','driver_assigned','ongoing','bidding'])
    drivers = Driver.objects()  # you might filter to online drivers
    return jsonify({
        'rides': [r.to_mongo() for r in rides],
        'drivers': [d.to_mongo() for d in drivers]
    })

@admin_bp.route('/ride_rental_management/ride/<ride_id>/bids')
def api_ride_bids(ride_id):
    r = Ride.objects(id=ride_id).first()
    return jsonify({'bids': r.bids if r else []})




@admin_bp.route("/ride_rental_management/rides")
def rides_waiting():
    query = Ride.objects

    # Filters
    ride_id = request.args.get("ride_id")
    passenger = request.args.get("passenger")
    vehicle_type = request.args.get("vehicle_type")
    status = request.args.get("status")

    if ride_id:
        query = query.filter(id=ride_id)
    if passenger:
        query = query.filter(passenger__name__icontains=passenger)
    if vehicle_type:
        query = query.filter(vehicle_type=vehicle_type)
    if status:
        query = query.filter(status=status)

    rides = query.all()
    return render_template("admin/assign_rides.html", rides=rides)


# Assign driver manually
@admin_bp.route("/ride_rental_management/assign_driver", methods=["POST"])
def assign_driver(ride_id):
    driver_id = request.form.get("driver_id")
    ride = Ride.objects.get(id=ride_id)
    driver = Driver.objects.get(id=driver_id)

    if driver.status != "available":
        flash("Driver is not available!", "danger")
        return redirect(url_for("admin_assign.rides_waiting"))

    # Assign driver
    ride.update(status="driver_assigned", driver=driver.id)
    driver.update(status="busy")

    # Notify both parties
    notify_driver(driver, f"You have been assigned to ride {ride.id}")
    notify_passenger(ride.passenger, f"Driver {driver.name} has been assigned to your ride.")

    flash(f"Driver {driver.name} assigned successfully!", "success")
    return redirect(url_for("admin_assign.rides_waiting"))

# Reassign driver
@admin_bp.route("/ride_rental_management/reassign", methods=["POST"])
def reassign_driver(ride_id):
    new_driver_id = request.form.get("driver_id")
    ride = Ride.objects.get(id=ride_id)
    new_driver = Driver.objects.get(id=new_driver_id)

    if new_driver.status != "available":
        flash("Driver is not available!", "danger")
        return redirect(url_for("admin_assign.rides_waiting"))

    # Release old driver if any
    if ride.driver:
        old_driver = Driver.objects.get(id=ride.driver)
        old_driver.update(status="available")

    # Assign new driver
    ride.update(driver=new_driver.id, status="driver_assigned")
    new_driver.update(status="busy")

    # Notifications
    notify_driver(new_driver, f"You have been reassigned to ride {ride.id}")
    notify_passenger(ride.passenger, f"Driver {new_driver.name} has been reassigned to your ride.")

    flash(f"Ride {ride.id} reassigned to {new_driver.name}", "success")
    return redirect(url_for("admin_assign.rides_waiting"))


@admin_bp.route("/ride_rental_management/complaint")
def list_complaints():
    complaints = Complaint.objects.all()
    for c in complaints:
        if c.category == "cancellation":
            ride = Ride.objects.get(id=c.ride_id)
            auto = calculate_cancellation_fee(ride, cancelled_by=c.user.role)
            c.auto_fee = auto["fee"]
            c.auto_reason = auto["reason"]
    return render_template("complain.html", complaints=complaints)

# Resolve complaint
@admin_bp.route("/ride_rental_management/resolve/<complaint_id>", methods=["POST"])
def resolve(complaint_id):
    complaint = Complaint.objects.get(id=complaint_id)
    override_action = request.form.get("override_action")
    notes = request.form.get("notes")

    if override_action == "system":
        fee = complaint.auto_fee
    elif override_action == "refund_full":
        fee = 0
    elif override_action == "refund_partial":
        fee = complaint.auto_fee / 2
    elif override_action == "waive_fee":
        fee = 0
    else:
        fee = complaint.auto_fee

    # Apply refund/charge
    process_refund_or_fee(complaint.ride_id, fee)

    complaint.update(
        status="resolved",
        resolution_notes=notes,
        applied_fee=fee,
        override_action=override_action,
    )
    flash(f"Complaint {complaint_id} resolved. Fee applied: ₹{fee}", "success")
    return redirect(url_for("admin_disputes.list_complaints"))




@admin_bp.route('/fare-pricing', methods=['GET'])
def fare_pricing_dashboard():
    city_tiers = CityTier.objects()
    pricing = FarePricing.objects()
    return render_template('fare_price.html', city_tiers=city_tiers, pricing=pricing)

@admin_bp.route('/fare-pricing/add', methods=['POST'])
def add_fare_pricing():
    vehicle_type = request.form.get('vehicle_type')
    ride_type = request.form.get('ride_type')
    tier = request.form.get('tier')
    base_fare = float(request.form.get('base_fare', 0))
    per_km = float(request.form.get('per_km', 0))
    per_minute = float(request.form.get('per_minute', 0))

    fare = FarePricing(
        vehicle_type=vehicle_type,
        ride_type=ride_type,
        tier=tier,
        base_fare=base_fare,
        per_km=per_km,
        per_minute=per_minute
    )
    fare.save()
    flash("Fare pricing added successfully!", "success")
    return redirect(url_for('admin.fare_pricing_dashboard'))

@admin_bp.route('/fare-pricing/city-tier/add', methods=['POST'])
def add_city_tier():
    city_name = request.form.get('city_name')
    tier = request.form.get('tier')
    city_tier = CityTier(city_name=city_name, tier=tier)
    city_tier.save()
    flash("City tier added successfully!", "success")
    return redirect(url_for('admin.fare_pricing_dashboard'))

import csv
from flask import request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
from .model import CityTier,ReferralRewardLog,ReferralReward,ReferralSetting,ReferralCode,FarePricing,FareRule,FareRuleAudit,CommissionRule,Complaint,Promotion

ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_FOLDER = 'uploads/'



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/fare-pricing/city-tier/upload', methods=['POST'])
def upload_city_tiers():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('fare.fare_pricing_dashboard'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('fare.fare_pricing_dashboard'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(admin_bp.config['UPLOAD_FOLDER'], filename)
        os.makedirs(admin_bp.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        
        # Read CSV and update DB
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                city_name = row.get('city_name')
                tier = row.get('tier')
                if city_name and tier:
                    CityTier.objects(city_name=city_name).update_one(upsert=True, set__tier=tier)
        flash('City tiers uploaded successfully!', 'success')
    else:
        flash('Invalid file format. Please upload a CSV.', 'danger')
    return redirect(url_for('admin.fare_pricing_dashboard'))

@admin_bp.route('/fare-pricing/update', methods=['POST'])
def update_fare_pricing():
    # Expect form data as fare_id[], base_fare[], per_km[], per_minute[]
    fare_ids = request.form.getlist('fare_id[]')
    base_fares = request.form.getlist('base_fare[]')
    per_kms = request.form.getlist('per_km[]')
    per_minutes = request.form.getlist('per_minute[]')

    for i, fare_id in enumerate(fare_ids):
        FarePricing.objects(id=fare_id).update_one(
            set__base_fare=float(base_fares[i]),
            set__per_km=float(per_kms[i]),
            set__per_minute=float(per_minutes[i])
        )
    flash("Fare pricing updated successfully!", "success")
    return redirect(url_for('admin.fare_pricing_dashboard'))

from flask import Blueprint, render_template, request, redirect, url_for, flash
import datetime


# Display all promotions
@admin_bp.route('/promotions')
def promotions_dashboard():
    promotions = Promotion.objects()
    referral = ReferralReward.objects.first()
    return render_template('promotions.html', promotions=promotions, referral=referral)

# Create new promotion
@admin_bp.route('/promotions/create', methods=['POST'])
def create_promotion():
    data = request.form
    promo = Promotion(
        promo_code=data['promo_code'],
        discount_type=data['discount_type'],
        discount_value=float(data['discount_value']),
        min_booking_amount=float(data.get('min_booking_amount', 0)),
        max_discount=float(data.get('max_discount', 0)),
        expiration_date=datetime.datetime.strptime(data['expiration_date'], "%Y-%m-%d"),
        usage_limit_per_user=int(data.get('usage_limit_per_user', 1)),
        total_usage_limit=int(data.get('total_usage_limit', 100)),
        active=bool(data.get('active', True))
    )
    promo.save()
    flash("Promotion created successfully!", "success")
    return redirect(url_for('admin.promotions_dashboard'))

# Edit/Deactivate promotion
@admin_bp.route('/promotions/<promo_id>/edit', methods=['POST'])
def edit_promotion(promo_id):
    promo = Promotion.objects.get(id=promo_id)
    data = request.form
    promo.update(
        set__discount_type=data['discount_type'],
        set__discount_value=float(data['discount_value']),
        set__min_booking_amount=float(data.get('min_booking_amount', 0)),
        set__max_discount=float(data.get('max_discount', 0)),
        set__expiration_date=datetime.datetime.strptime(data['expiration_date'], "%Y-%m-%d"),
        set__usage_limit_per_user=int(data.get('usage_limit_per_user', 1)),
        set__total_usage_limit=int(data.get('total_usage_limit', 100)),
        set__active=bool(data.get('active', True)),
        set__updated_at=datetime.datetime.utcnow()
    )
    flash("Promotion updated successfully!", "success")
    return redirect(url_for('admin.promotions_dashboard'))

# Update referral rewards
@admin_bp.route('/promotions/referral/update', methods=['POST'])
def update_referral():
    data = request.form
    referral = ReferralReward.objects.first()
    if referral:
        referral.update(
            set__user_reward=float(data['user_reward']),
            set__driver_reward=float(data['driver_reward']),
            set__active=bool(data.get('active', True)),
            set__updated_at=datetime.datetime.utcnow()
        )
    else:
        ReferralReward(
            user_reward=float(data['user_reward']),
            driver_reward=float(data['driver_reward']),
            active=True
        ).save()
    flash("Referral reward updated successfully!", "success")
    return redirect(url_for('admin.promotions_dashboard'))

from flask import Blueprint, render_template, request, redirect, url_for, flash

# View all commission rules
@admin_bp.route('/commissions')
def commissions_dashboard():
    rules = CommissionRule.objects()
    return render_template('commissions.html', rules=rules)

# Create or add commission rule
@admin_bp.route('/commissions/create', methods=['POST'])
def create_commission():
    data = request.form
    CommissionRule(
        vehicle_type=data['vehicle_type'],
        ride_type=data['ride_type'],
        commission_percentage=float(data['commission_percentage']),
        first_time_user_extra=float(data.get('first_time_user_extra', 2.0)),
        promo_applies=bool(data.get('promo_applies', True))
    ).save()
    flash("Commission rule created successfully!", "success")
    return redirect(url_for('admin.commissions_dashboard'))

# Edit commission rule
@admin_bp.route('/commissions/<rule_id>/edit', methods=['POST'])
def edit_commission(rule_id):
    rule = CommissionRule.objects.get(id=rule_id)
    data = request.form
    rule.update(
        set__vehicle_type=data['vehicle_type'],
        set__ride_type=data['ride_type'],
        set__commission_percentage=float(data['commission_percentage']),
        set__first_time_user_extra=float(data.get('first_time_user_extra', 2.0)),
        set__promo_applies=bool(data.get('promo_applies', True)),
        set__updated_at=datetime.datetime.utcnow()
    )
    flash("Commission rule updated successfully!", "success")
    return redirect(url_for('admin.commissions_dashboard'))

@admin_bp.route('/commissions/<rule_id>/edit-inline', methods=['POST'])
def edit_commission_inline(rule_id):
    data = request.get_json()
    rule = CommissionRule.objects.get(id=rule_id)
    rule.update(
        set__vehicle_type=data['vehicle_type'],
        set__ride_type=data['ride_type'],
        set__commission_percentage=float(data['commission_percentage']),
        set__first_time_user_extra=float(data['first_time_user_extra']),
        set__promo_applies=bool(data['promo_applies']),
        set__updated_at=datetime.datetime.utcnow()
    )
    return {"success": True}

import csv
from flask import Response

@admin_bp.route('/commissions/export')
def export_commissions():
    rules = CommissionRule.objects()
    def generate():
        yield 'vehicle_type,ride_type,commission_percentage,first_time_user_extra,promo_applies\n'
        for r in rules:
            yield f'{r.vehicle_type},{r.ride_type},{r.commission_percentage},{r.first_time_user_extra},{r.promo_applies}\n'
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition":"attachment;filename=commissions.csv"})

import csv
from werkzeug.utils import secure_filename

@admin_bp.route('/commissions/import', methods=['POST'])
def import_commissions():
    file = request.files['csv_file']
    csv_reader = csv.DictReader(file.stream.read().decode("utf-8").splitlines())
    for row in csv_reader:
        CommissionRule.objects(vehicle_type=row['vehicle_type'], ride_type=row['ride_type']).update(
            set__commission_percentage=float(row['commission_percentage']),
            set__first_time_user_extra=float(row['first_time_user_extra']),
            set__promo_applies=row['promo_applies'].lower() == 'true'
        )
    flash("CSV import completed!", "success")
    return redirect(url_for('admin.commissions_dashboard'))


from flask import Blueprint, render_template, request, redirect, url_for, jsonify


# Dashboard view
@admin_bp.route('/comission_fare')
def fare_dashboard():
    fare_rules = FareRule.query.all()
    return render_template('commission_fare.html', fare_rules=fare_rules)
from flask import request, jsonify
from .model import FareRule, FareRuleAudit
from bson import ObjectId
from datetime import datetime

@admin_bp.route('/comission_fare/edit/<string:rule_id>', methods=['POST'])
def edit_fare_rule(rule_id):
    try:
        # Fetch the FareRule document by ID
        rule = FareRule.objects(id=ObjectId(rule_id)).first()
        if not rule:
            return jsonify({"success": False, "message": "Rule not found"}), 404

        # Save old values for audit
        fields = ['city_tier','vehicle_type','ride_type','base_fare','per_km','per_minute','surge_percentage','platform_commission','active']
        old_values = {field: getattr(rule, field) for field in fields}

        # Update fields from request data
        data = request.json
        for key in data:
            if key in fields:
                setattr(rule, key, data[key])

        rule.save()  # Save changes to MongoDB

        # Log audit
        new_values = {field: getattr(rule, field) for field in fields}
        audit = FareRuleAudit(
            fare_rule_id=rule.id,
            changed_by="admin_user",  # Replace with current admin username
            old_values=str(old_values),
            new_values=str(new_values),
            timestamp=datetime.utcnow()
        )
        audit.save()  # Save audit log

        return jsonify({"success": True, "rule": new_values})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

    return jsonify({"success": True})

from flask import request, jsonify
from .model import FareRule  # MongoEngine model
from bson import ObjectId

@admin_bp.route('/comission_fare/toggle/<string:rule_id>', methods=['POST'])
def toggle_fare_rule(rule_id):
    try:
        # Fetch the FareRule document by ID
        rule = FareRule.objects(id=ObjectId(rule_id)).first()
        if not rule:
            return jsonify({"success": False, "message": "Rule not found"}), 404

        # Toggle the 'active' field
        rule.active = not rule.active
        rule.save()  # Save changes to MongoDB

        return jsonify({"success": True, "active": rule.active})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# CSV import/export placeholder
@admin_bp.route('/comission_fare/import', methods=['POST'])
def import_fare_rules():
    # CSV handling logic goes here
    return jsonify({"success": True})




from flask import Blueprint, render_template, request, jsonify

# Dashboard
@admin_bp.route('/referal_reword/')
def referral_dashboard():
    settings = ReferralSetting.query.first()
    logs = ReferralRewardLog.query.order_by(ReferralRewardLog.created_at.desc()).all()
    total_rewards = sum([log.reward_amount for log in logs if not log.revoked_by_admin])
    new_users = sum([1 for log in logs if log.user_type == 'rider' and not log.revoked_by_admin])
    new_drivers = sum([1 for log in logs if log.user_type == 'driver' and not log.revoked_by_admin])
    return render_template('referal_reword.html', settings=settings, logs=logs,
                           total_rewards=total_rewards, new_users=new_users, new_drivers=new_drivers)

#from flask import request, jsonify
from .model import ReferralSetting
from datetime import datetime

@admin_bp.route('/referal_reword/update_settings', methods=['POST'])
def update_settings():
    try:
        data = request.json
        settings = ReferralSetting.objects.first()  # get the first (or only) settings document
        if not settings:
            # If no settings exist yet, create a new one
            settings = ReferralSetting(
                user_reward=data.get('user_reward', 5),
                driver_reward=data.get('driver_reward', 10),
                active=data.get('active', True)
            )
        else:
            # Update existing settings
            settings.user_reward = data.get('user_reward', settings.user_reward)
            settings.driver_reward = data.get('driver_reward', settings.driver_reward)
            settings.active = data.get('active', settings.active)

        settings.updated_at = datetime.utcnow()
        settings.save()  # Save to MongoDB

        return jsonify({"success": True, "settings": {
            "user_reward": settings.user_reward,
            "driver_reward": settings.driver_reward,
            "active": settings.active
        }})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

from flask import request, jsonify
from datetime import datetime
from .model import ReferralRewardLog , Transaction

@admin_bp.route('/referal_reword/revoke/<string:log_id>', methods=['POST'])
def revoke_reward(log_id):
    try:
        data = request.json
        log = ReferralRewardLog.objects(id=log_id).first()  # fetch by ObjectId
        if not log:
            return jsonify({"success": False, "error": "Log not found"}), 404

        log.revoked_by_admin = True
        log.revoked_reason = data.get('reason', 'Fraudulent referral')
        log.status = 'revoked'
        log.save()  # save changes to MongoDB

        return jsonify({"success": True, "log_id": str(log.id)})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@admin_bp.route('/payment')
def payment_dashboard():
    # This will render the main page with subfunction links
    return render_template('payment_finance.html')

# Track All Transactions
# @admin_bp.route('/payment/transactions')
# def transactions():
#     # Filters
#     transaction_type = request.args.get('type', None)
#     user_id = request.args.get('user_id', None)
#     status = request.args.get('status', None)
    
#     query = Transaction.objects
#     if transaction_type:
#         query = query.filter(transaction_type=transaction_type)
#     if user_id:
#         query = query.filter(user_id=user_id)
#     if status:
#         query = query.filter(status=status)
        
#     transactions = query.order_by('-created_at')
#     return render_template('admin/transactions.html', transactions=transactions)

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta


@admin_bp.route('/payment/transactions')
def get_transactions():
    # Filters
    user_id = request.args.get('user_id')
    tx_type = request.args.get('type')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = {}
    if user_id: query['user_id'] = user_id
    if tx_type: query['transaction_type'] = tx_type
    if status: query['status'] = status
    if start_date and end_date:
        query['created_at'] = {'$gte': datetime.fromisoformat(start_date), '$lte': datetime.fromisoformat(end_date)}

    transactions = Transaction.objects(**query).order_by('-created_at')
    return jsonify([{
        'id': str(tx.id),
        'type': tx.transaction_type,
        'user_id': tx.user_id,
        'user_type': tx.user_type,
        'payment_method': tx.payment_method,
        'amount': tx.amount,
        'commission': tx.amount * tx.platform_commission / 100,
        'status': tx.status,
        'created_at': tx.created_at.isoformat()
    } for tx in transactions])


from mongoengine import Q
from datetime import datetime, timedelta
from flask import jsonify

@admin_bp.route('/payment/transactions/analytics')
def transaction_analytics():
    today = datetime.utcnow().date()
    start_week = today - timedelta(days=today.weekday())
    start_month = today.replace(day=1)

    transactions = Transaction.objects(status='completed')

    def sum_by_date(start):
        return sum(tx.amount for tx in transactions if tx.created_at.date() >= start)

    total_revenue = sum(tx.amount for tx in transactions)
    total_commission = sum(tx.amount * tx.platform_commission/100 for tx in transactions)
    daily_revenue = sum(tx.amount for tx in transactions if tx.created_at.date() == today)
    weekly_revenue = sum_by_date(start_week)
    monthly_revenue = sum_by_date(start_month)

    return jsonify({
        'total_revenue': total_revenue,
        'total_commission': total_commission,
        'daily_revenue': daily_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue
    })





from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from .model import RefundRequest
from driver.earn_model import DriverPayout

# Show all payout requests
@admin_bp.route('/payment/driver_payouts')
def list_payouts():
    payouts = DriverPayout.objects.order_by('-requested_at')
    return render_template('payouts.html', payouts=payouts)

# Approve a payout
@admin_bp.route('/payment/driver_payouts/approve/<payout_id>', methods=['POST'])
def approve_payout(payout_id):
    payout = DriverPayout.objects.get(id=payout_id)
    payout.status = 'approved'
    payout.processed_at = datetime.utcnow()
    payout.save()
    # TODO: trigger notification
    flash(f"Payout {payout.id} approved for Driver {payout.driver_id}", "success")
    return redirect(url_for('payout.list_payouts'))

# Reject a payout
@admin_bp.route('/payment/driver_payouts/reject/<payout_id>', methods=['POST'])
def reject_payout(payout_id):
    payout = DriverPayout.objects.get(id=payout_id)
    payout.status = 'rejected'
    payout.admin_note = request.form.get('note')
    payout.processed_at = datetime.utcnow()
    payout.save()
    # TODO: trigger notification
    flash(f"Payout {payout.id} rejected for Driver {payout.driver_id}", "danger")
    return redirect(url_for('admin.list_payouts'))

# Mark as processed (after actual transfer)
@admin_bp.route('/payment/driver_payouts/process/<payout_id>', methods=['POST'])
def process_payout(payout_id):
    payout = DriverPayout.objects.get(id=payout_id)
    payout.status = 'processed'
    payout.processed_at = datetime.utcnow()
    payout.save()
    # TODO: trigger notification
    flash(f"Payout {payout.id} processed for Driver {payout.driver_id}", "info")
    return redirect(url_for('admin.list_payouts'))





from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime


# List all refund requests
@admin_bp.route('/payment/refunds')
def list_refunds():
    refunds = RefundRequest.objects.order_by('-created_at')
    return render_template('refunds.html', refunds=refunds)

# Approve full refund
@admin_bp.route('/payment/refunds/approve/<refund_id>', methods=['POST'])
def approve_refund(refund_id):
    refund = RefundRequest.objects.get(id=refund_id)
    refund.status = 'approved'
    refund.amount_approved = refund.amount_requested
    refund.processed_at = datetime.utcnow()
    refund.save()
    flash(f"Refund {refund.id} approved for Passenger {refund.passenger_id}", "success")
    return redirect(url_for('refund.list_refunds'))

# Approve partial refund
@admin_bp.route('/payment/refunds/partial/<refund_id>', methods=['POST'])
def partial_refund(refund_id):
    refund = RefundRequest.objects.get(id=refund_id)
    amount = float(request.form.get('amount'))
    refund.status = 'partial'
    refund.amount_approved = amount
    refund.processed_at = datetime.utcnow()
    refund.admin_note = request.form.get('note')
    refund.save()
    flash(f"Partial refund of ₹{amount} approved for Passenger {refund.passenger_id}", "info")
    return redirect(url_for('refund.list_refunds'))

# Reject refund
@admin_bp.route('/payment/refunds/reject/<refund_id>', methods=['POST'])
def reject_refund(refund_id):
    refund = RefundRequest.objects.get(id=refund_id)
    refund.status = 'rejected'
    refund.admin_note = request.form.get('note')
    refund.processed_at = datetime.utcnow()
    refund.save()
    flash(f"Refund {refund.id} rejected for Passenger {refund.passenger_id}", "danger")
    return redirect(url_for('admin.list_refunds'))

# Mark refund as processed (after transfer)
@admin_bp.route('/payment/refunds/process/<refund_id>', methods=['POST'])
def process_refund(refund_id):
    refund = RefundRequest.objects.get(id=refund_id)
    refund.status = 'processed'
    refund.processed_at = datetime.utcnow()
    refund.save()
    flash(f"Refund {refund.id} processed for Passenger {refund.passenger_id}", "info")
    return redirect(url_for('admin.list_refunds'))



@admin_bp.route('/report_analiytics')
def report_analiytics():
    refunds = RideRentalHistory.objects.order_by('-created_at')
    return render_template('report_anaylitcs.html', refunds=refunds)
from .model import RideRentalHistory
from flask import Blueprint, render_template, request, send_file
import pandas as pd
from io import BytesIO
from datetime import datetime
# Show Ride / Rental History
@admin_bp.route("/report_analiytics/ride_history", methods=["GET", "POST"])
def ride_history():
    filters = {}
    query = RideRentalHistory.objects

    # Apply filters if submitted
    if request.method == "POST":
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        vehicle = request.form.get("vehicle")
        status = request.form.get("status")
        ride_type = request.form.get("ride_type")
        driver = request.form.get("driver")

        if start_date and end_date:
            query = query.filter(date__gte=start_date, date__lte=end_date)
        if vehicle:
            query = query.filter(vehicle=vehicle)
        if status:
            query = query.filter(status=status)
        if ride_type:
            query = query.filter(ride_type=ride_type)
        if driver:
            query = query.filter(driver=driver)


    # Pagination
    page = int(request.args.get("page", 1))
    per_page = 50
    total = query.count()
    rides = query.order_by("-date").skip((page - 1) * per_page).limit(per_page)

    total_pages = (total + per_page - 1) // per_page

    rides = query.order_by("-date")
    return render_template("ride_history.html", rides=rides, page=page, total_pages=total_pages,)


# Export Reports
@admin_bp.route("/report_analiytics/ride_history/export/<fmt>")
def export_ride_history(fmt):
    rides = RideRentalHistory.objects.order_by("-date")

    # Convert to DataFrame
    data = [{
        "Passenger": r.passenger,
        "Driver": r.driver,
        "Vehicle": r.vehicle,
        "Pickup": r.pickup,
        "Drop": r.drop,
        "Fare": r.fare,
        "Status": r.status,
        "Type": r.ride_type,
        "Date": r.date.strftime("%Y-%m-%d %H:%M")
    } for r in rides]

    df = pd.DataFrame(data)

    if fmt == "csv":
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(output, mimetype="text/csv", as_attachment=True, download_name="ride_history.csv",  fmt="csv")

    elif fmt == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="RideHistory")
        output.seek(0)
        return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         as_attachment=True, download_name="ride_history.xlsx",fmt="xlsx")

    elif fmt == "pdf":
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        from reportlab.lib import colors

        output = BytesIO()
        doc = SimpleDocTemplate(output)
        table_data = [df.columns.tolist()] + df.values.tolist()
        table = Table(table_data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black)
        ]))
        doc.build([table])
        output.seek(0)
        return send_file(output, mimetype="application/pdf", as_attachment=True, download_name="ride_history.pdf",fmt="pdf")

    return "Invalid format", 400


    

import csv
import io
from flask import make_response, send_file
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet


@admin_bp.route("/report_analiytics/revenue/export/<string:fmt>", methods=["POST"])
def export_revenue(fmt):
    # Re-run the aggregation with filters
    from datetime import datetime, timedelta

    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    period = request.form.get("period", "daily")

    if not start_date or not end_date:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    pipeline = [
        {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": {
                "year": {"$year": "$date"},
                "month": {"$month": "$date"},
                "day": {"$dayOfMonth": "$date"} if period == "daily" else None,
                "week": {"$week": "$date"} if period == "weekly" else None,
            },
            "total_revenue": {"$sum": "$fare"},
            "rides": {"$sum": {"$cond": [{"$eq": ["$ride_type", "Ride"]}, "$fare", 0]}},
            "rentals": {"$sum": {"$cond": [{"$eq": ["$ride_type", "Rental"]}, "$fare", 0]}},
            "commission": {"$sum": {"$multiply": ["$fare", 0.1]}},
            "driver_earnings": {"$sum": {"$multiply": ["$fare", 0.9]}},
        }},
        {"$sort": {"_id": 1}}
    ]

    results = list(RideRentalHistory.objects.aggregate(*pipeline))

    # Prepare rows for export
    rows = []
    for r in results:
        if period == "daily":
            label = f"{r['_id']['year']}-{r['_id']['month']:02d}-{r['_id']['day']:02d}"
        elif period == "weekly":
            label = f"Week {r['_id']['week']} {r['_id']['year']}"
        else:
            label = f"{r['_id']['month']:02d}/{r['_id']['year']}"

        rows.append({
            "Period": label,
            "Total Revenue": r["total_revenue"],
            "Rides": r["rides"],
            "Rentals": r["rentals"],
            "Commission": r["commission"],
            "Driver Earnings": r["driver_earnings"]
        })

    # Convert to DataFrame for CSV/Excel
    df = pd.DataFrame(rows)

    if fmt == "csv":
        output = io.StringIO()
        df.to_csv(output, index=False)
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=revenue_report.csv"
        response.headers["Content-Type"] = "text/csv"
        return response

    elif fmt == "excel":
        output = io.BytesIO()
        df.to_excel(output, index=False, sheet_name="Revenue")
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="revenue_report.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    elif fmt == "pdf":
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        elements = []
        style = getSampleStyleSheet()

        data = [["Period", "Total Revenue", "Rides", "Rentals", "Commission", "Driver Earnings"]]
        for row in rows:
            data.append(list(row.values()))

        table = Table(data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
            ("FONTSIZE", (0,0), (-1,-1), 8),
        ]))

        elements.append(Paragraph("Revenue Report", style["Title"]))
        elements.append(table)
        doc.build(elements)

        output.seek(0)
        return send_file(output, as_attachment=True, download_name="revenue_report.pdf", mimetype="application/pdf")

    return "Invalid format", 400

@admin_bp.route("/report_analiytics/driver-performance", methods=["GET", "POST"])
def driver_performance():
    from datetime import datetime, timedelta

    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    if not start_date or not end_date:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    pipeline = [
        {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": "$driver_id",
            "total_rides": {"$sum": {"$cond": [{"$eq": ["$ride_type", "Ride"]}, 1, 0]}},
            "total_rentals": {"$sum": {"$cond": [{"$eq": ["$ride_type", "Rental"]}, 1, 0]}},
            "accepted": {"$sum": {"$cond": [{"$eq": ["$status", "Accepted"]}, 1, 0]}},
            "rejected": {"$sum": {"$cond": [{"$eq": ["$status", "Rejected"]}, 1, 0]}},
            "avg_rating": {"$avg": "$rating"},
            "earnings": {"$sum": "$fare"},
        }},
        {"$sort": {"earnings": -1}}
    ]

    results = list(RideRentalHistory.objects.aggregate(*pipeline))

    # Enrich with driver info
    drivers = []
    for r in results:
        driver = Driver.objects(driver_id=r["_id"]).first()
        name = driver.name if driver else "Unknown"
        total_requests = r["accepted"] + r["rejected"]
        acceptance_rate = (r["accepted"] / total_requests * 100) if total_requests > 0 else 0
        rejection_rate = (r["rejected"] / total_requests * 100) if total_requests > 0 else 0

        drivers.append({
            "Driver": name,
            "Total Rides": r["total_rides"],
            "Total Rentals": r["total_rentals"],
            "Acceptance Rate": round(acceptance_rate, 2),
            "Rejection Rate": round(rejection_rate, 2),
            "Avg Rating": round(r["avg_rating"] or 0, 2),
            "Earnings": r["earnings"],
            "Incentives": driver.incentives if driver else 0,
            "Online Hours": getattr(driver, "online_hours", 0),
            "Utilization": getattr(driver, "utilization", 0)
        })

    return render_template("driver_performance.html", drivers=drivers,
                           start_date=start_date.strftime("%Y-%m-%d"),
                           end_date=end_date.strftime("%Y-%m-%d"))

@admin_bp.route("/notifications_alert")
def notifications_alert():
    return render_template("notification_alert.html")
# Platform-Wide Notifications page


@admin_bp.route("/notifications_alert/platform/create", methods=["POST"])
def create_notification():
    data = request.form
    target_users = request.form.getlist("target_users")
    delivery_methods = request.form.getlist("delivery_methods")

    notif = Notification(
        target_users=target_users,
        notification_type=data.get("notification_type"),
        delivery_methods=delivery_methods,
        message=data.get("message"),
        scheduled_time=datetime.strptime(data.get("scheduled_time"), "%Y-%m-%dT%H:%M"),
    ).save()

    # Broadcast via WebSocket
    socketio.emit("new_notification", {
        "id": str(notif.id),
        "message": notif.message,
        "type": notif.notification_type,
        "targets": notif.target_users,
        "methods": notif.delivery_methods,
        "scheduled_time": notif.scheduled_time.strftime("%Y-%m-%d %H:%M"),
    }, broadcast=True)

    return jsonify({"success": True, "id": str(notif.id)})


from flask import request, jsonify, render_template
from datetime import datetime
from .model import AdminAlert


# Admin Alerts Dashboard
@admin_bp.route("/notifications/admin-alerts", methods=["GET"])
def admin_alerts():
    alerts = AdminAlert.objects.order_by("-created_at")
    return render_template("admin_alert.html", alerts=alerts)

# API to create alerts (can be triggered automatically by system too)
@admin_bp.route("/notifications/admin-alerts/create", methods=["POST"])
def create_admin_alert():
    data = request.json
    alert = AdminAlert(
        alert_type=data.get("alert_type"),
        severity=data.get("severity", "medium"),
        message=data.get("message")
    ).save()

    # Broadcast alert in real-time
    socketio.emit("new_admin_alert", {
        "id": str(alert.id),
        "type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M"),
    }, broadcast=True)

    return jsonify({"success": True, "id": str(alert.id)})

# API to resolve an alert
@admin_bp.route("/notifications/admin-alerts/resolve/<alert_id>", methods=["POST"])
def resolve_admin_alert(alert_id):
    alert = AdminAlert.objects(id=alert_id).first()
    if not alert:
        return jsonify({"success": False, "error": "Alert not found"}), 404

    alert.resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.save()

    socketio.emit("alert_resolved", {"id": str(alert.id)}, broadcast=True)

    return jsonify({"success": True})
@admin_bp.route("/notifications/payment_notifications")
def payment_notifications():
    """
    Display payment notifications with sorting and filtering.
    Query params:
        - type: filter by payment type (success, refund, failed, pending)
        - sort: 'asc' or 'desc' by created_at
    """
    payment_type = request.args.get('type')  # e.g., ?type=refund
    sort_order = request.args.get('sort', 'desc')

    query = Transaction.objects
    if payment_type in ['success', 'refund', 'failed', 'pending']:
        query = query.filter(type=payment_type)

    if sort_order == 'asc':
        query = query.order_by('created_at')
    else:
        query = query.order_by('-created_at')

    notifications_list = []
    for n in query[:50]:
        notifications_list.append({
            "id": str(n.id),
            "type": n.type,
            "message": f"{n.user_name}: {n.description or ''} — ₹{n.amount}",
            "read": n.read
        })

    return render_template("payment_notifications.html", notifications=notifications_list,
                           selected_type=payment_type, sort_order=sort_order)

# --- Mark as read ---
@admin_bp.route("/notifications/payment_notifications/mark_read/<payment_id>", methods=["POST"])

def mark_payment_read_ajax(payment_id):
    """
    Mark a payment notification as read via AJAX.
    Returns JSON response.
    """
    payment = Transaction.objects(id=payment_id).first()
    if payment:
        payment.read = True
        payment.save()
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Payment not found"}), 404

from flask import jsonify

@admin_bp.route("/notifications/payment_notifications/fetch")
def fetch_payment_notifications():
    """
    Return latest payment notifications as JSON.
    Can be filtered or sorted if needed.
    """
    notifications = Transaction.objects.order_by('-created_at')[:50]

    notifications_list = []
    for n in notifications:
        notifications_list.append({
            "id": str(n.id),
            "type": n.type,
            "message": f"{n.user_name}: {n.description or ''} — ₹{n.amount}",
            "read": n.read
        })

    return jsonify(notifications_list)


@admin_bp.route("/notifications/complaint_notifications")
def complaint_notifications():
    """
    Display complaint notifications with sorting and filtering.
    """
    status_filter = request.args.get('status')  # optional filtering by status
    sort_order = request.args.get('sort', 'desc')

    query = Complaint.objects
    if status_filter in ['pending', 'resolved', 'in_progress']:
        query = query.filter(status=status_filter)

    if sort_order == 'asc':
        query = query.order_by('created_at')
    else:
        query = query.order_by('-created_at')

    complaints_list = []
    for c in query[:50]:
        complaints_list.append({
            "id": str(c.id),
            "user_name": c.user_name,
            "description": c.description,
            "status": c.status,
            "read": c.read
        })

    return render_template("complaint_notifications.html", complaints=complaints_list,
                           status_filter=status_filter, sort_order=sort_order)

# Mark complaint as read via AJAX
@admin_bp.route("/notifications/complaint_notifications/mark_read_ajax/<complaint_id>", methods=["POST"])
def mark_complaint_read_ajax(complaint_id):
    complaint = Complaint.objects(id=complaint_id).first()
    if complaint:
        complaint.read = True
        complaint.save()
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Complaint not found"}), 404

# Fetch latest complaints for auto-refresh
@admin_bp.route("/notifications/complaint_notifications/fetch")
def fetch_complaints():
    complaints = Complaint.objects.order_by('-created_at')[:50]
    complaints_list = []
    for c in complaints:
        complaints_list.append({
            "id": str(c.id),
            "user_name": c.user_name,
            "description": c.description,
            "status": c.status,
            "read": c.read
        })
    return jsonify(complaints_list)