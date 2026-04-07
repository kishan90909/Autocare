"""
WebSocket Service for AutoCare Real-time Updates
Provides real-time communication between server and clients
"""

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import json
import logging
from datetime import datetime
from threading import Thread
import time

class WebSocketService:
    def __init__(self, app, db):
        self.socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        self.db = db
        self.connected_clients = {}
        self.notification_threads = {}

        # Register event handlers
        self._register_handlers()

        # Start background services
        self._start_background_services()

    def _register_handlers(self):
        """Register WebSocket event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            client_id = request.sid
            client_ip = request.remote_addr
            self.connected_clients[client_id] = {
                'ip': client_ip,
                'connected_at': datetime.now(),
                'user_type': None,
                'user_id': None
            }
            logging.info(f"Client {client_id} connected from {client_ip}")
            emit('connection_status', {'status': 'connected', 'client_id': client_id})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            client_id = request.sid
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
            logging.info(f"Client {client_id} disconnected")

        @self.socketio.on('join')
        def handle_join(data):
            """Handle client joining a room"""
            client_id = request.sid
            room = data.get('room', 'general')
            user_type = data.get('user_type')
            user_id = data.get('user_id')

            join_room(room)

            # Update client info
            if client_id in self.connected_clients:
                self.connected_clients[client_id]['user_type'] = user_type
                self.connected_clients[client_id]['user_id'] = user_id

            logging.info(f"Client {client_id} joined room {room}")
            emit('joined_room', {'room': room, 'client_id': client_id})

        @self.socketio.on('leave')
        def handle_leave(data):
            """Handle client leaving a room"""
            client_id = request.sid
            room = data.get('room', 'general')
            leave_room(room)
            logging.info(f"Client {client_id} left room {room}")

        @self.socketio.on('subscribe_notifications')
        def handle_subscribe_notifications(data):
            """Subscribe to real-time notifications"""
            client_id = request.sid
            user_type = data.get('user_type', 'customer')
            user_id = data.get('user_id')

            # Join user-specific room
            user_room = f"{user_type}_{user_id}"
            join_room(user_room)

            logging.info(f"Client {client_id} subscribed to notifications for {user_room}")
            emit('notification_subscribed', {'user_room': user_room})

        @self.socketio.on('customer_status_update')
        def handle_customer_status_update(data):
            """Handle customer status updates"""
            booking_id = data.get('booking_id')
            status = data.get('status')
            customer_id = data.get('customer_id')

            # Broadcast to workshop and admin
            self.socketio.emit('customer_status_changed', {
                'booking_id': booking_id,
                'status': status,
                'customer_id': customer_id,
                'timestamp': datetime.now().isoformat()
            }, room='workshop')

            self.socketio.emit('customer_status_changed', {
                'booking_id': booking_id,
                'status': status,
                'customer_id': customer_id,
                'timestamp': datetime.now().isoformat()
            }, room='admin')

        @self.socketio.on('workshop_status_update')
        def handle_workshop_status_update(data):
            """Handle workshop status updates"""
            booking_id = data.get('booking_id')
            status = data.get('status')
            workshop_id = data.get('workshop_id')

            # Broadcast to customer and admin
            customer_room = f"customer_{data.get('customer_id')}"
            self.socketio.emit('workshop_status_changed', {
                'booking_id': booking_id,
                'status': status,
                'workshop_id': workshop_id,
                'timestamp': datetime.now().isoformat()
            }, room=customer_room)

            self.socketio.emit('workshop_status_changed', {
                'booking_id': booking_id,
                'status': status,
                'workshop_id': workshop_id,
                'timestamp': datetime.now().isoformat()
            }, room='admin')

        @self.socketio.on('new_booking')
        def handle_new_booking(data):
            """Handle new booking notifications"""
            booking_data = data.get('booking_data', {})

            # Notify relevant workshops
            service_type = booking_data.get('service_type')
            location = booking_data.get('location')

            # This would typically involve more sophisticated matching logic
            self.socketio.emit('new_booking_alert', {
                'booking': booking_data,
                'timestamp': datetime.now().isoformat()
            }, room='workshop')

        @self.socketio.on('payment_update')
        def handle_payment_update(data):
            """Handle payment status updates"""
            booking_id = data.get('booking_id')
            payment_status = data.get('payment_status')
            customer_id = data.get('customer_id')

            # Notify customer and admin
            customer_room = f"customer_{customer_id}"
            self.socketio.emit('payment_status_changed', {
                'booking_id': booking_id,
                'payment_status': payment_status,
                'timestamp': datetime.now().isoformat()
            }, room=customer_room)

            self.socketio.emit('payment_status_changed', {
                'booking_id': booking_id,
                'payment_status': payment_status,
                'timestamp': datetime.now().isoformat()
            }, room='admin')

    def _start_background_services(self):
        """Start background services for real-time updates"""
        # Start notification broadcaster
        notification_thread = Thread(target=self._notification_broadcaster, daemon=True)
        notification_thread.start()

        # Start system metrics broadcaster
        metrics_thread = Thread(target=self._system_metrics_broadcaster, daemon=True)
        metrics_thread.start()

    def _notification_broadcaster(self):
        """Background thread to broadcast notifications"""
        while True:
            try:
                # Check for new notifications in database
                # This would typically query the notifications table
                # For now, we'll simulate periodic updates

                # Broadcast system status every 30 seconds
                self.socketio.emit('system_status', {
                    'active_clients': len(self.connected_clients),
                    'timestamp': datetime.now().isoformat()
                })

                time.sleep(30)
            except Exception as e:
                logging.error(f"Error in notification broadcaster: {e}")
                time.sleep(60)  # Wait before retrying

    def _system_metrics_broadcaster(self):
        """Background thread to broadcast system metrics"""
        while True:
            try:
                # Get system metrics (simplified)
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'active_connections': len(self.connected_clients),
                    'rooms': list(set([room for client in self.connected_clients.values()
                                     for room in ['general', f"user_{client.get('user_id', 'unknown')}"]]))
                }

                self.socketio.emit('system_metrics', metrics)
                time.sleep(10)  # Update every 10 seconds
            except Exception as e:
                logging.error(f"Error in metrics broadcaster: {e}")
                time.sleep(30)

    def emit_to_user(self, user_type, user_id, event, data):
        """Emit event to specific user"""
        user_room = f"{user_type}_{user_id}"
        self.socketio.emit(event, data, room=user_room)

    def emit_to_room(self, room, event, data):
        """Emit event to specific room"""
        self.socketio.emit(event, data, room=room)

    def broadcast_alert(self, alert_type, message, priority='medium', data=None):
        """Broadcast alert to all connected clients"""
        alert_data = {
            'type': alert_type,
            'message': message,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }

        self.socketio.emit('alert', alert_data)

    def send_notification(self, user_type, user_id, title, message, notification_type='info', data=None):
        """Send notification to specific user"""
        notification_data = {
            'title': title,
            'message': message,
            'type': notification_type,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }

        self.emit_to_user(user_type, user_id, 'notification', notification_data)

    def get_connected_clients(self):
        """Get information about connected clients"""
        return self.connected_clients.copy()

    def get_client_count(self):
        """Get number of connected clients"""
        return len(self.connected_clients)

    def start_background_task(self, target, args=None):
        """Start a background task"""
        if args is None:
            args = ()
        thread = Thread(target=target, args=args, daemon=True)
        thread.start()
        return thread
