"""
Notification Service Module
Handles SMS and Email notifications for AutoCare system
"""
import logging
import requests
import json
from datetime import datetime, timedelta
from flask import current_app, render_template
from flask_mail import Mail, Message
from config import get_enhanced_config, get_notification_template
import mysql.connector
from mysql.connector import Error

class NotificationService:
    def __init__(self):
        self.config = get_enhanced_config()
        self.mail = None
        self.msg91_auth_key = None
        self.msg91_sender_id = None
        self.initialize_services()

    def initialize_services(self):
        """Initialize email and SMS services"""
        try:
            # Initialize MSG91 (doesn't require Flask context)
            if self.config.MSG91_ENABLED and self.config.MSG91_AUTH_KEY and self.config.MSG91_SENDER_ID:
                self.msg91_auth_key = self.config.MSG91_AUTH_KEY
                self.msg91_sender_id = self.config.MSG91_SENDER_ID
                logging.info("MSG91 SMS service initialized successfully")
            else:
                logging.warning("MSG91 SMS service not configured or disabled")

            # Note: Flask-Mail will be initialized when needed within app context
            logging.info("Notification services initialized successfully")

        except Exception as e:
            logging.error(f"Failed to initialize notification services: {e}")

    def send_sms(self, to_phone, message):
        """
        Send SMS using MSG91

        Args:
            to_phone (str): Recipient phone number
            message (str): SMS message content

        Returns:
            bool: True if sent successfully
        """
        try:
            if not self.msg91_auth_key or not self.msg91_sender_id:
                logging.error("MSG91 credentials not initialized")
                return False

            # MSG91 API endpoint
            url = "https://api.msg91.com/api/v2/sendsms"

            payload = {
                "sender": self.msg91_sender_id,
                "route": "4",
                "country": "91",
                "sms": [
                    {
                        "message": message,
                        "to": [to_phone]
                    }
                ]
            }

            headers = {
                "authkey": self.msg91_auth_key,
                "content-type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                logging.info(f"SMS sent successfully to {to_phone}")
                return True
            else:
                logging.error(f"Failed to send SMS to {to_phone}: {response.text}")
                return False

        except Exception as e:
            logging.error(f"Unexpected error sending SMS: {e}")
            return False

    def send_email(self, to_email, subject, html_content, text_content=None):
        """
        Send email using Flask-Mail

        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            html_content (str): HTML email content
            text_content (str): Plain text content (optional)

        Returns:
            bool: True if sent successfully
        """
        try:
            # Initialize Flask-Mail if not already done
            if not self.mail and self.config.EMAIL_ENABLED:
                try:
                    from flask import current_app
                    self.mail = Mail(current_app)
                except Exception as e:
                    logging.error(f"Failed to initialize Flask-Mail: {e}")
                    return False

            if not self.mail:
                logging.error("Mail service not initialized")
                return False

            msg = Message(
                subject=subject,
                recipients=[to_email],
                html=html_content,
                body=text_content
            )

            self.mail.send(msg)
            logging.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logging.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_notification(self, notification_type, recipient_info, template_data):
        """
        Send notification using appropriate channel

        Args:
            notification_type (str): Type of notification (booking_confirmed, payment_received, etc.)
            recipient_info (dict): Recipient information (email, phone, preferences)
            template_data (dict): Data to populate template

        Returns:
            dict: Notification results
        """
        results = {
            'sms_sent': False,
            'email_sent': False,
            'errors': []
        }

        try:
            # Get notification template
            template = get_notification_template(notification_type)
            if not template:
                results['errors'].append(f"Template not found for {notification_type}")
                return results

            # Format messages
            sms_content = template.get('sms_template', '')
            email_subject = template.get('email_subject', f'Notification - {notification_type}')
            email_template_file = template.get('email_template', '')

            # Replace placeholders in templates
            for key, value in template_data.items():
                placeholder = f"{{{key}}}"
                sms_content = sms_content.replace(placeholder, str(value))

            # Send SMS if enabled and phone available
            if (self.config.MSG91_ENABLED and
                recipient_info.get('phone') and
                recipient_info.get('sms_notifications', True)):

                sms_sent = self.send_sms(recipient_info['phone'], sms_content)
                results['sms_sent'] = sms_sent

            # Send Email if enabled and email available
            if (self.config.EMAIL_ENABLED and
                recipient_info.get('email') and
                recipient_info.get('email_notifications', True)):

                # For invoice_ready, use the HTML template file
                if notification_type == 'invoice_ready' and email_template_file:
                    try:
                        from flask import render_template
                        html_content = render_template(email_template_file, **template_data)
                    except Exception as e:
                        logging.error(f"Error rendering email template {email_template_file}: {e}")
                        html_content = f"<h3>Invoice Ready</h3><p>Your invoice for booking #{template_data.get('booking_id', 'N/A')} is ready. Total: ₹{template_data.get('total_amount', 'N/A')}</p>"
                else:
                    # Use SMS content as fallback for other notifications
                    html_content = sms_content

                email_sent = self.send_email(
                    recipient_info['email'],
                    email_subject,
                    html_content,
                    sms_content  # Use SMS content as plain text fallback
                )
                results['email_sent'] = email_sent

            # Log notification
            self.log_notification(
                notification_type=notification_type,
                recipient_type=recipient_info.get('type', 'customer'),
                recipient_id=recipient_info.get('id'),
                sms_sent=results['sms_sent'],
                email_sent=results['email_sent'],
                template_data=template_data
            )

        except Exception as e:
            results['errors'].append(str(e))
            logging.error(f"Error sending notification: {e}")

        return results

    def log_notification(self, notification_type, recipient_type, recipient_id,
                        sms_sent=False, email_sent=False, template_data=None):
        """
        Log notification to database

        Args:
            notification_type (str): Type of notification
            recipient_type (str): Type of recipient (customer, workshop, admin)
            recipient_id (int): Recipient ID
            sms_sent (bool): Whether SMS was sent
            email_sent (bool): Whether email was sent
            template_data (dict): Template data used
        """
        try:
            conn = self.get_db_connection()
            if conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO sent_notifications
                    (notification_type, recipient_type, recipient_id, content, delivery_method, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    notification_type,
                    recipient_type,
                    recipient_id,
                    json.dumps(template_data or {}),
                    'both' if sms_sent and email_sent else ('sms' if sms_sent else 'email'),
                    'sent' if (sms_sent or email_sent) else 'failed'
                ))

                conn.commit()
                cursor.close()
                conn.close()

        except Exception as e:
            logging.error(f"Failed to log notification: {e}")

    def get_db_connection(self):
        """Get database connection"""
        try:
            return mysql.connector.connect(
                host=self.config.MYSQL_HOST,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                database=self.config.MYSQL_DATABASE,
                port=self.config.MYSQL_PORT
            )
        except Error as e:
            logging.error(f"Database connection error: {e}")
            return None

    def send_booking_notification(self, booking_id, notification_type, customer_info, workshop_info=None):
        """
        Send booking-related notification

        Args:
            booking_id (int): Booking ID
            notification_type (str): Type of notification
            customer_info (dict): Customer information
            workshop_info (dict): Workshop information (optional)
        """
        try:
            # Get booking details from database
            conn = self.get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)

                cursor.execute("""
                    SELECT b.*, u.username as customer_name, u.email as customer_email, u.phone as customer_phone
                    FROM bookings b
                    JOIN users u ON b.customer_id = u.id
                    WHERE b.id = %s
                """, (booking_id,))

                booking = cursor.fetchone()
                cursor.close()
                conn.close()

                if not booking:
                    logging.error(f"Booking not found: {booking_id}")
                    return False

                # Prepare template data
                template_data = {
                    'booking_id': booking_id,
                    'customer_name': booking['customer_name'],
                    'services': ', '.join([s['name'] for s in booking.get('services', [])]),
                    'total_cost': booking['total_cost'],
                    'preferred_date': booking['preferred_date'],
                    'preferred_time': booking['preferred_time'],
                    'vehicle_info': booking['vehicle_info'],
                    'status': booking['status']
                }

                if workshop_info:
                    template_data.update({
                        'workshop_name': workshop_info.get('name', ''),
                        'workshop_address': workshop_info.get('address', ''),
                        'workshop_phone': workshop_info.get('phone', '')
                    })

                # Send notification
                result = self.send_notification(
                    notification_type,
                    recipient_info=customer_info,
                    template_data=template_data
                )

                logging.info(f"Booking notification sent: {notification_type} for booking {booking_id}")
                return result

        except Exception as e:
            logging.error(f"Error sending booking notification: {e}")
            return False

    def send_payment_notification(self, booking_id, payment_amount, payment_status, customer_info):
        """
        Send payment-related notification

        Args:
            booking_id (int): Booking ID
            payment_amount (float): Payment amount
            payment_status (str): Payment status
            customer_info (dict): Customer information
        """
        try:
            template_data = {
                'booking_id': booking_id,
                'amount': payment_amount,
                'status': payment_status,
                'payment_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            notification_type = 'payment_received' if payment_status == 'completed' else 'payment_failed'

            result = self.send_notification(
                notification_type,
                recipient_info=customer_info,
                template_data=template_data
            )

            logging.info(f"Payment notification sent: {notification_type} for booking {booking_id}")
            return result

        except Exception as e:
            logging.error(f"Error sending payment notification: {e}")
            return False

    def send_service_reminder(self, customer_info, vehicle_info, service_type, next_service_date):
        """
        Send service reminder notification

        Args:
            customer_info (dict): Customer information
            vehicle_info (str): Vehicle information
            service_type (str): Type of service needed
            next_service_date (str): Recommended next service date
        """
        try:
            template_data = {
                'vehicle_info': vehicle_info,
                'service_type': service_type,
                'next_service_date': next_service_date,
                'reminder_date': datetime.now().strftime('%Y-%m-%d')
            }

            result = self.send_notification(
                'service_reminder',
                recipient_info=customer_info,
                template_data=template_data
            )

            logging.info(f"Service reminder sent to customer: {customer_info.get('id')}")
            return result

        except Exception as e:
            logging.error(f"Error sending service reminder: {e}")
            return False

# Global notification service instance
notification_service = NotificationService()

def get_notification_service():
    """Get notification service instance"""
    return notification_service

def send_booking_status_update(booking_id, status, customer_info, workshop_info=None):
    """
    Send booking status update notification

    Args:
        booking_id (int): Booking ID
        status (str): New booking status
        customer_info (dict): Customer information
        workshop_info (dict): Workshop information (optional)
    """
    notification_type = 'booking_confirmed' if status == 'confirmed' else 'status_update'

    return notification_service.send_booking_notification(
        booking_id, notification_type, customer_info, workshop_info
    )

def send_service_completion_notification(booking_id, customer_info, workshop_info):
    """
    Send service completion notification

    Args:
        booking_id (int): Booking ID
        customer_info (dict): Customer information
        workshop_info (dict): Workshop information
    """
    return notification_service.send_booking_notification(
        booking_id, 'service_completed', customer_info, workshop_info
    )
