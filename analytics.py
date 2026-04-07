"""
Enhanced Analytics Module
Provides advanced analytics and reporting for AutoCare system
"""
import logging
from datetime import datetime, timedelta, date
from collections import defaultdict
import json
from config import get_enhanced_config
import mysql.connector
from mysql.connector import Error

class EnhancedAnalytics:
    def __init__(self):
        self.config = get_enhanced_config()

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

    def log_metric(self, metric_name, metric_value, metric_type='counter', workshop_id=None, customer_id=None, booking_id=None):
        """
        Log a metric to the analytics database

        Args:
            metric_name (str): Name of the metric
            metric_value (float): Value of the metric
            metric_type (str): Type of metric (counter, gauge, histogram)
            workshop_id (int): Workshop ID (optional)
            customer_id (int): Customer ID (optional)
            booking_id (int): Booking ID (optional)
        """
        try:
            conn = self.get_db_connection()
            if conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO analytics_data
                    (metric_name, metric_value, metric_type, date_recorded, workshop_id, customer_id, booking_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    metric_name,
                    float(metric_value),
                    metric_type,
                    date.today(),
                    workshop_id,
                    customer_id,
                    booking_id
                ))

                conn.commit()
                cursor.close()
                conn.close()

                logging.info(f"Metric logged: {metric_name} = {metric_value}")

        except Exception as e:
            logging.error(f"Error logging metric: {e}")

    def get_booking_analytics(self, start_date=None, end_date=None, workshop_id=None):
        """
        Get booking analytics for the specified period

        Args:
            start_date (date): Start date for analysis
            end_date (date): End date for analysis
            workshop_id (int): Workshop ID to filter by

        Returns:
            dict: Booking analytics data
        """
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()

            conn = self.get_db_connection()
            if not conn:
                return None

            cursor = conn.cursor(dictionary=True)

            # Base query
            query = """
                SELECT
                    COUNT(*) as total_bookings,
                    SUM(total_cost) as total_revenue,
                    AVG(total_cost) as avg_booking_value,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_bookings,
                    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_bookings,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_bookings
                FROM bookings
                WHERE created_at >= %s AND created_at <= %s
            """
            params = [start_date, end_date]

            if workshop_id:
                query += " AND workshop_id = %s"
                params.append(workshop_id)

            cursor.execute(query, params)
            summary = cursor.fetchone()

            # Get daily booking trends
            cursor.execute("""
                SELECT
                    DATE(created_at) as booking_date,
                    COUNT(*) as bookings_count,
                    SUM(total_cost) as daily_revenue
                FROM bookings
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY DATE(created_at)
                ORDER BY booking_date
            """, (start_date, end_date))

            daily_trends = cursor.fetchall()

            # Get service popularity
            cursor.execute("""
                SELECT
                    s.name as service_name,
                    COUNT(bs.service_id) as booking_count,
                    SUM(s.price) as total_revenue
                FROM booking_services bs
                JOIN services s ON bs.service_id = s.id
                JOIN bookings b ON bs.booking_id = b.id
                WHERE b.created_at >= %s AND b.created_at <= %s
                GROUP BY bs.service_id, s.name
                ORDER BY booking_count DESC
                LIMIT 10
            """, (start_date, end_date))

            service_popularity = cursor.fetchall()

            cursor.close()
            conn.close()

            return {
                'summary': summary,
                'daily_trends': daily_trends,
                'service_popularity': service_popularity,
                'period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                }
            }

        except Exception as e:
            logging.error(f"Error getting booking analytics: {e}")
            return None

    def get_customer_analytics(self, start_date=None, end_date=None):
        """
        Get customer analytics for the specified period

        Args:
            start_date (date): Start date for analysis
            end_date (date): End date for analysis

        Returns:
            dict: Customer analytics data
        """
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()

            conn = self.get_db_connection()
            if not conn:
                return None

            cursor = conn.cursor(dictionary=True)

            # Customer acquisition over time
            cursor.execute("""
                SELECT
                    DATE(created_at) as signup_date,
                    COUNT(*) as new_customers
                FROM users
                WHERE role = 'customer' AND created_at >= %s AND created_at <= %s
                GROUP BY DATE(created_at)
                ORDER BY signup_date
            """, (start_date, end_date))

            customer_acquisition = cursor.fetchall()

            # Customer retention (customers who made repeat bookings)
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT customer_id) as repeat_customers
                FROM bookings
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY customer_id
                HAVING COUNT(*) > 1
            """, (start_date, end_date))

            repeat_customers = cursor.fetchone()
            repeat_count = repeat_customers['repeat_customers'] if repeat_customers else 0

            # Total customers
            cursor.execute("""
                SELECT COUNT(*) as total_customers
                FROM users
                WHERE role = 'customer' AND created_at <= %s
            """, (end_date,))

            total_customers = cursor.fetchone()['total_customers']

            # Customer satisfaction (average rating)
            cursor.execute("""
                SELECT
                    AVG(rating) as avg_rating,
                    COUNT(*) as total_reviews
                FROM reviews
                WHERE created_at >= %s AND created_at <= %s
            """, (start_date, end_date))

            satisfaction = cursor.fetchone()

            cursor.close()
            conn.close()

            return {
                'customer_acquisition': customer_acquisition,
                'repeat_customers': repeat_count,
                'total_customers': total_customers,
                'satisfaction': satisfaction,
                'retention_rate': (repeat_count / total_customers * 100) if total_customers > 0 else 0
            }

        except Exception as e:
            logging.error(f"Error getting customer analytics: {e}")
            return None

    def get_workshop_analytics(self, start_date=None, end_date=None):
        """
        Get workshop analytics for the specified period

        Args:
            start_date (date): Start date for analysis
            end_date (date): End date for analysis

        Returns:
            dict: Workshop analytics data
        """
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()

            conn = self.get_db_connection()
            if not conn:
                return None

            cursor = conn.cursor(dictionary=True)

            # Workshop performance
            cursor.execute("""
                SELECT
                    w.name as workshop_name,
                    COUNT(b.id) as total_bookings,
                    SUM(b.total_cost) as total_revenue,
                    AVG(b.total_cost) as avg_booking_value,
                    COUNT(CASE WHEN b.status = 'completed' THEN 1 END) as completed_bookings,
                    COUNT(CASE WHEN b.status = 'cancelled' THEN 1 END) as cancelled_bookings,
                    AVG(r.rating) as avg_rating,
                    COUNT(r.id) as total_reviews
                FROM workshops w
                LEFT JOIN bookings b ON w.id = b.workshop_id AND b.created_at >= %s AND b.created_at <= %s
                LEFT JOIN reviews r ON b.id = r.booking_id
                GROUP BY w.id, w.name
                ORDER BY total_revenue DESC
            """, (start_date, end_date))

            workshop_performance = cursor.fetchall()

            # Workshop utilization
            cursor.execute("""
                SELECT
                    w.name as workshop_name,
                    COUNT(b.id) as bookings_count,
                    COUNT(DISTINCT DATE(b.preferred_date)) as working_days,
                    ROUND(COUNT(b.id) / COUNT(DISTINCT DATE(b.preferred_date)), 2) as avg_daily_bookings
                FROM workshops w
                LEFT JOIN bookings b ON w.id = b.workshop_id AND b.created_at >= %s AND b.created_at <= %s
                GROUP BY w.id, w.name
                ORDER BY avg_daily_bookings DESC
            """, (start_date, end_date))

            workshop_utilization = cursor.fetchall()

            cursor.close()
            conn.close()

            return {
                'workshop_performance': workshop_performance,
                'workshop_utilization': workshop_utilization
            }

        except Exception as e:
            logging.error(f"Error getting workshop analytics: {e}")
            return None

    def get_revenue_analytics(self, start_date=None, end_date=None):
        """
        Get revenue analytics for the specified period

        Args:
            start_date (date): Start date for analysis
            end_date (date): End date for analysis

        Returns:
            dict: Revenue analytics data
        """
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()

            conn = self.get_db_connection()
            if not conn:
                return None

            cursor = conn.cursor(dictionary=True)

            # Revenue by day
            cursor.execute("""
                SELECT
                    DATE(created_at) as revenue_date,
                    SUM(total_cost) as daily_revenue,
                    COUNT(*) as daily_bookings
                FROM bookings
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY DATE(created_at)
                ORDER BY revenue_date
            """, (start_date, end_date))

            daily_revenue = cursor.fetchall()

            # Revenue by service
            cursor.execute("""
                SELECT
                    s.name as service_name,
                    SUM(s.price) as service_revenue,
                    COUNT(bs.service_id) as service_count
                FROM booking_services bs
                JOIN services s ON bs.service_id = s.id
                JOIN bookings b ON bs.booking_id = b.id
                WHERE b.created_at >= %s AND b.created_at <= %s
                GROUP BY bs.service_id, s.name
                ORDER BY service_revenue DESC
            """, (start_date, end_date))

            service_revenue = cursor.fetchall()

            # Payment method breakdown
            cursor.execute("""
                SELECT
                    payment_method,
                    COUNT(*) as payment_count,
                    SUM(amount) as total_amount
                FROM payments
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY payment_method
                ORDER BY total_amount DESC
            """, (start_date, end_date))

            payment_methods = cursor.fetchall()

            # Calculate totals
            total_revenue = sum(day['daily_revenue'] for day in daily_revenue)
            total_bookings = sum(day['daily_bookings'] for day in daily_revenue)

            cursor.close()
            conn.close()

            return {
                'daily_revenue': daily_revenue,
                'service_revenue': service_revenue,
                'payment_methods': payment_methods,
                'totals': {
                    'total_revenue': total_revenue,
                    'total_bookings': total_bookings,
                    'avg_booking_value': total_revenue / total_bookings if total_bookings > 0 else 0
                }
            }

        except Exception as e:
            logging.error(f"Error getting revenue analytics: {e}")
            return None

    def get_system_logs_summary(self, start_date=None, end_date=None, log_level=None):
        """
        Get system logs summary

        Args:
            start_date (date): Start date for analysis
            end_date (date): End date for analysis
            log_level (str): Log level to filter by

        Returns:
            dict: System logs summary
        """
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=7)
            if not end_date:
                end_date = date.today()

            conn = self.get_db_connection()
            if not conn:
                return None

            cursor = conn.cursor(dictionary=True)

            # Log level distribution
            query = """
                SELECT
                    log_level,
                    COUNT(*) as log_count
                FROM system_logs
                WHERE created_at >= %s AND created_at <= %s
            """
            params = [start_date, end_date]

            if log_level:
                query += " AND log_level = %s"
                params.append(log_level)

            query += " GROUP BY log_level ORDER BY log_count DESC"

            cursor.execute(query, params)
            log_levels = cursor.fetchall()

            # Logs by category
            cursor.execute("""
                SELECT
                    category,
                    COUNT(*) as log_count
                FROM system_logs
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY category
                ORDER BY log_count DESC
                LIMIT 10
            """, (start_date, end_date))

            log_categories = cursor.fetchall()

            # Recent errors
            cursor.execute("""
                SELECT
                    message,
                    category,
                    created_at,
                    user_id
                FROM system_logs
                WHERE log_level IN ('ERROR', 'CRITICAL')
                AND created_at >= %s AND created_at <= %s
                ORDER BY created_at DESC
                LIMIT 10
            """, (start_date, end_date))

            recent_errors = cursor.fetchall()

            cursor.close()
            conn.close()

            return {
                'log_levels': log_levels,
                'log_categories': log_categories,
                'recent_errors': recent_errors,
                'total_logs': sum(log['log_count'] for log in log_levels)
            }

        except Exception as e:
            logging.error(f"Error getting system logs summary: {e}")
            return None

    def generate_comprehensive_report(self, report_type='monthly', include_charts=True):
        """
        Generate comprehensive analytics report

        Args:
            report_type (str): Type of report (daily, weekly, monthly)
            include_charts (bool): Whether to include chart data

        Returns:
            dict: Comprehensive report data
        """
        try:
            # Determine date range based on report type
            today = date.today()
            if report_type == 'daily':
                start_date = today - timedelta(days=1)
                end_date = today
            elif report_type == 'weekly':
                start_date = today - timedelta(days=7)
                end_date = today
            else:  # monthly
                start_date = today - timedelta(days=30)
                end_date = today

            # Gather all analytics
            booking_analytics = self.get_booking_analytics(start_date, end_date)
            customer_analytics = self.get_customer_analytics(start_date, end_date)
            workshop_analytics = self.get_workshop_analytics(start_date, end_date)
            revenue_analytics = self.get_revenue_analytics(start_date, end_date)
            system_logs = self.get_system_logs_summary(start_date, end_date)

            return {
                'report_info': {
                    'report_type': report_type,
                    'generated_at': datetime.now(),
                    'period': {
                        'start_date': start_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d')
                    }
                },
                'booking_analytics': booking_analytics,
                'customer_analytics': customer_analytics,
                'workshop_analytics': workshop_analytics,
                'revenue_analytics': revenue_analytics,
                'system_logs': system_logs,
                'include_charts': include_charts
            }

        except Exception as e:
            logging.error(f"Error generating comprehensive report: {e}")
            return None

# Global analytics instance
analytics = EnhancedAnalytics()

def get_analytics():
    """Get analytics instance"""
    return analytics

def get_analytics_service():
    """Get analytics service instance (alias for get_analytics)"""
    return analytics

def log_user_activity(user_id, activity_type, details=None, ip_address=None):
    """
    Log user activity

    Args:
        user_id (int): User ID
        activity_type (str): Type of activity
        details (str): Activity details
        ip_address (str): User IP address
    """
    analytics.log_metric(
        metric_name=f'user_activity_{activity_type}',
        metric_value=1,
        metric_type='counter',
        customer_id=user_id
    )

def log_booking_event(booking_id, event_type, workshop_id=None):
    """
    Log booking event

    Args:
        booking_id (int): Booking ID
        event_type (str): Type of event
        workshop_id (int): Workshop ID
    """
    analytics.log_metric(
        metric_name=f'booking_event_{event_type}',
        metric_value=1,
        metric_type='counter',
        booking_id=booking_id,
        workshop_id=workshop_id
    )

def log_system_event(category, message, level='INFO', user_id=None):
    """
    Log system event

    Args:
        category (str): Event category
        message (str): Event message
        level (str): Log level
        user_id (int): User ID (optional)
    """
    try:
        conn = analytics.get_db_connection()
        if conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO system_logs
                (log_level, category, message, user_id, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                level,
                category,
                message,
                user_id,
                None,  # IP address would be set by calling function
                None   # User agent would be set by calling function
            ))

            conn.commit()
            cursor.close()
            conn.close()

    except Exception as e:
        logging.error(f"Error logging system event: {e}")
