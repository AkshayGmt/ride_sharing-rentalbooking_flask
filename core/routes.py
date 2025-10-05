from flask import Blueprint, render_template, request, session

core_bp = Blueprint("core", __name__, template_folder="templates")

# Secret keyword to reveal admin login
SECRET_KEYWORD = "superaccess"
@core_bp.route("/", methods=["GET"])
def home():
    keyword = request.args.get("keyword", "").strip().lower()
    show_admin = keyword == SECRET_KEYWORD


    return render_template("home.html", show_admin=show_admin)

@core_bp.route("/passenger")
def passenger_page():
    return render_template("passenger.html")


@core_bp.route("/driver")
def driver_page():
    return render_template("driver.html")


@core_bp.route("/career")
def career_page():
    return render_template("career.html")


@core_bp.route("/contact")
def contact_page():
    return render_template("contact.html")


@core_bp.route("/terms")
def terms_page():
    return render_template("terms.html")
