"""
Payment Gateway Integration Module
Handles Razorpay payment processing for AutoCare system
"""
import razorpay
import json
import logging
from datetime import datetime
from flask import current_app, request
from config import get_enhanced_config

class PaymentGateway:
    def __init__(self):
        self.config = get_enhanced_config()
        self.client = None
        self.initialize_client()

    def initialize_client(self):
        """Initialize Razorpay client"""
        try:
            if self.config.RAZORPAY_ENABLED and self.config.RAZORPAY_KEY_ID and self.config.RAZORPAY_KEY_SECRET:
                self.client = razorpay.Client(
                    auth=(self.config.RAZORPAY_KEY_ID, self.config.RAZORPAY_KEY_SECRET)
                )
                logging.info("Razorpay client initialized successfully")
            else:
                logging.warning("Razorpay not configured or disabled")
        except Exception as e:
            logging.error(f"Failed to initialize Razorpay client: {e}")
            self.client = None

    def create_order(self, amount, currency="INR", receipt=None, notes=None):
        """
        Create a new payment order

        Args:
            amount (float): Amount in rupees
            currency (str): Currency code (default: INR)
            receipt (str): Receipt identifier
            notes (dict): Additional notes

        Returns:
            dict: Order details or None if failed
        """
        try:
            if not self.client:
                logging.error("Razorpay client not initialized")
                return None

            # Convert amount to paise (Razorpay expects amount in smallest currency unit)
            amount_paise = int(amount * 100)

            order_data = {
                "amount": amount_paise,
                "currency": currency,
                "receipt": receipt or f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "notes": notes or {}
            }

            order = self.client.order.create(data=order_data)
            logging.info(f"Payment order created: {order.get('id')}")
            return order

        except Exception as e:
            logging.error(f"Failed to create payment order: {e}")
            return None

    def verify_payment(self, payment_id, order_id, signature):
        """
        Verify payment signature

        Args:
            payment_id (str): Razorpay payment ID
            order_id (str): Razorpay order ID
            signature (str): Payment signature

        Returns:
            bool: True if signature is valid
        """
        try:
            if not self.client:
                return False

            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            result = self.client.utility.verify_payment_signature(params_dict)
            logging.info(f"Payment signature verified for payment: {payment_id}")
            return result

        except Exception as e:
            logging.error(f"Payment verification failed: {e}")
            return False

    def get_payment_details(self, payment_id):
        """
        Get payment details

        Args:
            payment_id (str): Razorpay payment ID

        Returns:
            dict: Payment details or None if failed
        """
        try:
            if not self.client:
                return None

            payment = self.client.payment.fetch(payment_id)
            return payment

        except Exception as e:
            logging.error(f"Failed to fetch payment details: {e}")
            return None

    def refund_payment(self, payment_id, amount=None, notes=None):
        """
        Process payment refund

        Args:
            payment_id (str): Razorpay payment ID
            amount (float): Refund amount (optional, refunds full amount if not specified)
            notes (dict): Refund notes

        Returns:
            dict: Refund details or None if failed
        """
        try:
            if not self.client:
                return None

            refund_data = {"notes": notes or {}}

            if amount:
                refund_data["amount"] = int(amount * 100)  # Convert to paise

            refund = self.client.payment.refund(payment_id, refund_data)
            logging.info(f"Refund processed for payment: {payment_id}")
            return refund

        except Exception as e:
            logging.error(f"Refund failed: {e}")
            return None

    def get_order_details(self, order_id):
        """
        Get order details

        Args:
            order_id (str): Razorpay order ID

        Returns:
            dict: Order details or None if failed
        """
        try:
            if not self.client:
                return None

            order = self.client.order.fetch(order_id)
            return order

        except Exception as e:
            logging.error(f"Failed to fetch order details: {e}")
            return None

    def generate_payment_link(self, amount, customer_details, description="AutoCare Service Payment"):
        """
        Generate payment link for customer

        Args:
            amount (float): Payment amount
            customer_details (dict): Customer information
            description (str): Payment description

        Returns:
            dict: Payment link details or None if failed
        """
        try:
            if not self.client:
                return None

            amount_paise = int(amount * 100)

            link_data = {
                "amount": amount_paise,
                "currency": "INR",
                "description": description,
                "customer": customer_details,
                "notify": {
                    "sms": True,
                    "email": True
                },
                "reminder_enable": True,
                "notes": {
                    "autocare_booking": "true"
                }
            }

            payment_link = self.client.payment_link.create(link_data)
            logging.info(f"Payment link generated: {payment_link.get('id')}")
            return payment_link

        except Exception as e:
            logging.error(f"Failed to generate payment link: {e}")
            return None

    def handle_webhook(self, webhook_data):
        """
        Handle Razorpay webhook events

        Args:
            webhook_data (dict): Webhook payload

        Returns:
            dict: Processed webhook data
        """
        try:
            event = webhook_data.get('event')
            payment_entity = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})

            processed_data = {
                'event': event,
                'payment_id': payment_entity.get('id'),
                'order_id': payment_entity.get('order_id'),
                'amount': payment_entity.get('amount', 0) / 100,  # Convert from paise
                'currency': payment_entity.get('currency'),
                'status': payment_entity.get('status'),
                'method': payment_entity.get('method'),
                'captured': payment_entity.get('captured'),
                'timestamp': datetime.now()
            }

            logging.info(f"Webhook processed: {event} - {processed_data.get('payment_id')}")
            return processed_data

        except Exception as e:
            logging.error(f"Webhook processing failed: {e}")
            return None

# Global payment gateway instance
payment_gateway = PaymentGateway()

def get_payment_gateway():
    """Get payment gateway instance"""
    return payment_gateway

def create_booking_payment_order(booking_id, amount, customer_email, customer_name):
    """
    Create payment order for a specific booking

    Args:
        booking_id (int): Booking ID
        amount (float): Payment amount
        customer_email (str): Customer email
        customer_name (str): Customer name

    Returns:
        dict: Payment order details
    """
    notes = {
        "booking_id": str(booking_id),
        "customer_name": customer_name,
        "customer_email": customer_email,
        "payment_type": "booking_payment"
    }

    return payment_gateway.create_order(
        amount=amount,
        receipt=f"booking_{booking_id}",
        notes=notes
    )

def verify_booking_payment(payment_id, order_id, signature, booking_id):
    """
    Verify payment for a specific booking

    Args:
        payment_id (str): Razorpay payment ID
        order_id (str): Razorpay order ID
        signature (str): Payment signature
        booking_id (int): Booking ID

    Returns:
        bool: True if payment is valid
    """
    is_valid = payment_gateway.verify_payment(payment_id, order_id, signature)

    if is_valid:
        logging.info(f"Payment verified for booking: {booking_id}")
    else:
        logging.warning(f"Payment verification failed for booking: {booking_id}")

    return is_valid

def process_booking_refund(booking_id, payment_id, amount=None):
    """
    Process refund for a booking payment

    Args:
        booking_id (int): Booking ID
        payment_id (str): Razorpay payment ID
        amount (float): Refund amount (optional)

    Returns:
        dict: Refund details
    """
    notes = {
        "booking_id": str(booking_id),
        "refund_type": "booking_refund"
    }

    refund = payment_gateway.refund_payment(payment_id, amount, notes)

    if refund:
        logging.info(f"Refund processed for booking: {booking_id}")
    else:
        logging.error(f"Refund failed for booking: {booking_id}")

    return refund
