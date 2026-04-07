#!/usr/bin/env python3
"""
Critical Path Testing for Enhanced AutoCare System
Tests the main enhanced features: payment flow, notifications, PDF generation
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestEnhancedFeatures(unittest.TestCase):
    """Test the enhanced features of the AutoCare system"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        print(f"🧪 Setting up test environment in {self.test_dir}")

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        print("🧹 Test environment cleaned up")

    def test_01_config_enhanced_import(self):
        """Test that enhanced configuration can be imported"""
        print("🔍 Testing enhanced configuration import...")
        try:
            from config import get_enhanced_config, is_feature_enabled
            config = get_enhanced_config()
            self.assertIsNotNone(config)
            print("✅ Enhanced configuration imported successfully")
            return True
        except ImportError as e:
            self.fail(f"❌ Failed to import enhanced configuration: {e}")

    def test_02_payment_gateway_module(self):
        """Test payment gateway module functionality"""
        print("🔍 Testing payment gateway module...")
        try:
            from payment import PaymentGateway, get_payment_gateway

            # Test with mocked configuration
            with patch('payment_gateway.get_enhanced_config') as mock_config:
                mock_config.return_value.RAZORPAY_ENABLED = False
                mock_config.return_value.RAZORPAY_KEY_ID = None
                mock_config.return_value.RAZORPAY_KEY_SECRET = None

                gateway = PaymentGateway()
                self.assertIsNone(gateway.client)
                print("✅ Payment gateway module loaded (client not initialized due to missing config)")

            return True
        except ImportError as e:
            self.fail(f"❌ Failed to import payment gateway: {e}")

    def test_03_notification_service_module(self):
        """Test notification service module functionality"""
        print("🔍 Testing notification service module...")
        try:
            from notification import NotificationService, get_notification_service

            # Test with mocked configuration
            with patch('notification_service.get_enhanced_config') as mock_config:
                mock_config.return_value.SMS_ENABLED = False
                mock_config.return_value.EMAIL_ENABLED = False
                mock_config.return_value.MSG91_AUTH_KEY = None
                mock_config.return_value.MSG91_SENDER_ID = None
                mock_config.return_value.MAIL_USERNAME = None

                service = NotificationService()
                self.assertIsNone(service.msg91_auth_key)
                self.assertIsNone(service.msg91_sender_id)
                self.assertIsNone(service.mail)
                print("✅ Notification service module loaded (clients not initialized due to missing config)")

            return True
        except ImportError as e:
            self.fail(f"❌ Failed to import notification service: {e}")

    def test_04_pdf_generator_module(self):
        """Test PDF generator module functionality"""
        print("🔍 Testing PDF generator module...")
        try:
            from pdf import PDFGenerator, get_pdf_generator

            generator = PDFGenerator()
            self.assertIsNotNone(generator)
            print("✅ PDF generator module loaded successfully")

            return True
        except ImportError as e:
            self.fail(f"❌ Failed to import PDF generator: {e}")

    def test_05_enhanced_analytics_module(self):
        """Test enhanced analytics module functionality"""
        print("🔍 Testing enhanced analytics module...")
        try:
            from analytics import EnhancedAnalytics, get_analytics_service

            analytics = EnhancedAnalytics()
            self.assertIsNotNone(analytics)
            print("✅ Enhanced analytics module loaded successfully")

            return True
        except ImportError as e:
            self.fail(f"❌ Failed to import enhanced analytics: {e}")

    def test_06_enhanced_app_routes(self):
        """Test that enhanced app routes can be imported"""
        print("🔍 Testing enhanced app routes...")
        try:
            from app_enhanced_autocare import app

            # Check if the app has the expected routes
            routes = [rule.rule for rule in app.url_map.iter_rules()]
            enhanced_routes = [
                '/customer/service_tracking',
                '/customer/service_history',
                '/customer/invoice/<int:booking_id>',
                '/admin/logs_reports',
                '/admin/enhanced_analytics',
                '/workshop/notifications',
                '/workshop/enhanced_features'
            ]

            for route in enhanced_routes:
                self.assertIn(route, routes, f"Route {route} not found in app routes")
                print(f"✅ Route {route} found")

            print("✅ Enhanced app routes loaded successfully")
            return True
        except ImportError as e:
            self.fail(f"❌ Failed to import enhanced app: {e}")

    def test_07_template_files_exist(self):
        """Test that enhanced template files exist"""
        print("🔍 Testing enhanced template files...")
        template_files = [
            'templates/customer_service_tracking.html',
            'templates/customer_service_history.html',
            'templates/customer_payment.html',
            'templates/admin_logs_reports.html',
            'templates/admin_enhanced_analytics.html',
            'templates/workshop_notifications.html',
            'templates/workshop_enhanced_features.html'
        ]

        for template_file in template_files:
            self.assertTrue(os.path.exists(template_file), f"Template file {template_file} not found")
            print(f"✅ Template file {template_file} exists")

        print("✅ All enhanced template files exist")
        return True

    def test_08_database_schema_enhancements(self):
        """Test that database schema enhancements are present"""
        print("🔍 Testing database schema enhancements...")
        try:
            with open('setup_fixed.sql', 'r') as f:
                schema_content = f.read()

            # Check for enhanced tables
            enhanced_tables = [
                'customer_preferences',
                'workshop_inventory',
                'equipment_maintenance',
                'service_packages',
                'service_subscriptions',
                'system_logs',
                'notification_templates',
                'sent_notifications',
                'payment_config',
                'analytics_data',
                'customer_feedback',
                'service_reminders'
            ]

            for table in enhanced_tables:
                self.assertIn(f'CREATE TABLE IF NOT EXISTS {table}', schema_content,
                            f"Enhanced table {table} not found in schema")
                print(f"✅ Enhanced table {table} found in schema")

            print("✅ Database schema enhancements verified")
            return True
        except FileNotFoundError:
            self.fail("❌ Database schema file not found")

    def test_09_critical_feature_integration(self):
        """Test critical feature integration"""
        print("🔍 Testing critical feature integration...")

        try:
            # Test that all modules can be imported together
            from config import get_enhanced_config
            from payment import PaymentGateway
            from notification import NotificationService
            from pdf import PDFGenerator
            from analytics import EnhancedAnalytics

            # Test configuration integration
            config = get_enhanced_config()
            self.assertIsNotNone(config)

            # Test module instantiation
            gateway = PaymentGateway()
            notification_service = NotificationService()
            pdf_gen = PDFGenerator()
            analytics = EnhancedAnalytics()

            self.assertIsNotNone(gateway)
            self.assertIsNotNone(notification_service)
            self.assertIsNotNone(pdf_gen)
            self.assertIsNotNone(analytics)

            print("✅ All enhanced modules integrate successfully")
            return True
        except Exception as e:
            self.fail(f"❌ Critical feature integration failed: {e}")

def run_critical_tests():
    """Run all critical path tests"""
    print("🚀 Enhanced AutoCare System - Critical Path Testing")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEnhancedFeatures)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    print("=" * 60)

    if result.wasSuccessful():
        print("🎉 ALL CRITICAL TESTS PASSED!")
        print("✅ Enhanced AutoCare System is ready for deployment")
        return True
    else:
        print("❌ Some critical tests failed")
        print("⚠️  Please fix the issues before deployment")
        return False

if __name__ == "__main__":
    success = run_critical_tests()
    sys.exit(0 if success else 1)
