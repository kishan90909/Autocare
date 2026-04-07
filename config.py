"""
Enhanced AutoCare System Configuration
Includes configurations for payment gateway, SMS, email, and advanced features
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EnhancedConfig:
    # Flask Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "enhanced_autocare_secret_key_2025")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5012))

    # Database Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '1234')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'autocare')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))

    # Email Configuration (Flask-Mail)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'your-app-password')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@autocare.com')

    # SMS Configuration (MSG91)
    MSG91_AUTH_KEY = os.getenv('MSG91_AUTH_KEY', '470404Avigl1Y1jiN68d28b9aP1')
    MSG91_SENDER_ID = os.getenv('MSG91_SENDER_ID', 'AUTOCR')
    MSG91_ENABLED = os.getenv('MSG91_ENABLED', 'true').lower() == 'true'

    # Payment Gateway (Disabled)
    RAZORPAY_ENABLED = os.getenv('RAZORPAY_ENABLED', 'false').lower() == 'true'
    PAYMENT_ENABLED = os.getenv('PAYMENT_ENABLED', 'false').lower() == 'true'

    # Application Settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    INVOICE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'invoices')
    LOG_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    TEMP_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')

    # Notification Settings
    NOTIFICATION_ENABLED = os.getenv('NOTIFICATION_ENABLED', 'true').lower() == 'true'
    SMS_ENABLED = os.getenv('SMS_ENABLED', 'false').lower() == 'true'
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'true').lower() == 'true'

    # Real-time Updates
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    SOCKETIO_ENABLED = os.getenv('SOCKETIO_ENABLED', 'false').lower() == 'true'

    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

    # Invoice Settings
    INVOICE_LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'autocare_logo.png')
    INVOICE_WATERMARK_TEXT = "AutoCare Services - Official Invoice"
    INVOICE_CURRENCY = "INR"

    # Analytics Settings
    ANALYTICS_ENABLED = os.getenv('ANALYTICS_ENABLED', 'true').lower() == 'true'
    REPORT_RETENTION_DAYS = int(os.getenv('REPORT_RETENTION_DAYS', 90))

    # Security Settings
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = int(os.getenv('SESSION_LIFETIME', 3600))  # 1 hour

    # API Settings
    API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '1000/hour')
    API_ENABLED = os.getenv('API_ENABLED', 'true').lower() == 'true'

    # Create directories if they don't exist
    for folder in [UPLOAD_FOLDER, INVOICE_FOLDER, LOG_FOLDER, TEMP_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Notification Templates
    NOTIFICATION_TEMPLATES = {
        'booking_confirmed': {
            'email_subject': 'Booking Confirmed - AutoCare Services',
            'sms_template': 'Your booking #{booking_id} has been confirmed. Workshop: {workshop_name}. Date: {preferred_date}',
            'email_template': 'booking_confirmed.html'
        },
        'payment_received': {
            'email_subject': 'Payment Received - AutoCare Services',
            'sms_template': 'Payment of Rs.{amount} received for booking #{booking_id}. Thank you!',
            'email_template': 'payment_received.html'
        },
        'service_completed': {
            'email_subject': 'Service Completed - AutoCare Services',
            'sms_template': 'Your vehicle service is completed. Booking #{booking_id}. Please collect your vehicle.',
            'email_template': 'service_completed.html'
        },
        'invoice_ready': {
            'email_subject': 'Invoice Ready - AutoCare Services',
            'sms_template': 'Invoice ready for booking #{booking_id}. Total: Rs.{total_amount}. Download from AutoCare app.',
            'email_template': 'invoice_ready.html'
        },
        'reminder': {
            'email_subject': 'Service Reminder - AutoCare Services',
            'sms_template': 'Reminder: Your vehicle service is due. Book now to avoid inconvenience.',
            'email_template': 'service_reminder.html'
        }
    }

# Development Configuration
class DevelopmentEnhancedConfig(EnhancedConfig):
    DEBUG = True
    DEVELOPMENT = True
    TESTING = False

# Production Configuration
class ProductionEnhancedConfig(EnhancedConfig):
    DEBUG = False
    DEVELOPMENT = False
    TESTING = False

    # Production overrides
    SESSION_COOKIE_SECURE = True
    API_ENABLED = True
    NOTIFICATION_ENABLED = True

# Testing Configuration
class TestingEnhancedConfig(EnhancedConfig):
    DEBUG = True
    DEVELOPMENT = False
    TESTING = True

    # Use in-memory database for testing
    MYSQL_HOST = 'localhost'
    MYSQL_DATABASE = 'autocare_test'

# Get configuration based on environment
enhanced_config = {
    'development': DevelopmentEnhancedConfig,
    'production': ProductionEnhancedConfig,
    'testing': TestingEnhancedConfig,
    'default': DevelopmentEnhancedConfig
}

def get_enhanced_config(config_name=None):
    """Get enhanced configuration based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    return enhanced_config.get(config_name, enhanced_config['default'])()

def get_notification_template(template_name):
    """Get notification template configuration"""
    config = get_enhanced_config()
    return config.NOTIFICATION_TEMPLATES.get(template_name, {})

def is_feature_enabled(feature_name):
    """Check if a feature is enabled"""
    config = get_enhanced_config()
    return getattr(config, f'{feature_name.upper()}_ENABLED', False)
