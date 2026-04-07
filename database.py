"""
Database utility functions for AutoCare system
Shared database connection utilities
"""
import mysql.connector
from mysql.connector import Error
import logging
from config import get_enhanced_config

# Database configuration
config = get_enhanced_config()
DB_CONFIG_WITH_PASSWORD = {
    'host': config.MYSQL_HOST,
    'user': config.MYSQL_USER,
    'password': config.MYSQL_PASSWORD,
    'database': config.MYSQL_DATABASE,
    'port': config.MYSQL_PORT
}

DB_CONFIG_NO_PASSWORD = {
    'host': config.MYSQL_HOST,
    'user': config.MYSQL_USER,
    'database': config.MYSQL_DATABASE,
    'port': config.MYSQL_PORT
}

def get_db_connection():
    """Get database connection with error handling - tries with password first"""
    try:
        # Try connecting with password first (current working configuration)
        conn = mysql.connector.connect(**DB_CONFIG_WITH_PASSWORD)
        return conn
    except Error as e:
        try:
            # If that fails, try without password (for --skip-grant-tables mode)
            conn = mysql.connector.connect(**DB_CONFIG_NO_PASSWORD)
            return conn
        except Error as e2:
            logging.error(f"Database connection error: {e2}")
            return None

def test_db_connection():
    """Test database connection"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result is not None
        return False
    except Exception as e:
        logging.error(f"Database test error: {e}")
        return False
