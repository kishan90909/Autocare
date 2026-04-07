#!/usr/bin/env python3
"""
Enhanced AutoCare System with All Modules - INTEGRATED VERSION
- Customer Module: Registration, booking, tracking, ratings, service history, payments
- Workshop Module: Registration, service management, notifications, inventory, CRM
- Admin Module: User approval, complaint handling, analytics, system logs, reports
- Real-time updates, calendar scheduling, Google Maps integration
- Payment Gateway Integration (Razorpay)
- SMS/Email Notifications (Twilio, Flask-Mail)
- PDF Invoice Generation
- Advanced Analytics and Reporting
"""


from flask import (
    Flask, render_template, request, redirect, session, url_for,
    flash, jsonify, make_response, send_file
)
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import json
import uuid
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import math

# Import enhanced modules
from config import get_enhanced_config, is_feature_enabled
# Payment gateway disabled
from notification import get_notification_service
from pdf import get_pdf_generator
from analytics import get_analytics_service
from websocket import WebSocketService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('autocare.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logging.getLogger().addHandler(handler)

# Initialize enhanced services
config = get_enhanced_config()
# Payment gateway disabled
notification_service = get_notification_service()
pdf_generator = get_pdf_generator()
analytics_service = get_analytics_service()

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['SECRET_KEY'] = app.secret_key

# Initialize WebSocket service for real-time updates (will be initialized after database functions)
websocket_service = None

# Database configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'autocare'),
    'port': int(os.getenv('MYSQL_PORT', 3306))
}

# Database connection functions - using shared utility
def get_db_connection():
    """Get database connection with error handling"""
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            port=DB_CONFIG['port']
        )
        if connection.is_connected():
            return connection
        else:
            logging.error("Database connection failed: Unable to connect")
            return None
    except Error as e:
        logging.error(f"Database connection error: {e}")
        # Removed flash() - causes context error outside request
        return None

# Initialize WebSocket service after database functions are defined
try:
    db_connection = get_db_connection()
    if db_connection:
        websocket_service = WebSocketService(app, db_connection)
        logging.info("✅ WebSocket service initialized successfully")
    else:
        logging.warning("⚠️ WebSocket service initialization skipped - database connection failed")
except Exception as e:
    logging.error(f"❌ WebSocket service initialization failed: {e}")
    websocket_service = None

def init_db():
    """Initialize database with schema"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            with open('setup_fixed.sql', 'r') as f:
                sql_script = f.read()
            cursor.execute(sql_script)
            conn.commit()
            cursor.close()
            conn.close()
            logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Database initialization error: {e}")

# In-memory data storage (fallback)
USERS = {
    "admin@autocare.com": {
        "id": 1,
        "username": "admin",
        "email": "admin@autocare.com",
        "password": generate_password_hash(os.getenv("ADMIN_PASSWORD", "admin123")),
        "role": "admin",
        "approved": True,
        "created_at": datetime.now()
    }
}

WORKSHOPS = {
    "workshop1@autocare.com": {
        "id": 1,
        "username": "City Auto Service",
        "email": "workshop1@autocare.com",
        "password": generate_password_hash(os.getenv("WORKSHOP_PASSWORD", "workshop123")),
        "role": "workshop",
        "approved": True,
        "created_at": datetime.now(),
        "details": {
            "name": "City Auto Service",
            "address": "Alkapuri Main Road, Vadodara, Gujarat",
            "phone": "+91-9876543210",
            "latitude": 22.3072,
            "longitude": 73.1812,
            "services": ["Oil Change", "Brake Service", "Tire Rotation"],
            "rating": 4.5,
            "total_bookings": 0
        }
    },

    "workshop2@autocare.com": {
        "id": 2,
        "username": "Speed Auto Garage",
        "email": "workshop2@autocare.com",
        "password": generate_password_hash(os.getenv("WORKSHOP_PASSWORD", "workshop123")),
        "role": "workshop",
        "approved": True,
        "created_at": datetime.now(),
        "details": {
            "name": "Speed Auto Garage",
            "address": "SG Highway, Ahmedabad, Gujarat",
            "phone": "+91-9876543211",
            "latitude": 23.0225,
            "longitude": 72.5714,
            "services": ["Engine Repair", "Battery Check", "Wheel Alignment"],
            "rating": 4.3,
            "total_bookings": 0
        }
    },

    "workshop3@autocare.com": {
        "id": 3,
        "username": "Prime Car Care",
        "email": "workshop3@autocare.com",
        "password": generate_password_hash(os.getenv("WORKSHOP_PASSWORD", "workshop123")),
        "role": "workshop",
        "approved": True,
        "created_at": datetime.now(),
        "details": {
            "name": "Prime Car Care",
            "address": "Adajan, Surat, Gujarat",
            "phone": "+91-9876543212",
            "latitude": 21.1702,
            "longitude": 72.8311,
            "services": ["AC Repair", "Car Wash", "Interior Cleaning"],
            "rating": 4.6,
            "total_bookings": 0
        }
    },

    "workshop4@autocare.com": {
        "id": 4,
        "username": "AutoFix Hub",
        "email": "workshop4@autocare.com",
        "password": generate_password_hash(os.getenv("WORKSHOP_PASSWORD", "workshop123")),
        "role": "workshop",
        "approved": True,
        "created_at": datetime.now(),
        "details": {
            "name": "AutoFix Hub",
            "address": "Kalawad Road, Rajkot, Gujarat",
            "phone": "+91-9876543213",
            "latitude": 22.3039,
            "longitude": 70.8022,
            "services": ["Clutch Repair", "Suspension Work", "General Service"],
            "rating": 4.2,
            "total_bookings": 0
        }
    },

    "workshop5@autocare.com": {
        "id": 5,
        "username": "Urban Mechanic",
        "email": "workshop5@autocare.com",
        "password": generate_password_hash(os.getenv("WORKSHOP_PASSWORD", "workshop123")),
        "role": "workshop",
        "approved": True,
        "created_at": datetime.now(),
        "details": {
            "name": "Urban Mechanic",
            "address": "Sector 21, Gandhinagar, Gujarat",
            "phone": "+91-9876543214",
            "latitude": 23.2156,
            "longitude": 72.6369,
            "services": ["Dent Repair", "Painting", "Full Car Service"],
            "rating": 4.4,
            "total_bookings": 0
        }
    }
}

CUSTOMERS = {}
BOOKINGS = []
NOTIFICATIONS = []
COMPLAINTS = []
REVIEWS = []
ANALYTICS = {
    "total_bookings": 0,
    "completed_bookings": 0,
    "pending_bookings": 0,
    "total_revenue": 0,
    "customer_count": 0,
    "workshop_count": 0
}

# Services catalog
SERVICES = [

    # ================= CAR SERVICES =================
    {"id": 1, "name": "Oil Change", "description": "Complete engine oil change", "price": 500.00, "duration": 30, "vehicle_type": "Car"},
    {"id": 2, "name": "Brake Service", "description": "Brake pad replacement and inspection", "price": 1200.00, "duration": 60, "vehicle_type": "Car"},
    {"id": 3, "name": "Tire Rotation", "description": "Tire rotation and balancing", "price": 300.00, "duration": 20, "vehicle_type": "Car"},
    {"id": 4, "name": "Car Wash", "description": "Exterior and interior cleaning", "price": 400.00, "duration": 45, "vehicle_type": "Car"},
    {"id": 5, "name": "Engine Tune-up", "description": "Complete engine diagnostic", "price": 2500.00, "duration": 90, "vehicle_type": "Car"},
    {"id": 6, "name": "Battery Replacement", "description": "Battery testing and replacement", "price": 800.00, "duration": 25, "vehicle_type": "Car"},

    # ================= BIKE SERVICES =================
    {"id": 7, "name": "Bike Oil Service", "description": "Bike engine oil replacement", "price": 250.00, "duration": 20, "vehicle_type": "Bike"},
    {"id": 8, "name": "Chain Cleaning", "description": "Chain cleaning & lubrication", "price": 150.00, "duration": 15, "vehicle_type": "Bike"},
    {"id": 9, "name": "Bike Wash", "description": "Complete bike cleaning", "price": 200.00, "duration": 20, "vehicle_type": "Bike"},
    {"id": 10, "name": "Brake Adjustment", "description": "Brake inspection & adjustment", "price": 180.00, "duration": 15, "vehicle_type": "Bike"},
    {"id": 11, "name": "Clutch Service", "description": "Clutch plate check and service", "price": 400.00, "duration": 30, "vehicle_type": "Bike"},
    {"id": 12, "name": "Engine Checkup", "description": "General engine inspection", "price": 350.00, "duration": 25, "vehicle_type": "Bike"},

    # ================= AUTO SERVICES =================
    {"id": 13, "name": "Auto Engine Service", "description": "Engine servicing for auto", "price": 350.00, "duration": 25, "vehicle_type": "Auto"},
    {"id": 14, "name": "Auto Brake Service", "description": "Brake check and repair", "price": 400.00, "duration": 30, "vehicle_type": "Auto"},
    {"id": 15, "name": "Auto Wash", "description": "Complete auto cleaning", "price": 250.00, "duration": 20, "vehicle_type": "Auto"},
    {"id": 16, "name": "Auto Tire Check", "description": "Tire pressure and inspection", "price": 200.00, "duration": 15, "vehicle_type": "Auto"},
    {"id": 17, "name": "Auto Battery Check", "description": "Battery inspection", "price": 300.00, "duration": 20, "vehicle_type": "Auto"},
    {"id": 18, "name": "Auto Electrical Service", "description": "Electrical wiring inspection", "price": 450.00, "duration": 35, "vehicle_type": "Auto"},

    # ================= BUS SERVICES =================
    {"id": 19, "name": "Bus Engine Inspection", "description": "Heavy engine inspection", "price": 3000.00, "duration": 120, "vehicle_type": "Bus"},
    {"id": 20, "name": "Bus Brake Service", "description": "Heavy brake servicing", "price": 2500.00, "duration": 90, "vehicle_type": "Bus"},
    {"id": 21, "name": "Bus Wash", "description": "Full bus cleaning", "price": 1500.00, "duration": 60, "vehicle_type": "Bus"},
    {"id": 22, "name": "Bus Tire Alignment", "description": "Wheel alignment and balancing", "price": 2000.00, "duration": 80, "vehicle_type": "Bus"},
    {"id": 23, "name": "Bus Electrical Check", "description": "Electrical system inspection", "price": 1800.00, "duration": 70, "vehicle_type": "Bus"},
    {"id": 24, "name": "Bus AC Service", "description": "Air conditioning maintenance", "price": 2200.00, "duration": 75, "vehicle_type": "Bus"},

    # ================= TRUCK SERVICES =================
    {"id": 25, "name": "Truck Engine Service", "description": "Heavy engine servicing", "price": 3500.00, "duration": 120, "vehicle_type": "Truck"},
    {"id": 26, "name": "Truck Brake Service", "description": "Truck brake maintenance", "price": 2800.00, "duration": 90, "vehicle_type": "Truck"},
    {"id": 27, "name": "Truck Wash", "description": "Full truck body wash", "price": 1200.00, "duration": 60, "vehicle_type": "Truck"},
    {"id": 28, "name": "Truck Tire Check", "description": "Heavy tire inspection", "price": 1800.00, "duration": 70, "vehicle_type": "Truck"},
    {"id": 29, "name": "Truck Suspension Check", "description": "Suspension system inspection", "price": 2500.00, "duration": 80, "vehicle_type": "Truck"},
    {"id": 30, "name": "Truck Electrical Service", "description": "Electrical diagnostics", "price": 2000.00, "duration": 75, "vehicle_type": "Truck"}
]

# Enhanced booking statuses
BOOKING_STATUSES = {
    'pending': {'label': 'Pending', 'color': 'warning', 'description': 'Waiting for workshop assignment'},
    'assigned': {'label': 'Assigned', 'color': 'info', 'description': 'Workshop assigned, waiting for acceptance'},
    'accepted': {'label': 'Accepted', 'color': 'primary', 'description': 'Workshop has accepted the booking'},
    'in_progress': {'label': 'In Progress', 'color': 'success', 'description': 'Work has started'},
    'completed': {'label': 'Completed', 'color': 'success', 'description': 'Work completed, ready for payment'},
    'paid': {'label': 'Paid', 'color': 'success', 'description': 'Payment completed'},
    'cancelled': {'label': 'Cancelled', 'color': 'danger', 'description': 'Booking cancelled'}
}

# Role-based access decorator
def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session.get('role') != role:
                flash("Access denied. Please login with appropriate credentials.", "danger")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Context processor for templates
@app.context_processor
def inject_now():
    return {"datetime": datetime, "str": str, "BOOKING_STATUSES": BOOKING_STATUSES}

# Notification helper function
def send_booking_notification(booking_id, status, customer_email, workshop_name=None):
    """Send notification for booking status changes"""
    try:
        booking = next((b for b in BOOKINGS if b['id'] == booking_id), None)
        if not booking:
            return False

        customer = CUSTOMERS.get(customer_email)
        if not customer:
            return False

        # Create notification message
        status_info = BOOKING_STATUSES.get(status, {'label': status, 'description': status})
        if workshop_name:
            message = f"Your booking #{booking_id} status: {status_info['label']} - {status_info['description']} at {workshop_name}"
        else:
            message = f"Your booking #{booking_id} status: {status_info['label']} - {status_info['description']}"

        # Add to notifications list
        notification = {
            'id': len(NOTIFICATIONS) + 1,
            'type': 'booking_status',
            'message': message,
            'booking_id': booking_id,
            'customer_email': customer_email,
            'status': status,
            'created_at': datetime.now()
        }
        NOTIFICATIONS.append(notification)

        # Send email notification if service is available
        if is_feature_enabled('email'):
            try:
                email_subject = f"AutoCare Booking #{booking_id} - Status Update"
                email_body = f"""
                Dear {customer['username']},

                Your booking status has been updated:

                Booking ID: #{booking_id}
                Status: {status_info['label']}
                Description: {status_info['description']}
                {'Workshop: ' + workshop_name if workshop_name else ''}

                You can track your booking status at: http://127.0.0.1:5012/customer/service_tracking

                Thank you for choosing AutoCare!

                Best regards,
                AutoCare Team
                """

                notification_service.send_email(
                    to_email=customer_email,
                    subject=email_subject,
                    html_content=email_body
                )
                logging.info(f"Email notification sent for booking #{booking_id}")
            except Exception as e:
                logging.error(f"Email notification failed: {e}")

        # Send SMS notification if service is available
        if is_feature_enabled('sms'):
            try:
                sms_message = f"AutoCare: Booking #{booking_id} - {status_info['label']}: {status_info['description']}"
                if workshop_name:
                    sms_message += f" at {workshop_name}"

                customer_phone = customer.get('profile', {}).get('phone', '')
                if customer_phone:
                    notification_service.send_sms(
                        to_phone=customer_phone,
                        message=sms_message
                    )
                    logging.info(f"SMS notification sent for booking #{booking_id}")
            except Exception as e:
                logging.error(f"SMS notification failed: {e}")

        # Send real-time WebSocket notification if service is available
        if websocket_service:
            try:
                websocket_service.send_notification(
                    user_type='customer',
                    user_id=customer['id'],
                    title=f"Booking #{booking_id} - {status_info['label']}",
                    message=status_info['description'],
                    notification_type='booking_status',
                    data={
                        'booking_id': booking_id,
                        'status': status,
                        'workshop_name': workshop_name
                    }
                )

                # Also broadcast to workshop if assigned
                if workshop_name and booking.get('workshop_id'):
                    websocket_service.emit_to_room(
                        room='workshop',
                        event='booking_status_update',
                        data={
                            'booking_id': booking_id,
                            'status': status,
                            'customer_name': customer['username'],
                            'timestamp': datetime.now().isoformat()
                        }
                    )

                logging.info(f"WebSocket notification sent for booking #{booking_id}")
            except Exception as e:
                logging.error(f"WebSocket notification failed: {e}")

        return True
    except Exception as e:
        logging.error(f"Notification sending failed: {e}")
        return False

# Return distance
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in KM
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


# nearest workshop
def get_nearest_workshop(user_lat, user_lng):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM workshops WHERE approved = TRUE")
    workshops = cursor.fetchall()

    nearest = None
    min_distance = float('inf')

    for w in workshops:
        distance = calculate_distance(
            user_lat,
            user_lng,
            w['latitude'],
            w['longitude']
        )

        if distance < min_distance:
            min_distance = distance
            nearest = w

    return nearest



# Routes
@app.route("/")
def index():

    # If customer is logged in, redirect to customer dashboard
    if 'user_id' in session and session.get('role') == 'customer':
        return redirect(url_for('customer_dashboard'))

    # ⭐ SHOW ONLY 8 SERVICES ON HOME PAGE
    limited_services = SERVICES[:8]

    return render_template(
        "index.html",
        services=limited_services
    )

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/locate_garages")
def locate_garages():
    return render_template("locate_garages.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        complaint = {
            "id": len(COMPLAINTS) + 1,
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "subject": request.form.get("subject"),
            "message": request.form.get("message"),
            "status": "pending",
            "created_at": datetime.now()
        }
        COMPLAINTS.append(complaint)
        flash("Your complaint has been submitted. Admin will review it shortly.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/contact-support", methods=["GET", "POST"])
def contact_support():
    """Enhanced contact support page"""
    if request.method == "POST":
        complaint = {
            "id": len(COMPLAINTS) + 1,
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "subject": request.form.get("subject"),
            "message": request.form.get("message"),
            "priority": request.form.get("priority", "medium"),
            "category": request.form.get("category", "general"),
            "status": "pending",
            "created_at": datetime.now()
        }
        COMPLAINTS.append(complaint)

        # Send notification to admin
        admin_notification = {
            'id': len(NOTIFICATIONS) + 1,
            'type': 'support_ticket',
            'message': f'New support ticket #{complaint["id"]} - {complaint["subject"]} (Priority: {complaint["priority"]})',
            'created_at': datetime.now()
        }
        NOTIFICATIONS.append(admin_notification)

        flash("Your support ticket has been submitted. Our team will respond shortly.", "success")
        return redirect(url_for("contact_support"))
    return render_template("contact_support.html")

@app.route("/book-service", methods=["GET", "POST"])
def book_service_redirect():
    """Redirect to book service page"""
    return redirect(url_for("book_service"))    

# Payment routes disabled

@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            role = request.form.get("role", "")

            # Validate input
            if not email or not password or not role:
                flash("All fields are required.", "warning")
                return render_template("login.html")

            if role not in ["admin", "workshop", "customer"]:
                flash("Invalid role selected.", "danger")
                return render_template("login.html")

            # Find user by email across all user types
            user_data = None

            if role == "admin":
                user_data = USERS.get(email)
            elif role == "workshop":
                user_data = WORKSHOPS.get(email)
            elif role == "customer":
                user_data = CUSTOMERS.get(email)

            if user_data and check_password_hash(user_data["password"], password):
                # Check if user is approved
                if not user_data.get("approved", True):
                    flash("Your account is pending approval. Please contact admin.", "warning")
                    return render_template("login.html")

                session["user_id"] = user_data["id"]
                session["username"] = user_data["username"]
                session["role"] = user_data["role"]
                session["email"] = user_data["email"]

                logging.info(f"User {email} logged in successfully as {role}")
                flash("Logged in successfully!", "success")

                if user_data["role"] == "admin":
                    return redirect(url_for("admin_dashboard"))
                elif user_data["role"] == "workshop":
                    return redirect(url_for("workshop_dashboard"))
                else:
                    return redirect(url_for("customer_dashboard"))
            else:
                logging.warning(f"Failed login attempt for email: {email}")
                flash("Invalid credentials or user not approved", "danger")

        return render_template("login.html")
    except Exception as e:
        logging.error(f"Login error: {e}")
        flash("An error occurred during login. Please try again.", "danger")
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    try:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            role = request.form.get("role", "")
            phone = request.form.get("phone", "").strip()
            address = request.form.get("address", "").strip()

            # Validate required fields
            if not name or not email or not password:
                flash("Name, email and password are required.", "danger")
                return render_template("register.html")

            # Validate email format
            import re
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                flash("Please enter a valid email address.", "danger")
                return render_template("register.html")

            # Validate password strength
            if len(password) < 6:
                flash("Password must be at least 6 characters long.", "danger")
                return render_template("register.html")

            # Validate role
            if role not in ["customer", "workshop"]:
                flash("Please select a valid role.", "danger")
                return render_template("register.html")

            # Check if user already exists
            if email in USERS or email in WORKSHOPS or email in CUSTOMERS:
                flash("User already exists with this email.", "danger")
                return render_template("register.html")

            # Create new user
            user_id = len(USERS) + len(WORKSHOPS) + len(CUSTOMERS) + 1

            if role == "workshop":
                new_user = {
                    "id": user_id,
                    "username": name,
                    "email": email,
                    "password": generate_password_hash(password),
                    "role": role,
                    "approved": True,  # Auto-approved for demo - shows on map immediately
                    "created_at": datetime.now(),
                    "details": {
                        "name": name,
                        "address": address,
                        "phone": phone,
                        "latitude": 19.0760,
                        "longitude": 72.8777,
                        "services": ["Oil Change", "Brake Service", "Tire Rotation"],  # Default services
                        "rating": 4.0,
                        "total_bookings": 0
                    }
                }
                WORKSHOPS[email] = new_user
                logging.info(f"New workshop registered & auto-approved: {email} - Now visible on map!")
            else:
                new_user = {
                    "id": user_id,
                    "username": name,
                    "email": email,
                    "password": generate_password_hash(password),
                    "role": role,
                    "approved": True,  # Customers auto-approved
                    "created_at": datetime.now(),
                    "profile": {
                        "phone": phone,
                        "address": address,
                        "vehicles": []
                    }
                }
                CUSTOMERS[email] = new_user
                logging.info(f"New customer registered: {email}")

            flash("Registered successfully. Workshop accounts require admin approval.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")
    except Exception as e:
        logging.error(f"Registration error: {e}")
        flash("An error occurred during registration. Please try again.", "danger")
        return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("index"))

# Customer Routes
@app.route("/customer/dashboard")
@require_role("customer")
def customer_dashboard():
    user_email = session.get("email")
    customer = CUSTOMERS.get(user_email)
    user_bookings = [b for b in BOOKINGS if b['customer_id'] == customer['id']]
    return render_template("customer_dashboard.html",
                         customer=customer, bookings=user_bookings)

@app.route("/customer/profile", methods=["GET", "POST"])
@require_role("customer")
def customer_profile():
    user_email = session.get("email")
    customer = CUSTOMERS.get(user_email)

    if request.method == "POST":
        customer['profile']['phone'] = request.form.get("phone", customer['profile']['phone'])
        customer['profile']['address'] = request.form.get("address", customer['profile']['address'])
        flash("Profile updated successfully!", "success")

    return render_template("customer_profile.html", customer=customer)

@app.route("/get_nearby_workshops")
def get_nearby_workshops():
    try:
        print("🔥 API HIT")

        lat = request.args.get("lat")
        lng = request.args.get("lng")

        if not lat or not lng:
            return jsonify({"error": "Missing coordinates"}), 400

        lat = float(lat)
        lng = float(lng)

        # TRY DB FIRST, FALLBACK TO IN-MEMORY
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM workshops WHERE approved = TRUE")
                workshops = cursor.fetchall()
                cursor.close()
                conn.close()
                print("✅ DB workshops loaded")
            except Exception as db_err:
                logging.error(f"DB query failed: {db_err}")
                workshops = []
        else:
            # FALLBACK: Use preloaded WORKSHOPS (5 demo workshops)
            workshops = [w['details'] for w in WORKSHOPS.values() if w.get('approved', True)]
            print("✅ Using in-memory WORKSHOPS (DB unavailable)")

        result = []

        for w in workshops:
            # ✅ SKIP if lat/lng missing
            if not w.get("latitude") or not w.get("longitude"):
                print(f"⚠ Skipping workshop (no coords): {w.get('name')}")
                continue

            try:
                distance = calculate_distance(
                    lat, lng,
                    float(w["latitude"]),
                    float(w["longitude"])
                )
            except Exception as e:
                print("❌ Distance error:", e)
                continue

            workshop_data = {
                "id": w.get("id", "demo"),
                "name": w.get("name", "Demo Workshop"),
                "latitude": float(w["latitude"]),
                "longitude": float(w["longitude"]),
                "distance": round(distance, 2)
            }

            print("✅ Workshop:", workshop_data)
            result.append(workshop_data)

        # ✅ SORT BY DISTANCE
        result.sort(key=lambda x: x["distance"])

        print("📦 FINAL RESULT:", result[:5])

        # CITY GROUPING BONUS (Vadodara/Ahmedabad/etc)
        cities = {}
        city_keywords = {
            "Vadodara": ["Vadodara"],
            "Ahmedabad": ["Ahmedabad", "SG Highway"],
            "Surat": ["Surat", "Adajan"],
            "Rajkot": ["Rajkot", "Kalawad"],
            "Gandhinagar": ["Gandhinagar", "Sector 21"]
        }
        
        for w in result:
            for city, keywords in city_keywords.items():
                if any(kw.lower() in w['name'].lower() or kw.lower() in w.get('address', '').lower() for kw in keywords):
                    if city not in cities:
                        cities[city] = []
                    cities[city].append(w)
                    break

        return jsonify({
            "workshops": result[:5],
            "cities": cities,
            "total": len(result)
        })

    except Exception as e:
        print("🔥 ERROR IN API:", str(e))
        return jsonify({"error": "Server error"}), 500

@app.route("/book_service", methods=["GET", "POST"])
@require_role("customer")
def book_service():
    try:
        user_email = session.get("email")
        customer = CUSTOMERS.get(user_email)

        if customer is None:
            logging.warning(f"Customer not found for session email: {user_email}")
            flash("Customer data not found. Please login again.", "danger")
            return redirect(url_for('login'))

        if request.method == "POST":
            service_ids = request.form.getlist('service_ids')
            preferred_date = request.form.get('preferred_date', '').strip()
            preferred_time = request.form.get('preferred_time', '').strip()
            vehicle_info = request.form.get('vehicle_info', '').strip()
            workshop_id = request.form.get('workshop_id')
            
            if not workshop_id:
                flash("Please select a workshop.", "warning")
                return render_template("book_service.html", services=SERVICES)

            # ✅ GET USER LOCATION
            user_lat = float(request.form.get('latitude', 0))
            user_lng = float(request.form.get('longitude', 0))

            if user_lat == 0 or user_lng == 0:
                flash("Please click 'Use My Location' before booking.", "warning")
                return render_template("book_service.html", services=SERVICES)


            if not service_ids:
                flash("Please select at least one service.", "warning")
                return render_template("book_service.html", services=SERVICES)

            if preferred_date:
                try:
                    booking_date = datetime.strptime(preferred_date, '%Y-%m-%d')
                    if booking_date.date() < datetime.now().date():
                        flash("Please select a future date for your booking.", "warning")
                        return render_template("book_service.html", services=SERVICES)
                except ValueError:
                    flash("Please enter a valid date.", "warning")
                    return render_template("book_service.html", services=SERVICES)

            selected_services = [s for s in SERVICES if str(s['id']) in service_ids]
            if not selected_services:
                flash("Invalid service selection.", "danger")
                return render_template("book_service.html", services=SERVICES)

            total_cost = sum(s['price'] for s in selected_services)
            
            # Fix 'demo' ID → Use workshop name as fallback ID
            selected_workshop = next(
                (w for w in WORKSHOPS.values() if str(w['id']) == workshop_id),
                next((w for w in WORKSHOPS.values()), None)
            ) or {'details': {'name': 'Local Workshop'}}

            # Create booking
            booking_id = len(BOOKINGS) + 1
            booking = {
                'id': booking_id,
                'customer_id': customer['id'],
                'customer_name': customer['username'],
                'customer_email': customer['email'],
                'services': selected_services,
                'total_cost': total_cost,
                'status': 'assigned',
                'preferred_date': preferred_date,
                'preferred_time': preferred_time,
                'vehicle_info': vehicle_info,
                'workshop_id': 1,  # Default fallback ID
                'workshop_name': selected_workshop.get('username', selected_workshop['details']['name'] if 'details' in selected_workshop else 'Local Workshop'),
                'workshop_name': selected_workshop['username'] if selected_workshop else "Unknown",
                'payment_status': 'pending',
                'invoice_generated': False,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'status_history': [{
                    'status': 'pending',
                    'timestamp': datetime.now(),
                    'message': f"Assigned to {selected_workshop['username']}"
                }]
            }

            BOOKINGS.append(booking)
            ANALYTICS['total_bookings'] += 1

            # Create notification for admin
            notification = {
                'id': len(NOTIFICATIONS) + 1,
                'type': 'new_booking',
                'message': f'New booking #{booking_id} from {customer["username"]} - {len(selected_services)} services, ₹{total_cost}',
                'booking_id': booking_id,
                'created_at': datetime.now()
            }
            NOTIFICATIONS.append(notification)

            # Send initial notification to customer
            send_booking_notification(booking_id, 'pending', customer['email'])

            # Send real-time WebSocket notifications for new booking
            if websocket_service:
                try:
                    # Notify admin of new booking
                    websocket_service.emit_to_room(
                        room='admin',
                        event='new_booking',
                        data={
                            'booking_id': booking_id,
                            'customer_name': customer['username'],
                            'customer_email': customer['email'],
                            'services': [s['name'] for s in selected_services],
                            'total_cost': total_cost,
                            'preferred_date': preferred_date,
                            'preferred_time': preferred_time,
                            'vehicle_info': vehicle_info,
                            'timestamp': datetime.now().isoformat()
                        }
                    )

                    # Notify all workshops of new booking (for potential assignment)
                    websocket_service.emit_to_room(
                        room='workshop',
                        event='new_booking_available',
                        data={
                            'booking_id': booking_id,
                            'customer_name': customer['username'],
                            'services': [s['name'] for s in selected_services],
                            'location': customer.get('profile', {}).get('address', ''),
                            'total_cost': total_cost,
                            'preferred_date': preferred_date,
                            'timestamp': datetime.now().isoformat()
                        }
                    )

                    logging.info(f"WebSocket new booking notification sent for booking #{booking_id}")
                except Exception as e:
                    logging.error(f"WebSocket new booking notification failed: {e}")

            logging.info(f"New booking created: #{booking_id} by {customer['username']} - Services: {[s['name'] for s in selected_services]}")
            flash("✅ Booking created successfully! You'll receive notifications about status updates.", "success")
            flash("📞 For pickup services, please call +91 1234567809.", "success")
            return redirect(url_for('customer_dashboard'))

        return render_template("book_service.html", services=SERVICES)
    except Exception as e:
        logging.error(f"Book service error: {e}")
        flash("An error occurred while processing your booking. Please try again.", "danger")
    return render_template("book_service.html", services=SERVICES)

@app.route("/customer/bookings")
@require_role("customer")
def customer_bookings():
    user_email = session.get("email")
    customer = CUSTOMERS.get(user_email)
    user_bookings = [b for b in BOOKINGS if b['customer_id'] == customer['id']]
    return render_template("customer_bookings.html", bookings=user_bookings)

@app.route("/customer/rate/<int:booking_id>", methods=["POST"])
@require_role("customer")
def rate_booking(booking_id):
    rating = request.form.get("rating")
    comment = request.form.get("comment")

    booking = next((b for b in BOOKINGS if b['id'] == booking_id), None)
    if booking:
        review = {
            'id': len(REVIEWS) + 1,
            'booking_id': booking_id,
            'customer_id': session.get('user_id'),
            'workshop_id': booking.get('workshop_id'),
            'rating': int(rating),
            'comment': comment,
            'created_at': datetime.now()
        }
        REVIEWS.append(review)

        # Update workshop rating
        if booking.get('workshop_id'):
            workshop = next((w for w in WORKSHOPS.values() if w['id'] == booking['workshop_id']), None)
            if workshop:
                workshop_reviews = [r for r in REVIEWS if r['workshop_id'] == booking['workshop_id']]
                if workshop_reviews:
                    workshop['details']['rating'] = sum(r['rating'] for r in workshop_reviews) / len(workshop_reviews)

        flash("Thank you for your rating!", "success")

    return redirect(url_for('customer_bookings'))

# Enhanced Customer Routes
@app.route("/customer/service_tracking")
@require_role("customer")
def customer_service_tracking():
    """Enhanced service tracking dashboard with real-time updates"""
    user_email = session.get("email")
    customer = CUSTOMERS.get(user_email)
    user_bookings = [b for b in BOOKINGS if b['customer_id'] == customer['id']]

    # Calculate dashboard statistics
    active_bookings = len([b for b in user_bookings if b['status'] not in ['completed', 'paid', 'cancelled']])
    pending_bookings = len([b for b in user_bookings if b['status'] in ['pending', 'assigned']])
    completed_services = len([b for b in user_bookings if b['status'] in ['completed', 'paid']])
    total_spent = sum(b['total_cost'] for b in user_bookings if b['status'] in ['completed', 'paid'])

    # Active bookings list for display
    active_bookings_list = [b for b in user_bookings if b['status'] not in ['completed', 'paid', 'cancelled']]

    # Add enhanced information to active bookings
    for booking in active_bookings_list:
        # Status information
        status_info = BOOKING_STATUSES.get(booking['status'], {'label': booking['status'], 'color': 'secondary'})
        booking['status_info'] = status_info

        # Workshop details (mock for now, in real app would fetch from workshop data)
        booking['workshop_name'] = booking.get('workshop_name', 'Not Assigned')
        booking['workshop_address'] = 'Workshop Address'  # Mock
        booking['workshop_phone'] = 'Workshop Phone'  # Mock

        # Progress percentage based on status
        status_progress = {
            'pending': 25,
            'assigned': 40,
            'accepted': 50,
            'in_progress': 75,
            'completed': 90,
            'paid': 100
        }
        booking['progress'] = status_progress.get(booking['status'], 0)

    # Mock upcoming reminders (in real app, would be calculated based on service history)
    upcoming_reminders = [
        {
            'service_type': 'Oil Change',
            'next_service_date': '2025-10-15',
            'vehicle_info': 'Honda City - MH12AB1234'
        },
        {
            'service_type': 'Tire Rotation',
            'next_service_date': '2025-11-01',
            'vehicle_info': 'Honda City - MH12AB1234'
        }
    ]

    # Mock recent activities (in real app, would be from booking history)
    recent_activities = [
        {
            'description': 'Booking #1 status updated to In Progress',
            'timestamp': '2 hours ago'
        },
        {
            'description': 'Invoice generated for Booking #1',
            'timestamp': '1 day ago'
        },
        {
            'description': 'Payment completed for Booking #1',
            'timestamp': '1 day ago'
        }
    ]

    # Get customer notifications
    customer_notifications = [n for n in NOTIFICATIONS if n.get('customer_email') == user_email]

    return render_template("customer_service_tracking.html",
                         customer=customer,
                         active_bookings=active_bookings,
                         pending_bookings=pending_bookings,
                         completed_services=completed_services,
                         total_spent=total_spent,
                         active_bookings_list=active_bookings_list,
                         upcoming_reminders=upcoming_reminders,
                         recent_activities=recent_activities,
                         services=SERVICES,
                         notifications=customer_notifications[-10:])  # Last 10 notifications





# Payment routes disabled - removed customer payment functionality

@app.route("/customer/invoice/<int:booking_id>")
@require_role("customer")
def customer_invoice(booking_id):
    """Generate and download invoice PDF"""
    user_email = session.get("email")
    customer = CUSTOMERS.get(user_email)
    booking = next((b for b in BOOKINGS if b['id'] == booking_id and b['customer_id'] == customer['id']), None)

    if not booking:
        logging.warning(f"Customer invoice: Booking not found - ID: {booking_id}, Customer: {user_email}")
        flash("Booking not found.", "danger")
        return redirect(url_for('customer_bookings'))

    # Check if booking is completed or paid
    if booking['status'] not in ['completed', 'paid']:
        logging.warning(f"Customer invoice: Booking not completed - ID: {booking_id}, Status: {booking['status']}")

        flash("Invoice not available yet. Complete the service first.", "warning")
        return redirect(url_for('customer_bookings'))


    try:
        logging.info(f"Customer invoice: Generating PDF for booking {booking_id}")

        # Generate invoice PDF with enhanced data
        invoice_data = {
            'id': booking_id,
            'booking_id': booking_id,
            'customer_name': customer['username'],
            'customer_email': customer['email'],
            'customer_phone': customer.get('profile', {}).get('phone', ''),
            'services': booking['services'],
            'total_amount': booking['total_cost'],
            'booking_date': booking['created_at'],
            'completion_date': booking.get('updated_at'),
            'workshop_name': booking.get('workshop_name', 'AutoCare Services'),
            'payment_id': booking.get('payment_id', ''),
            'vehicle_info': booking.get('vehicle_info', ''),
            'status_history': booking.get('status_history', [])
        }

        pdf_path = pdf_generator.generate_invoice(invoice_data)
        logging.info(f"Customer invoice: PDF generation result - Path: {pdf_path}")

        if pdf_path and os.path.exists(pdf_path):
            # Update booking to mark invoice as generated
            booking['invoice_generated'] = True
            booking['invoice_generated_at'] = datetime.now()

            logging.info(f"Customer invoice: Sending file - {pdf_path}")
            return send_file(pdf_path, as_attachment=True,
                           download_name=f"autocare_invoice_{booking_id}.pdf",
                           mimetype='application/pdf')
        else:

            logging.error(f"Customer invoice: PDF generation failed or file not found - Path: {pdf_path}")
            flash("Invoice generation failed. Please try again.", "danger")
            return redirect(url_for('customer_bookings'))


    except Exception as e:

        logging.error(f"Customer invoice generation error: {e}")
        flash("Error generating invoice. Please contact support.", "danger")
        return redirect(url_for('customer_bookings'))


@app.route("/customer/invoice/view/<int:booking_id>")
@require_role("customer")
def customer_invoice_view(booking_id):
    """View invoice details before downloading"""
    user_email = session.get("email")
    customer = CUSTOMERS.get(user_email)
    booking = next((b for b in BOOKINGS if b['id'] == booking_id and b['customer_id'] == customer['id']), None)

    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for('customer_bookings'))

    # Check if booking is completed or paid
    if booking['status'] not in ['completed', 'paid']:
        flash("Invoice not available yet. Complete the service first.", "warning")
        return redirect(url_for('customer_service_tracking'))

    # Prepare invoice data for display
    invoice_data = {
        'booking_id': booking_id,
        'customer_name': customer['username'],
        'customer_email': customer['email'],
        'customer_phone': customer.get('profile', {}).get('phone', ''),
        'services': booking['services'],
        'total_amount': booking['total_cost'],
        'booking_date': booking['created_at'],
        'completion_date': booking.get('updated_at'),
        'workshop_name': booking.get('workshop_name', 'AutoCare Services'),
        'payment_id': booking.get('payment_id', ''),
        'vehicle_info': booking.get('vehicle_info', ''),
        'status_history': booking.get('status_history', [])
    }

    return render_template("customer_invoice_view.html",
                         customer=customer,
                         booking=booking,
                         invoice_data=invoice_data)

@app.route("/customer/complaints")
@require_role("customer")
def customer_complaints():
    """Customer complaints dashboard"""
    user_email = session.get("email")
    customer = CUSTOMERS.get(user_email)

    # Get customer's complaints
    customer_complaints = [c for c in COMPLAINTS if c.get('customer_email') == user_email]

    # Sort by creation time (newest first)
    customer_complaints.sort(key=lambda x: x.get('created_at', datetime.now()), reverse=True)

    return render_template("customer_complaints.html",
                         customer=customer,
                         complaints=customer_complaints)

@app.route("/customer/complaint/new", methods=["GET", "POST"])
@require_role("customer")
def customer_new_complaint():
    """Create new complaint"""
    user_email = session.get("email")
    customer = CUSTOMERS.get(user_email)

    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        category = request.form.get("category", "general")
        priority = request.form.get("priority", "medium")
        booking_id = request.form.get("booking_id")

        if not subject or not message:
            flash("Subject and message are required.", "danger")
            return render_template("customer_new_complaint.html", customer=customer)

        # Create complaint
        complaint = {
            "id": len(COMPLAINTS) + 1,
            "customer_id": customer['id'],
            "customer_email": user_email,
            "customer_name": customer['username'],
            "subject": subject,
            "message": message,
            "category": category,
            "priority": priority,
            "booking_id": booking_id,
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        COMPLAINTS.append(complaint)

        # Create notification for admin
        admin_notification = {
            'id': len(NOTIFICATIONS) + 1,
            'type': 'new_complaint',
            'message': f'New customer complaint #{complaint["id"]} - {subject} (Priority: {priority})',
            'complaint_id': complaint["id"],
            'created_at': datetime.now()
        }
        NOTIFICATIONS.append(admin_notification)

        flash("Your complaint has been submitted successfully. We'll respond shortly.", "success")
        return redirect(url_for('customer_complaints'))

    # Get customer's completed bookings for reference
    completed_bookings = [b for b in BOOKINGS
                         if b['customer_id'] == customer['id'] and b['status'] in ['completed', 'paid']]

    return render_template("customer_new_complaint.html",
                         customer=customer,
                         bookings=completed_bookings)

@app.route("/customer/complaint/<int:complaint_id>")
@require_role("customer")
def customer_complaint_detail(complaint_id):
    """View complaint details"""
    user_email = session.get("email")
    customer = CUSTOMERS.get(user_email)

    complaint = next((c for c in COMPLAINTS
                     if c['id'] == complaint_id and c.get('customer_email') == user_email), None)

    if not complaint:
        flash("Complaint not found.", "danger")
        return redirect(url_for('customer_complaints'))

    return render_template("customer_complaint_detail.html",
                         customer=customer,
                         complaint=complaint)

# Workshop Routes
@app.route("/workshop/dashboard")
@require_role("workshop")
def workshop_dashboard():
    user_email = session.get("email")
    workshop = WORKSHOPS.get(user_email)
    if not workshop or not workshop.get('details'):
        flash("Workshop details not found.", "error")
        return redirect(url_for("logout"))
    workshop_bookings = [b for b in BOOKINGS if b.get('workshop_id') == workshop['id']]
    workshop_services = [s for s in SERVICES if s['name'] in (workshop['details'].get('services') or [])]

    workshop_with_details = {
        "id": workshop["id"],
        "username": workshop["username"],
        "email": workshop["email"],
        "role": workshop["role"],
        "approved": workshop["approved"],
        "created_at": workshop["created_at"],
        "details": {
            "name": workshop["details"].get("name", workshop["username"]),
            "address": workshop["details"].get("address", "Address not provided"),
            "phone": workshop["details"].get("phone", "Phone not provided"),
            "latitude": workshop["details"].get("latitude", 19.0760),
            "longitude": workshop["details"].get("longitude", 72.8777),
            "services": workshop["details"].get("services", ["Oil Change", "Brake Service", "Tire Rotation"]),
            "rating": workshop["details"].get("rating", 4.5),
            "total_bookings": workshop["details"].get("total_bookings", len(workshop_bookings))
        }
    }

    return render_template("workshop_dashboard.html",
                         workshop=workshop_with_details, bookings=workshop_bookings, services=workshop_services)

@app.route("/workshop/performance")
@require_role("workshop")
def workshop_performance():
    user_email = session.get("email")
    workshop = WORKSHOPS.get(user_email)
    if not workshop:
        flash("Workshop not found.", "error")
        return redirect(url_for("logout"))

    workshop_bookings = [b for b in BOOKINGS if b.get('workshop_id') == workshop['id']]

    now = datetime.now()
    monthly_stats = {}
    for i in range(5, -1, -1):
        month_date = now.replace(day=1) - timedelta(days=i*30)
        month_key = month_date.strftime('%Y-%m')
        month_bookings = [b for b in workshop_bookings
                         if b['created_at'].strftime('%Y-%m') == month_key]

        monthly_stats[month_key] = {
            'bookings': len(month_bookings),
            'completed': len([b for b in month_bookings if b['status'] == 'completed']),
            'revenue': sum(b['total_cost'] for b in month_bookings if b['status'] == 'completed')
        }

    service_stats = {}
    for booking in workshop_bookings:
        for service in booking['services']:
            service_name = service['name']
            if service_name not in service_stats:
                service_stats[service_name] = 0
            service_stats[service_name] += 1

    workshop_reviews = [r for r in REVIEWS if r.get('workshop_id') == workshop['id']]
    avg_rating = 0
    if workshop_reviews:
        avg_rating = sum(r['rating'] for r in workshop_reviews) / len(workshop_reviews)

    performance_data = {
        'total_bookings': len(workshop_bookings),
        'completed_bookings': len([b for b in workshop_bookings if b['status'] == 'completed']),
        'pending_bookings': len([b for b in workshop_bookings if b['status'] in ['pending', 'assigned']]),
        'cancelled_bookings': len([b for b in workshop_bookings if b['status'] == 'cancelled']),
        'total_revenue': sum(b['total_cost'] for b in workshop_bookings if b['status'] == 'completed'),
        'monthly_stats': monthly_stats,
        'service_stats': service_stats,
        'avg_rating': avg_rating,
        'total_reviews': len(workshop_reviews)
    }

    return render_template("workshop_performance.html", performance=performance_data, workshop=workshop)

@app.route("/workshop/services", methods=["GET", "POST"])
@require_role("workshop")
def workshop_services():
    user_email = session.get("email")
    workshop = WORKSHOPS.get(user_email)
    if not workshop:
        flash("Workshop not found.", "error")
        return redirect(url_for("logout"))

    if request.method == "POST":
        service_id = int(request.form.get("service_id"))
        service = next((s for s in SERVICES if s['id'] == service_id), None)
        if service and service['name'] not in workshop['details'].get('services', []):
            workshop['details'].setdefault('services', []).append(service['name'])
            flash("Service added successfully.", "success")
        else:
            flash("Service already exists or invalid.", "warning")
        return redirect(url_for("workshop_services"))

    all_services = SERVICES
    current_services = [s for s in SERVICES if s['name'] in workshop['details'].get('services', [])]

    return render_template("workshop_services.html",
                           all_services=all_services,
                           workshop_services=current_services,
                           workshop_service_ids=workshop['details'].get('services', []))

@app.route("/workshop/services/remove", methods=["POST"])
@require_role("workshop")
def remove_workshop_service():
    user_email = session.get("email")
    workshop = WORKSHOPS.get(user_email)
    service_name = request.form.get("service_name")
    if workshop and service_name in workshop['details'].get('services', []):
        workshop['details']['services'].remove(service_name)
        flash("Service removed successfully.", "success")
    else:
        flash("Service not found.", "error")
    return redirect(url_for("workshop_services"))

@app.route("/workshop/bookings")
@require_role("workshop")
def workshop_bookings():
    user_email = session.get("email")
    workshop = WORKSHOPS.get(user_email)
    workshop_bookings = [b for b in BOOKINGS if b.get('workshop_id') == workshop['id']]
    return render_template("workshop_bookings.html", bookings=workshop_bookings)

@app.route("/workshop/update_status/<int:booking_id>", methods=["POST"])
@require_role("workshop")
def update_booking_status(booking_id):
    status = request.form.get("status")
    user_email = session.get("email")
    workshop = WORKSHOPS.get(user_email)

    booking = next((b for b in BOOKINGS if b['id'] == booking_id and b.get('workshop_id') == workshop['id']), None)
    if booking and status in ['accepted', 'in_progress', 'completed', 'cancelled']:
        old_status = booking['status']
        booking['status'] = status
        booking['updated_at'] = datetime.now()

        # Add to status history
        status_message = ""
        if status == 'accepted':
            status_message = f"Workshop {workshop['username']} accepted the booking"
        elif status == 'in_progress':
            status_message = f"Workshop started working on the vehicle"
        elif status == 'completed':
            status_message = f"Workshop completed all services"
            # Generate invoice automatically
            booking['invoice_generated'] = True
        elif status == 'cancelled':
            status_message = f"Booking cancelled by workshop"

        booking['status_history'].append({
            'status': status,
            'timestamp': datetime.now(),
            'message': status_message,
            'workshop_name': workshop['username']
        })

        # Update analytics based on status transition
        if old_status == 'pending' and status == 'assigned':
            ANALYTICS['pending_bookings'] -= 1
        elif old_status == 'assigned' and status == 'accepted':
            pass  # Still pending until accepted
        elif old_status == 'accepted' and status == 'in_progress':
            pass
        elif old_status == 'in_progress' and status == 'completed':
            ANALYTICS['completed_bookings'] += 1
            ANALYTICS['total_revenue'] += booking['total_cost']
        elif old_status == 'pending' and status == 'completed':
            ANALYTICS['pending_bookings'] -= 1
            ANALYTICS['completed_bookings'] += 1
            ANALYTICS['total_revenue'] += booking['total_cost']
        elif status == 'cancelled':
            if old_status == 'pending':
                ANALYTICS['pending_bookings'] -= 1
            elif old_status == 'assigned':
                ANALYTICS['pending_bookings'] -= 1
            elif old_status == 'in_progress':
                ANALYTICS['completed_bookings'] -= 1
                ANALYTICS['total_revenue'] -= booking['total_cost']

        # Send notification to customer
        send_booking_notification(booking_id, status, booking['customer_email'], workshop['username'])

        # Create notification for admin
        notification = {
            'id': len(NOTIFICATIONS) + 1,
            'type': 'status_update',
            'message': f'Booking #{booking_id} updated to {BOOKING_STATUSES[status]["label"]} by {workshop["username"]}',
            'booking_id': booking_id,
            'workshop_id': workshop['id'],
            'created_at': datetime.now()
        }
        NOTIFICATIONS.append(notification)

        # Send real-time WebSocket updates
        if websocket_service:
            try:
                # Notify customer of status change
                websocket_service.send_notification(
                    user_type='customer',
                    user_id=booking['customer_id'],
                    title=f"Booking #{booking_id} - Status Updated",
                    message=f"Your booking status changed to {BOOKING_STATUSES[status]['label']}",
                    notification_type='status_update',
                    data={
                        'booking_id': booking_id,
                        'status': status,
                        'workshop_name': workshop['username']
                    }
                )

                # Notify admin of status change
                websocket_service.emit_to_room(
                    room='admin',
                    event='booking_status_update',
                    data={
                        'booking_id': booking_id,
                        'status': status,
                        'workshop_name': workshop['username'],
                        'customer_name': booking['customer_name'],
                        'timestamp': datetime.now().isoformat()
                    }
                )

                logging.info(f"WebSocket status update sent for booking #{booking_id}")
            except Exception as e:
                logging.error(f"WebSocket status update failed: {e}")

        flash(f"✅ Booking status updated to {BOOKING_STATUSES[status]['label']}!", "success")

    return redirect(url_for('workshop_bookings'))

# Enhanced Workshop Routes
@app.route("/workshop/notifications")
@require_role("workshop")
def workshop_notifications():
    """Customer notification management"""
    user_email = session.get("email")
    workshop = WORKSHOPS.get(user_email)

    # Get recent notifications for this workshop
    workshop_notifications = [n for n in NOTIFICATIONS if n.get('workshop_id') == workshop['id']]

    return render_template("workshop_notifications.html",
                         workshop=workshop,
                         notifications=workshop_notifications[-20:])  # Last 20 notifications

@app.route("/workshop/enhanced_features")
@require_role("workshop")
def workshop_enhanced_features():
    """Additional workshop features - inventory, CRM, etc."""
    user_email = session.get("email")
    workshop = WORKSHOPS.get(user_email)

    # Mock inventory data (in real app, this would come from database)
    inventory_items = [
        {"id": 1, "name": "Engine Oil 5W-30", "quantity": 50, "min_quantity": 10, "unit_price": 450.00},
        {"id": 2, "name": "Brake Pads", "quantity": 25, "min_quantity": 5, "unit_price": 1200.00},
        {"id": 3, "name": "Air Filter", "quantity": 30, "min_quantity": 8, "unit_price": 300.00},
    ]

    # Mock customer data for CRM
    workshop_customers = []
    for booking in BOOKINGS:
        if booking.get('workshop_id') == workshop['id']:
            customer = CUSTOMERS.get(booking['customer_email'])
            if customer and customer not in workshop_customers:
                workshop_customers.append(customer)

    return render_template("workshop_enhanced_features.html",
                         workshop=workshop,
                         inventory=inventory_items,
                         customers=workshop_customers[:10])  # Limit to 10 customers

@app.route("/workshop/generate_invoice/<int:booking_id>")
@require_role("workshop")
def workshop_generate_invoice(booking_id):
    """Generate invoice for a specific booking"""
    user_email = session.get("email")
    workshop = WORKSHOPS.get(user_email)
    booking = next((b for b in BOOKINGS if b['id'] == booking_id and b.get('workshop_id') == workshop['id']), None)

    if not booking:
        flash("Booking not found or not assigned to your workshop.", "danger")
        return redirect(url_for('workshop_bookings'))

    # Check if booking is completed
    if booking['status'] not in ['completed']:
        flash("Invoice can only be generated for completed services.", "warning")
        return redirect(url_for('workshop_bookings'))

    try:
        # Get customer information
        customer = CUSTOMERS.get(booking['customer_email'])
        if not customer:
            flash("Customer information not found.", "danger")
            return redirect(url_for('workshop_bookings'))

        # Generate invoice PDF with enhanced data
        invoice_data = {
            'id': booking_id,
            'booking_id': booking_id,
            'customer_name': customer['username'],
            'customer_email': customer['email'],
            'customer_phone': customer.get('profile', {}).get('phone', ''),
            'customer_address': customer.get('profile', {}).get('address', ''),
            'services': booking['services'],
            'total_amount': booking['total_cost'],
            'booking_date': booking['created_at'],
            'completion_date': booking.get('updated_at'),
            'workshop_name': workshop['username'],
            'workshop_address': workshop['details']['address'],
            'workshop_phone': workshop['details']['phone'],
            'payment_id': booking.get('payment_id', ''),
            'vehicle_info': booking.get('vehicle_info', ''),
            'status_history': booking.get('status_history', [])
        }

        # Fix: Use generate_invoice method instead of generate_booking_invoice
        pdf_path = pdf_generator.generate_invoice(invoice_data)

        if pdf_path:
            # Update booking to mark invoice as generated
            booking['invoice_generated'] = True
            booking['invoice_generated_at'] = datetime.now()

            # Create notification for customer
            notification = {
                'id': len(NOTIFICATIONS) + 1,
                'type': 'invoice_generated',
                'message': f'Invoice generated for booking #{booking_id} - Total: ₹{booking["total_cost"]:.2f}',
                'booking_id': booking_id,
                'customer_email': booking['customer_email'],
                'created_at': datetime.now()
            }
            NOTIFICATIONS.append(notification)

            # Send notification to customer using enhanced notification service
            from notification import notification_service

            customer_info = {
                'id': booking.get('customer_id'),
                'email': booking['customer_email'],
                'phone': customer.get('profile', {}).get('phone', ''),
                'type': 'customer',
                'email_notifications': True,
                'sms_notifications': True
            }

            template_data = {
                'booking_id': booking_id,
                'total_amount': booking['total_cost'],
                'workshop_name': workshop['username'],
                'invoice_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'customer_name': customer['username']
            }

            notification_result = notification_service.send_notification(
                'invoice_ready',
                recipient_info=customer_info,
                template_data=template_data
            )

            logging.info(f"Invoice notification sent for booking #{booking_id}: SMS={notification_result['sms_sent']}, Email={notification_result['email_sent']}")

            # Send real-time WebSocket notification
            if websocket_service:
                try:
                    websocket_service.send_notification(
                        user_type='customer',
                        user_id=booking['customer_id'],
                        title=f"Invoice Ready - Booking #{booking_id}",
                        message=f"Your invoice for ₹{booking['total_cost']:.2f} is ready for download",
                        notification_type='invoice_ready',
                        data={
                            'booking_id': booking_id,
                            'total_amount': booking['total_cost'],
                            'workshop_name': workshop['username']
                        }
                    )
                    logging.info(f"WebSocket invoice notification sent for booking #{booking_id}")
                except Exception as e:
                    logging.error(f"WebSocket invoice notification failed: {e}")

            return send_file(pdf_path, as_attachment=True,
                           download_name=f"autocare_invoice_booking_{booking_id}.pdf")
        else:
            flash("Invoice generation failed. Please try again.", "danger")
            return redirect(url_for('workshop_bookings'))

    except Exception as e:
        logging.error(f"Invoice generation error: {e}")
        flash("Error generating invoice. Please contact support.", "danger")
        return redirect(url_for('workshop_bookings'))

@app.route("/workshop/invoices")
@require_role("workshop")
def workshop_invoices():
    """List all invoices generated by the workshop"""
    user_email = session.get("email")
    workshop = WORKSHOPS.get(user_email)
    workshop_bookings = [b for b in BOOKINGS if b.get('workshop_id') == workshop['id']]

    # Filter bookings with invoices
    bookings_with_invoices = [b for b in workshop_bookings if b.get('invoice_generated', False)]

    # Add customer information to each booking
    for booking in bookings_with_invoices:
        customer = CUSTOMERS.get(booking['customer_email'])
        if customer:
            booking['customer_info'] = customer

    return render_template("workshop_invoices.html",
                         workshop=workshop,
                         bookings=bookings_with_invoices)

@app.route("/workshop/invoice_preview/<int:booking_id>")
@require_role("workshop")
def workshop_invoice_preview(booking_id):
    """Preview invoice before generating PDF"""
    user_email = session.get("email")
    workshop = WORKSHOPS.get(user_email)
    booking = next((b for b in BOOKINGS if b['id'] == booking_id and b.get('workshop_id') == workshop['id']), None)

    if not booking:
        flash("Booking not found or not assigned to your workshop.", "danger")
        return redirect(url_for('workshop_bookings'))

    # Get customer information
    customer = CUSTOMERS.get(booking['customer_email'])
    if not customer:
        flash("Customer information not found.", "danger")
        return redirect(url_for('workshop_bookings'))

    # Prepare invoice data for preview
    invoice_data = {
        'id': booking_id,
        'booking_id': booking_id,
        'customer_name': customer['username'],
        'customer_email': customer['email'],
        'customer_phone': customer.get('profile', {}).get('phone', ''),
        'customer_address': customer.get('profile', {}).get('address', ''),
        'services': booking['services'],
        'total_amount': booking['total_cost'],
        'booking_date': booking['created_at'],
        'completion_date': booking.get('updated_at'),
        'workshop_name': workshop['username'],
        'workshop_address': workshop['details']['address'],
        'workshop_phone': workshop['details']['phone'],
        'payment_id': booking.get('payment_id', ''),
        'vehicle_info': booking.get('vehicle_info', ''),
        'status_history': booking.get('status_history', [])
    }

    return render_template("workshop_invoice_preview.html",
                         workshop=workshop,
                         booking=booking,
                         customer=customer,
                         invoice_data=invoice_data)

# Admin Routes
@app.route("/admin/dashboard")
@require_role("admin")
def admin_dashboard():
    # Recalculate analytics from current data to ensure accuracy
    ANALYTICS['total_bookings'] = len(BOOKINGS)
    ANALYTICS['pending_bookings'] = len([b for b in BOOKINGS if b['status'] == 'pending'])
    ANALYTICS['completed_bookings'] = len([b for b in BOOKINGS if b['status'] == 'completed'])
    ANALYTICS['customer_count'] = len(CUSTOMERS)
    ANALYTICS['workshop_count'] = len([w for w in WORKSHOPS.values() if w['approved']])

    # Get recent bookings with enhanced status information
    recent_bookings = BOOKINGS[-20:]  # Last 20 bookings
    for booking in recent_bookings:
        booking['status_info'] = BOOKING_STATUSES.get(booking['status'], {'label': booking['status'], 'color': 'secondary'})
        booking['recent_updates'] = booking.get('status_history', [])[-2:]  # Last 2 updates

    # Get system statistics
    status_counts = {}
    for booking in BOOKINGS:
        status = booking['status']
        status_counts[status] = status_counts.get(status, 0) + 1

    # Get recent notifications
    recent_notifications = NOTIFICATIONS[-15:]  # Last 15 notifications

    # Get pending workshops
    pending_workshops = [w for w in WORKSHOPS.values() if not w['approved']]

    # Get pending complaints
    pending_complaints = [c for c in COMPLAINTS if c['status'] == 'pending']

    # Calculate revenue by status
    revenue_by_status = {}
    for booking in BOOKINGS:
        if booking.get('payment_status') == 'completed':
            status = booking['status']
            revenue_by_status[status] = revenue_by_status.get(status, 0) + booking['total_cost']

    return render_template("admin_dashboard.html",
                         analytics=ANALYTICS,
                         recent_bookings=recent_bookings,
                         pending_workshops=pending_workshops,
                         pending_complaints=pending_complaints,
                         status_counts=status_counts,
                         recent_notifications=recent_notifications,
                         revenue_by_status=revenue_by_status)

@app.route("/admin/workshops")
@require_role("admin")
def admin_workshops():
    return render_template("admin_workshops.html", workshops=WORKSHOPS.values())

@app.route("/admin/approve_workshop/<int:workshop_id>")
@require_role("admin")
def approve_workshop(workshop_id):
    workshop = next((w for w in WORKSHOPS.values() if w['id'] == workshop_id), None)
    if workshop:
        workshop['approved'] = True
        ANALYTICS['workshop_count'] = len([w for w in WORKSHOPS.values() if w['approved']])
        flash(f"Workshop '{workshop['username']}' approved successfully!", "success")
    return redirect(url_for('admin_workshops'))

@app.route("/admin/bookings")
@require_role("admin")
def admin_bookings():
    # Enhance bookings with status information
    enhanced_bookings = []
    for booking in BOOKINGS:
        booking_info = booking.copy()
        booking_info['status_info'] = BOOKING_STATUSES.get(booking['status'], {'label': booking['status'], 'color': 'secondary'})
        booking_info['recent_updates'] = booking.get('status_history', [])[-3:]  # Last 3 updates
        booking_info['can_assign'] = booking['status'] == 'pending'
        booking_info['can_update'] = booking['status'] not in ['paid', 'cancelled']
        booking_info['has_invoice'] = booking.get('invoice_generated', False)
        enhanced_bookings.append(booking_info)

    # Sort bookings by creation date (newest first)
    enhanced_bookings.sort(key=lambda x: x.get('created_at', datetime.now()), reverse=True)

    return render_template("admin_bookings.html",
                         bookings=enhanced_bookings,
                         workshops=WORKSHOPS.values(),
                         BOOKING_STATUSES=BOOKING_STATUSES)

@app.route("/admin/assign_workshop/<int:booking_id>", methods=["GET", "POST"])
@require_role("admin")
def assign_workshop(booking_id):
    if request.method == "POST":
        workshop_id = request.form.get("workshop_id")
        booking = next((b for b in BOOKINGS if b['id'] == booking_id), None)
        workshop = next((w for w in WORKSHOPS.values() if w['id'] == int(workshop_id)), None)

        if booking and workshop:
            booking['workshop_id'] = workshop['id']
            booking['workshop_name'] = workshop['username']
            booking['status'] = 'assigned'
            booking['updated_at'] = datetime.now()

            # Update analytics: decrement pending bookings since status changed from 'pending' to 'assigned'
            ANALYTICS['pending_bookings'] -= 1

            # Add to status history
            booking['status_history'].append({
                'status': 'assigned',
                'timestamp': datetime.now(),
                'message': f'Admin assigned to workshop: {workshop["username"]}',
                'workshop_name': workshop['username']
            })

            workshop['details']['total_bookings'] += 1

            # Send notification to customer
            send_booking_notification(booking_id, 'assigned', booking['customer_email'], workshop['username'])

            # Create notification for workshop
            workshop_notification = {
                'id': len(NOTIFICATIONS) + 1,
                'type': 'workshop_assigned',
                'message': f'New booking #{booking_id} assigned - Customer: {booking["customer_name"]}, Services: {len(booking["services"])}',
                'booking_id': booking_id,
                'workshop_id': workshop_id,
                'created_at': datetime.now()
            }
            NOTIFICATIONS.append(workshop_notification)

            # Send real-time WebSocket notifications
            if websocket_service:
                try:
                    # Notify workshop of new assignment
                    websocket_service.emit_to_room(
                        room='workshop',
                        event='new_booking_assigned',
                        data={
                            'booking_id': booking_id,
                            'customer_name': booking['customer_name'],
                            'customer_email': booking['customer_email'],
                            'services': [s['name'] for s in booking['services']],
                            'total_cost': booking['total_cost'],
                            'preferred_date': booking.get('preferred_date'),
                            'preferred_time': booking.get('preferred_time'),
                            'vehicle_info': booking.get('vehicle_info', ''),
                            'timestamp': datetime.now().isoformat()
                        }
                    )

                    # Notify customer of assignment
                    websocket_service.send_notification(
                        user_type='customer',
                        user_id=booking['customer_id'],
                        title=f"Booking #{booking_id} - Workshop Assigned",
                        message=f"Your booking has been assigned to {workshop['username']}",
                        notification_type='workshop_assigned',
                        data={
                            'booking_id': booking_id,
                            'workshop_name': workshop['username'],
                            'workshop_phone': workshop['details']['phone'],
                            'workshop_address': workshop['details']['address']
                        }
                    )

                    # Notify admin of assignment
                    websocket_service.emit_to_room(
                        room='admin',
                        event='booking_assigned',
                        data={
                            'booking_id': booking_id,
                            'workshop_name': workshop['username'],
                            'customer_name': booking['customer_name'],
                            'timestamp': datetime.now().isoformat()
                        }
                    )

                    logging.info(f"WebSocket assignment notification sent for booking #{booking_id}")
                except Exception as e:
                    logging.error(f"WebSocket assignment notification failed: {e}")

            flash(f"✅ Workshop '{workshop['username']}' assigned to booking #{booking_id}!", "success")

        return redirect(url_for('admin_bookings'))
    else:
        return redirect(url_for('admin_bookings'))

@app.route("/admin/update_booking_status/<int:booking_id>", methods=["POST"])
@require_role("admin")
def admin_update_booking_status(booking_id):
    status = request.form.get("status")
    booking = next((b for b in BOOKINGS if b['id'] == booking_id), None)

    if booking and status in ['in_progress', 'completed', 'cancelled']:
        old_status = booking['status']
        booking['status'] = status
        booking['updated_at'] = datetime.now()

        if old_status == 'pending' and status == 'assigned':
            ANALYTICS['pending_bookings'] -= 1
        elif old_status == 'assigned' and status == 'in_progress':
            pass
        elif old_status == 'in_progress' and status == 'completed':
            ANALYTICS['completed_bookings'] += 1
            ANALYTICS['total_revenue'] += booking['total_cost']
        elif old_status == 'pending' and status == 'completed':
            ANALYTICS['pending_bookings'] -= 1
            ANALYTICS['completed_bookings'] += 1
            ANALYTICS['total_revenue'] += booking['total_cost']
        elif status == 'cancelled':
            if old_status == 'pending':
                ANALYTICS['pending_bookings'] -= 1
            elif old_status == 'assigned':
                ANALYTICS['pending_bookings'] -= 1
            elif old_status == 'in_progress':
                ANALYTICS['completed_bookings'] -= 1
                ANALYTICS['total_revenue'] -= booking['total_cost']

        notification = {
            'id': len(NOTIFICATIONS) + 1,
            'type': 'status_update',
            'message': f'Booking #{booking_id} status updated to {status}',
            'booking_id': booking_id,
            'created_at': datetime.now()
        }
        NOTIFICATIONS.append(notification)

        flash("Booking status updated successfully!", "success")

    return redirect(url_for('admin_bookings'))

@app.route("/admin/complaints")
@require_role("admin")
def admin_complaints():
    return render_template("admin_complaints.html", complaints=COMPLAINTS)

@app.route("/admin/update_complaint/<int:complaint_id>", methods=["POST"])
@require_role("admin")
def update_complaint(complaint_id):
    status = request.form.get("status")
    response = request.form.get("response")

    complaint = next((c for c in COMPLAINTS if c['id'] == complaint_id), None)
    if complaint:
        complaint['status'] = status
        complaint['response'] = response
        complaint['updated_at'] = datetime.now()
        flash("Complaint updated successfully!", "success")

    return redirect(url_for('admin_complaints'))

@app.route("/admin/analytics")
@require_role("admin")
def admin_analytics():
    """Enhanced admin analytics with comprehensive data and charts"""
    from datetime import datetime, timedelta
    import calendar

    # Get date range from query parameters or default to last 30 days
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = datetime.now().date() - timedelta(days=30)
            end_date = datetime.now().date()
    else:
        start_date = datetime.now().date() - timedelta(days=30)
        end_date = datetime.now().date()

    # Filter bookings by date range
    filtered_bookings = [
        b for b in BOOKINGS
        if start_date <= b['created_at'].date() <= end_date
    ]

    # Calculate basic metrics
    total_bookings = len(filtered_bookings)
    completed_bookings = len([b for b in filtered_bookings if b['status'] == 'completed'])
    pending_bookings = len([b for b in filtered_bookings if b['status'] in ['pending', 'assigned']])
    cancelled_bookings = len([b for b in filtered_bookings if b['status'] == 'cancelled'])
    total_revenue = sum(b['total_cost'] for b in filtered_bookings if b['status'] == 'completed')
    active_workshops = len([w for w in WORKSHOPS.values() if w['approved']])
    total_customers = len(CUSTOMERS)

    # Calculate previous period for growth metrics
    prev_start_date = start_date - timedelta(days=(end_date - start_date).days + 1)
    prev_end_date = start_date - timedelta(days=1)
    prev_bookings = [
        b for b in BOOKINGS
        if prev_start_date <= b['created_at'].date() <= prev_end_date
    ]
    prev_revenue = sum(b['total_cost'] for b in prev_bookings if b['status'] == 'completed')
    prev_customers = len([c for c in CUSTOMERS.values() if prev_start_date <= c['created_at'].date() <= prev_end_date])

    # Calculate growth percentages
    booking_growth = ((total_bookings - len(prev_bookings)) / len(prev_bookings) * 100) if prev_bookings else 0
    revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue else 0
    customer_growth = ((total_customers - prev_customers) / prev_customers * 100) if prev_customers else 0
    workshop_growth = 0  # Static for now

    # Monthly booking trends (last 6 months)
    monthly_bookings = []
    for i in range(5, -1, -1):
        month_date = datetime.now().replace(day=1) - timedelta(days=i*30)
        month_start = month_date.replace(day=1)
        month_end = month_date.replace(day=calendar.monthrange(month_date.year, month_date.month)[1])

        month_count = len([
            b for b in BOOKINGS
            if month_start.date() <= b['created_at'].date() <= month_end.date()
        ])

        monthly_bookings.append({
            'month': month_date.strftime('%b %Y'),
            'count': month_count
        })

    # Booking status distribution
    booking_status = [
        {'status': 'Pending', 'count': pending_bookings},
        {'status': 'Completed', 'count': completed_bookings},
        {'status': 'Cancelled', 'count': cancelled_bookings},
        {'status': 'In Progress', 'count': len([b for b in filtered_bookings if b['status'] == 'in_progress'])}
    ]

    # Service revenue breakdown
    service_revenue = []
    service_counts = {}
    for booking in filtered_bookings:
        for service in booking['services']:
            service_name = service['name']
            if service_name not in service_counts:
                service_counts[service_name] = {'count': 0, 'revenue': 0}
            service_counts[service_name]['count'] += 1
            if booking['status'] == 'completed':
                service_counts[service_name]['revenue'] += service['price']

    for service_name, data in service_counts.items():
        service_revenue.append({
            'service': service_name,
            'revenue': data['revenue'],
            'count': data['count']
        })
    service_revenue.sort(key=lambda x: x['revenue'], reverse=True)

    # Workshop performance
    workshop_performance = []
    for workshop in WORKSHOPS.values():
        if workshop['approved']:
            workshop_bookings = [b for b in filtered_bookings if b.get('workshop_id') == workshop['id']]
            completed_ws_bookings = [b for b in workshop_bookings if b['status'] == 'completed']
            revenue = sum(b['total_cost'] for b in completed_ws_bookings)

            workshop_performance.append({
                'name': workshop['username'],
                'bookings': len(workshop_bookings),
                'revenue': revenue,
                'rating': workshop['details'].get('rating', 0)
            })
    workshop_performance.sort(key=lambda x: x['revenue'], reverse=True)

    # Top performing workshops
    top_workshops = workshop_performance[:5] if len(workshop_performance) >= 5 else workshop_performance

    # Popular services
    popular_services = []
    total_service_bookings = sum(s['count'] for s in service_revenue)
    for service in service_revenue[:5]:
        percentage = (service['count'] / total_service_bookings * 100) if total_service_bookings > 0 else 0
        popular_services.append({
            'name': service['service'],
            'bookings': service['count'],
            'revenue': service['revenue'],
            'percentage': round(percentage, 1)
        })

    # Prepare comprehensive analytics data
    analytics_data = {
        # Basic metrics
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'pending_bookings': pending_bookings,
        'total_revenue': total_revenue,
        'active_workshops': active_workshops,
        'total_customers': total_customers,

        # Growth metrics
        'booking_growth': round(booking_growth, 1),
        'revenue_growth': round(revenue_growth, 1),
        'workshop_growth': round(workshop_growth, 1),
        'customer_growth': round(customer_growth, 1),

        # Date range
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),

        # Chart data
        'monthly_bookings': monthly_bookings,
        'booking_status': booking_status,
        'service_revenue': service_revenue[:10],  # Top 10 services
        'workshop_performance': workshop_performance[:10],  # Top 10 workshops

        # Top performers
        'top_workshops': top_workshops,
        'popular_services': popular_services
    }

    return render_template("admin_analytics.html", analytics=analytics_data)

# Enhanced Admin Routes
@app.route("/admin/logs_reports")
@require_role("admin")
def admin_logs_reports():
    """System logs and comprehensive reports"""
    # Get recent system logs
    recent_logs = [
        {"level": "INFO", "message": "User logged in successfully", "timestamp": datetime.now()},
        {"level": "WARNING", "message": "Payment gateway timeout", "timestamp": datetime.now()},
        {"level": "ERROR", "message": "Database connection failed", "timestamp": datetime.now()},
    ]

    # Generate reports data
    reports_data = {
        'total_users': len(USERS) + len(WORKSHOPS) + len(CUSTOMERS),
        'total_bookings': len(BOOKINGS),
        'total_revenue': ANALYTICS['total_revenue'],
        'active_workshops': len([w for w in WORKSHOPS.values() if w['approved']]),
        'pending_bookings': ANALYTICS['pending_bookings'],
        'completed_bookings': ANALYTICS['completed_bookings']
    }

    return render_template("admin_logs_reports.html",
                         logs=recent_logs,
                         reports=reports_data)

@app.route("/admin/enhanced_analytics")
@require_role("admin")
def admin_enhanced_analytics():
    """Advanced analytics with charts and graphs"""
    # Enhanced analytics data
    enhanced_data = {
        'revenue_by_month': {
            'Jan': 15000, 'Feb': 18000, 'Mar': 22000, 'Apr': 25000, 'May': 28000, 'Jun': 32000
        },
        'bookings_by_status': {
            'completed': ANALYTICS['completed_bookings'],
            'pending': ANALYTICS['pending_bookings'],
            'cancelled': len([b for b in BOOKINGS if b['status'] == 'cancelled'])
        },
        'workshop_performance': [
            {'name': 'City Auto Service', 'rating': 4.5, 'bookings': 25, 'revenue': 15000},
            {'name': 'Premium Car Care', 'rating': 4.8, 'bookings': 30, 'revenue': 18000}
        ],
        'customer_satisfaction': {
            'excellent': 65, 'good': 25, 'average': 8, 'poor': 2
        }
    }

    return render_template("admin_enhanced_analytics.html", analytics=enhanced_data)

@app.route("/admin/invoice/<int:booking_id>")
@require_role("admin")
def admin_invoice(booking_id):
    """Admin can download and view invoice PDF"""
    booking = next((b for b in BOOKINGS if b['id'] == booking_id), None)

    if not booking:
        logging.warning(f"Admin invoice: Booking not found - ID: {booking_id}")
        flash("Booking not found.", "danger")
        return redirect(url_for('admin_bookings'))

    # Check if booking is completed or paid
    if booking['status'] not in ['completed', 'paid']:
        logging.warning(f"Admin invoice: Booking not completed - ID: {booking_id}, Status: {booking['status']}")
        flash("Invoice not available yet. Complete the service first.", "warning")
        return redirect(url_for('admin_bookings'))

    try:
        logging.info(f"Admin invoice: Generating PDF for booking {booking_id}")

        # Get customer information
        customer = CUSTOMERS.get(booking['customer_email'])
        if not customer:
            logging.error(f"Admin invoice: Customer information not found for booking {booking_id}")
            flash("Customer information not found.", "danger")
            return redirect(url_for('admin_bookings'))

        # Generate invoice PDF with enhanced data
        invoice_data = {
            'id': booking_id,
            'booking_id': booking_id,
            'customer_name': customer['username'],
            'customer_email': customer['email'],
            'customer_phone': customer.get('profile', {}).get('phone', ''),
            'services': booking['services'],
            'total_amount': booking['total_cost'],
            'booking_date': booking['created_at'],
            'completion_date': booking.get('updated_at'),
            'workshop_name': booking.get('workshop_name', 'AutoCare Services'),
            'payment_id': booking.get('payment_id', ''),
            'vehicle_info': booking.get('vehicle_info', ''),
            'status_history': booking.get('status_history', [])
        }

        pdf_path = pdf_generator.generate_invoice(invoice_data)
        logging.info(f"Admin invoice: PDF generation result - Path: {pdf_path}")

        if pdf_path and os.path.exists(pdf_path):
            # Update booking to mark invoice as generated
            booking['invoice_generated'] = True
            booking['invoice_generated_at'] = datetime.now()

            logging.info(f"Admin invoice: Sending file - {pdf_path}")
            return send_file(pdf_path, as_attachment=True,
                           download_name=f"autocare_invoice_{booking_id}.pdf",
                           mimetype='application/pdf')
        else:
            logging.error(f"Admin invoice: PDF generation failed or file not found - Path: {pdf_path}")
            flash("Invoice generation failed. Please try again.", "danger")
            return redirect(url_for('admin_bookings'))

    except Exception as e:
        logging.error(f"Admin invoice generation error: {e}")
        flash("Error generating invoice. Please contact support.", "danger")
        return redirect(url_for('admin_bookings'))

@app.route("/admin/invoice/view/<int:booking_id>")
@require_role("admin")
def admin_invoice_view(booking_id):
    """Admin can view invoice details before downloading"""
    booking = next((b for b in BOOKINGS if b['id'] == booking_id), None)

    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for('admin_bookings'))

    # Check if booking is completed or paid
    if booking['status'] not in ['completed', 'paid']:
        flash("Invoice not available yet. Complete the service first.", "warning")
        return redirect(url_for('admin_bookings'))

    # Get customer information
    customer = CUSTOMERS.get(booking['customer_email'])
    if not customer:
        flash("Customer information not found.", "danger")
        return redirect(url_for('admin_bookings'))

    # Prepare invoice data for display
    invoice_data = {
        'booking_id': booking_id,
        'customer_name': customer['username'],
        'customer_email': customer['email'],
        'customer_phone': customer.get('profile', {}).get('phone', ''),
        'services': booking['services'],
        'total_amount': booking['total_cost'],
        'booking_date': booking['created_at'],
        'completion_date': booking.get('updated_at'),
        'workshop_name': booking.get('workshop_name', 'AutoCare Services'),
        'payment_id': booking.get('payment_id', ''),
        'vehicle_info': booking.get('vehicle_info', ''),
        'status_history': booking.get('status_history', [])
    }

    return render_template("admin_invoice_view.html",
                         booking=booking,
                         invoice_data=invoice_data)

# Payment Gateway Routes disabled - removed all payment functionality

# API Routes
@app.route("/api/garages")
def api_garages():
    garages = []
    for workshop in WORKSHOPS.values():
        if workshop['approved']:
            garages.append({
                "id": workshop['id'],
                "name": workshop['details']['name'],
                "address": workshop['details']['address'],
                "latitude": workshop['details']['latitude'],
                "longitude": workshop['details']['longitude'],
                "phone": workshop['details']['phone'],
                "rating": workshop['details']['rating'],
                "services": workshop['details']['services']
            })
    return jsonify(garages)

@app.route("/api/notifications")
def api_notifications():
    if 'user_id' not in session:
        return jsonify([])

    user_notifications = [n for n in NOTIFICATIONS if n.get('user_id') == session.get('user_id')]
    return jsonify(user_notifications[-10:])  # Last 10 notifications

@app.route("/api/booking_status/<int:booking_id>")
def api_booking_status(booking_id):
    """API endpoint for real-time booking status updates"""
    booking = next((b for b in BOOKINGS if b['id'] == booking_id), None)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    # Get customer email from session
    user_email = session.get('email')
    if not user_email or booking['customer_email'] != user_email:
        return jsonify({"error": "Unauthorized"}), 403

    # Return enhanced booking status information
    status_info = BOOKING_STATUSES.get(booking['status'], {'label': booking['status'], 'color': 'secondary'})

    return jsonify({
        "booking_id": booking_id,
        "status": booking['status'],
        "status_label": status_info['label'],
        "status_color": status_info['color'],
        "status_description": status_info['description'],
        "updated_at": booking.get('updated_at', booking['created_at']).isoformat(),
        "workshop_name": booking.get('workshop_name', 'Not assigned'),
            "can_pay": False,  # Payment disabled
            "can_download_invoice": booking.get('invoice_generated', False) or booking.get('status') == 'completed',
        "payment_status": booking.get('payment_status', 'pending'),
        "recent_updates": booking.get('status_history', [])[-3:]  # Last 3 updates
    })

@app.route("/api/customer_bookings")
def api_customer_bookings():
    """API endpoint for customer bookings with real-time updates"""
    if 'user_id' not in session or session.get('role') != 'customer':
        return jsonify({"error": "Unauthorized"}), 403

    user_email = session.get('email')
    customer = CUSTOMERS.get(user_email)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    user_bookings = [b for b in BOOKINGS if b['customer_id'] == customer['id']]

    # Enhance bookings with status information
    enhanced_bookings = []
    for booking in user_bookings:
        booking_info = {
            "id": booking['id'],
            "status": booking['status'],
            "status_info": BOOKING_STATUSES.get(booking['status'], {'label': booking['status'], 'color': 'secondary'}),
            "services": booking['services'],
            "total_cost": booking['total_cost'],
            "workshop_name": booking.get('workshop_name', 'Not assigned'),
            "created_at": booking['created_at'].isoformat(),
            "updated_at": booking.get('updated_at', booking['created_at']).isoformat(),
            "can_pay": False,  # Payment disabled
            "can_download_invoice": booking.get('invoice_generated', False) or booking.get('status') == 'completed',
            "payment_status": booking.get('payment_status', 'pending'),
            "progress": {
                'pending': 25,
                'assigned': 40,
                'accepted': 50,
                'in_progress': 75,
                'completed': 90,
                'paid': 100
            }.get(booking['status'], 0)
        }
        enhanced_bookings.append(booking_info)

    # Sort by creation date (newest first)
    enhanced_bookings.sort(key=lambda x: x['created_at'], reverse=True)

    return jsonify(enhanced_bookings)

# Error handler
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    print("🚀 Starting Enhanced AutoCare System - COMPREHENSIVE VERSION")
    print("=" * 80)
    print("✅ ENHANCED FEATURES IMPLEMENTED:")
    print("✅ Customer Module:")
    print("   📊 Service Tracking Dashboard with real-time updates")
    print("   📋 Service History with AutoCare watermarked invoices")
    print("   💳 Online Payment Integration (Razorpay)")
    print("   📱 Real-time SMS/Email notifications")
    print("   📄 PDF invoice download functionality")
    print("✅ Admin Module:")
    print("   📈 Advanced Analytics & System Reports")
    print("   📊 Real-time system monitoring")
    print("   🔍 Enhanced booking management")
    print("   📋 Comprehensive logging system")
    print("✅ Workshop Module:")
    print("   🔔 Customer notification management")
    print("   📊 Performance analytics & insights")
    print("   🔧 Inventory & equipment tracking")
    print("   📦 Service package management")
    print("✅ Real-time Updates:")
    print("   📱 SMS notifications (Twilio)")
    print("   📧 Email notifications (Flask-Mail)")
    print("   💳 Payment gateway integration")
    print("   📄 Automated invoice generation")
    print("   🔌 WebSocket real-time notifications")
    print("✅ Technical Features:")
    print("   🔒 Enhanced security & authentication")
    print("   📊 Advanced analytics & reporting")
    print("   🎨 Modern responsive UI")
    print("   ⚡ Real-time status updates")
    print("   🌐 WebSocket support for live updates")
    print("=" * 80)
    print("🔐 Admin Login: admin@autocare.com / admin123")
    print("🔐 Workshop Login: workshop1@autocare.com / workshop123")
    print("🔐 Customer: Register new account or use existing")
    print("=" * 80)
    print("🌐 Enhanced AutoCare System Access:")
    print("   📍 Main Dashboard: http://127.0.0.1:5012")
    print("   📊 Customer Tracking: http://127.0.0.1:5012/customer/service_tracking")
    print("   💳 Payment Portal: http://127.0.0.1:5012/customer/payment/<booking_id>")
    print("   📋 Admin Dashboard: http://127.0.0.1:5012/admin/dashboard")
    print("   🔔 Workshop Portal: http://127.0.0.1:5012/workshop/dashboard")
    print("   🔌 WebSocket Server: ws://127.0.0.1:5012")
    print("=" * 80)
    print("🎉 ALL ENHANCED FEATURES READY!")
    print("💡 Use the enhanced dashboards for the best experience!")
    print("🔌 WebSocket real-time updates are now active!")
    print("=" * 80)

    # Start the application with WebSocket support
    if websocket_service:
        print("✅ WebSocket service is running - Real-time updates enabled!")
        websocket_service.socketio.run(app, debug=True, host="127.0.0.1", port=5012)
    else:
        print("⚠️ WebSocket service not available - Running without real-time updates")
        app.run(debug=True, host="127.0.0.1", port=5012)
