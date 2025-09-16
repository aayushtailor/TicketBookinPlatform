from flask import Flask, render_template, request, jsonify, url_for, send_file
import razorpay
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os, traceback, qrcode, io, json



# ---- CONFIG ----
app = Flask(__name__)
application=app
# DB setup
BASEDIR = os.path.abspath(os.path.dirname(__file__))
DB_FILENAME = "bookings.db"
DB_PATH = os.path.join(BASEDIR, DB_FILENAME)
print("DB path (will be used):", DB_PATH)

# Razorpay keys (TEST MODE)
RAZORPAY_KEY_ID = "rzp_test_RGZngIKJRY2DJd"
RAZORPAY_KEY_SECRET = "QEk7cZL0d34eWk11XrefGHx9"
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# SQLAlchemy config
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# ---- MODEL ----
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(15))
    state = db.Column(db.String(50))
    city = db.Column(db.String(50))
    date = db.Column(db.String(20))
    time = db.Column(db.String(50))
    ticket_type = db.Column(db.String(50))
    quantity = db.Column(db.Integer)
    payment_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)


with app.app_context():
    db.create_all()
    print("✅ Database tables created")


# ---- ROUTES ----
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/booking")
def booking_page():
    return render_template("booking.html", razorpay_key_id=RAZORPAY_KEY_ID)


@app.route("/confirmation/<int:booking_id>")
def confirmation_page(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template("confirmation.html", booking=booking)


@app.route("/admin")
def admin_panel():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template("admin.html", bookings=bookings)


# === QR & Verification ===
@app.route("/ticket/<int:booking_id>/qrcode")
def ticket_qr(booking_id):
    """Generate QR with verify URL"""
    booking = Booking.query.get_or_404(booking_id)
    verify_url = url_for("verify_ticket_page", booking_id=booking.id, _external=True)
    img = qrcode.make(verify_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/verify/<int:booking_id>")
def verify_ticket_page(booking_id):
    """Staff-facing page to view details + verify button"""
    booking = Booking.query.get_or_404(booking_id)
    return render_template("verify.html", booking=booking)


@app.route("/api/verify_ticket/<int:booking_id>", methods=["POST"])
def api_verify_ticket(booking_id):
    """Mark ticket as used"""
    booking = Booking.query.get_or_404(booking_id)

    if booking.used:
        return jsonify({"success": False, "message": "❌ Ticket already used"}), 400

    booking.used = True
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "✅ Ticket verified",
        "booking_id": booking.id,
        "name": booking.name,
        "time": booking.time,
        "quantity": booking.quantity,
        "ticket_type": booking.ticket_type
    })


# === Razorpay Integration ===
@app.route("/create_order", methods=["POST"])
def create_order():
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        quantity = int(data.get("quantity", 1))
        ticket_type = data.get("ticket_type", "indian_adult")

        prices = {
            "indian_adult": 210.04,
            "indian_child": 105.02,
            "foreign_adult": 420.08,
            "foreign_child": 210.04,
            "luxury_private": 210.04 * 15
        }

        ticket_price = prices.get(ticket_type, 210.04)
        total_amount = ticket_price * quantity if ticket_type != "luxury_private" else ticket_price
        amount_paise = int(total_amount * 100)

        order = razorpay_client.order.create(dict(
            amount=amount_paise,
            currency="INR",
            payment_capture=1
        ))
        return jsonify(order)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@app.route("/verify_payment", methods=["POST"])
def verify_payment():
    try:
        data = request.get_json()
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_signature = data.get("razorpay_signature")

        if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
            return jsonify({"success": False, "message": "Missing Razorpay fields"}), 400

        # Verify Razorpay signature
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })

        # Save booking details
        booking_data = data.get("booking_data", {})
        new_booking = Booking(
            name=booking_data.get("name"),
            email=booking_data.get("email"),
            phone=booking_data.get("phone"),
            state=booking_data.get("state"),
            city=booking_data.get("city"),
            date=booking_data.get("date") or datetime.utcnow().strftime("%Y-%m-%d"),
            time=booking_data.get("time"),
            ticket_type=booking_data.get("ticket_type"),
            quantity=int(booking_data.get("quantity", 1)),
            payment_id=razorpay_payment_id
        )

        db.session.add(new_booking)
        db.session.commit()

        return jsonify({"success": True, "booking_id": new_booking.id})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 400


# ---- START ----
if __name__ == "__main__":
    app.run(debug=True)
    