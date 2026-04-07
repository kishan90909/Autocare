#!/bin/bash

echo "🚀 Starting Enhanced AutoCare System - INTEGRATED VERSION"
echo "=" * 70
echo "✅ All enhanced modules integrated!"
echo "✅ Customer, Workshop, and Admin modules with enhanced features"
echo "✅ Payment Gateway (Razorpay) integration"
echo "✅ SMS/Email Notification system"
echo "✅ PDF Invoice generation"
echo "✅ Advanced Analytics and Reporting"
echo "✅ Real-time notifications and updates"
echo "✅ Interactive calendar and booking system"
echo "✅ Google Maps integration ready"
echo "✅ Role-based access control"
echo "✅ All routes and features integrated!"
echo "=" * 70
echo "🔐 Admin Login: admin@autocare.com / admin123"
echo "🔐 Workshop Login: workshop1@autocare.com / workshop123"
echo "🔐 Customer: Register new account or use existing"
echo "=" * 70
echo "🌐 Access at: http://127.0.0.1:5012"
echo "=" * 70

# Activate virtual environment if it exists
if [ -d "venv_autocare" ]; then
    echo "Activating virtual environment..."
    source venv_autocare/bin/activate
fi

# Run the enhanced application
python3 app.py
