CREATE DATABASE IF NOT EXISTS autocare;
USE autocare;

-- Add missing columns to existing tables if they don't exist
ALTER TABLE services ADD COLUMN IF NOT EXISTS duration INT DEFAULT 30;
ALTER TABLE services ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE;
ALTER TABLE services ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE services ADD COLUMN IF NOT EXISTS vehicle_type VARCHAR(50) DEFAULT 'Car';

-- Stores user information (admins, customers, workshops)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','customer','workshop') NOT NULL,
    approved BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- Stores worker information
CREATE TABLE IF NOT EXISTS workers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    experience_years INT DEFAULT 0,
    phone VARCHAR(20),
    availability BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);

-- Stores workshop information
CREATE TABLE IF NOT EXISTS workshops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    latitude DOUBLE DEFAULT 19.0760,
    longitude DOUBLE DEFAULT 72.8777,
    approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_workshop_user (user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_approved (approved)
);

-- Services catalog
CREATE TABLE IF NOT EXISTS services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    duration INT DEFAULT 30, -- in minutes
    active BOOLEAN DEFAULT TRUE,
    vehicle_type VARCHAR(50) DEFAULT 'Car',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_service_name (name),
    INDEX idx_name (name),
    INDEX idx_active (active)
);

-- Links workers to the specific services they can perform
CREATE TABLE IF NOT EXISTS worker_skills (
    worker_id INT,
    service_id INT,
    PRIMARY KEY (worker_id, service_id),
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
    INDEX idx_worker_id (worker_id),
    INDEX idx_service_id (service_id)
);

-- Bookings table
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    worker_id INT DEFAULT NULL,
    status ENUM('pending','assigned','in_progress','completed','cancelled') DEFAULT 'pending',
    total_cost DECIMAL(10, 2) DEFAULT 0.00,
    preferred_date DATE,
    preferred_time TIME,
    vehicle_type VARCHAR(50),
    vehicle_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE SET NULL,
    INDEX idx_customer_id (customer_id),
    INDEX idx_worker_id (worker_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_preferred_date (preferred_date),
    INDEX idx_vehicle_type (vehicle_type)
);

-- Links a booking to the multiple services selected by the customer
CREATE TABLE IF NOT EXISTS booking_services (
    booking_id INT,
    service_id INT,
    quantity INT DEFAULT 1,
    price DECIMAL(10, 2),
    PRIMARY KEY (booking_id, service_id),
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
    INDEX idx_booking_id (booking_id),
    INDEX idx_service_id (service_id)
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    customer_id INT NOT NULL,
    workshop_id INT,
    rating TINYINT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (workshop_id) REFERENCES workshops(id) ON DELETE SET NULL,
    INDEX idx_booking_id (booking_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_workshop_id (workshop_id)
);

-- Contact messages table
CREATE TABLE IF NOT EXISTS contact_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    status ENUM('pending','in_progress','resolved') DEFAULT 'pending',
    response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    user_id INT,
    booking_id INT,
    workshop_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (workshop_id) REFERENCES workshops(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_booking_id (booking_id),
    INDEX idx_workshop_id (workshop_id),
    INDEX idx_type (type)
);

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    customer_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status ENUM('pending','paid','overdue','cancelled') DEFAULT 'pending',
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_booking_id (booking_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_status (status)
);

-- Invoice items table
CREATE TABLE IF NOT EXISTS invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    description VARCHAR(512) NOT NULL,
    quantity INT DEFAULT 1,
    rate DECIMAL(10, 2) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    INDEX idx_invoice_id (invoice_id)
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    order_id VARCHAR(255),
    payment_id VARCHAR(255),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    status ENUM('pending','completed','failed','refunded') DEFAULT 'pending',
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    INDEX idx_booking_id (booking_id),
    INDEX idx_status (status)
);

-- Garages table for locating workshops/garages on map
CREATE TABLE IF NOT EXISTS garages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    latitude DOUBLE NOT NULL,
    longitude DOUBLE NOT NULL,
    phone VARCHAR(50),
    rating DECIMAL(3, 2) DEFAULT 0.00,
    active TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_active (active),
    INDEX idx_rating (rating)
);

-- PRE-POPULATE with sample data
INSERT INTO services (name, description, price, duration, vehicle_type) VALUES
-- BIKE
('Bike Oil Change', 'Bike engine oil change', 250.00, 20, 'Bike'),
('Bike Brake Service', 'Bike brake check & repair', 400.00, 30, 'Bike'),
('Bike Chain Service', 'Chain cleaning & lubrication', 200.00, 15, 'Bike'),
('Bike Wash', 'Complete bike wash', 150.00, 20, 'Bike'),
('Bike Tune-up', 'Complete bike tuning', 600.00, 40, 'Bike'),
('Bike Battery Check', 'Bike battery check & replace', 350.00, 20, 'Bike'),

-- AUTO
('Auto Oil Change', 'Auto engine oil change', 400.00, 25, 'Auto'),
('Auto Brake Service', 'Auto brake inspection', 700.00, 40, 'Auto'),
('Auto Cleaning', 'Full auto cleaning', 300.00, 30, 'Auto'),
('Auto Engine Check', 'Auto engine diagnostic', 1000.00, 50, 'Auto'),
('Auto Tire Service', 'Auto tire service', 500.00, 30, 'Auto'),
('Auto Battery Service', 'Battery testing', 450.00, 25, 'Auto'),

-- CAR
('Car Oil Change', 'Complete engine oil change', 500.00, 30, 'Car'),
('Car Brake Service', 'Brake pad replacement', 1200.00, 60, 'Car'),
('Car Tire Rotation', 'Tire balancing', 300.00, 20, 'Car'),
('Car Wash', 'Interior & exterior cleaning', 400.00, 45, 'Car'),
('Car Tune-up', 'Engine diagnostic', 2500.00, 90, 'Car'),
('Car Battery Replacement', 'Battery testing', 800.00, 25, 'Car'),

-- TRUCK
('Truck Oil Change', 'Truck oil service', 2000.00, 60, 'Truck'),
('Truck Brake Service', 'Heavy brake inspection', 3500.00, 90, 'Truck'),
('Truck Tire Service', 'Truck tire check', 1500.00, 45, 'Truck'),
('Truck Wash', 'Heavy vehicle wash', 1000.00, 40, 'Truck'),
('Truck Engine Check', 'Engine diagnostics', 4000.00, 120, 'Truck'),
('Truck Battery Check', 'Battery service', 1200.00, 35, 'Truck'),

-- BUS
('Bus Oil Change', 'Bus engine oil service', 1800.00, 60, 'Bus'),
('Bus Brake Service', 'Bus brake inspection', 3000.00, 90, 'Bus'),
('Bus Cleaning', 'Complete bus cleaning', 1200.00, 45, 'Bus'),
('Bus Engine Check', 'Bus engine diagnostics', 3500.00, 110, 'Bus'),
('Bus Tire Service', 'Bus tire alignment', 1400.00, 50, 'Bus'),
('Bus Battery Service', 'Battery check & replace', 1000.00, 35, 'Bus')
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    price = VALUES(price),
    duration = VALUES(duration),
    vehicle_type = VALUES(vehicle_type);


-- Sample garages
INSERT INTO garages (name, address, latitude, longitude, phone, active) VALUES
('AutoCare Central', '123 Main St, Vadodara', 22.3072, 73.1812, '+91-9876543210', 1),
('Speedy Garage', '45 Ring Road, Vadodara', 22.3122, 73.1862, '+91-9876543211', 1),
('City Auto Service', '78 LBS Road, Vadodara', 22.3022, 73.1762, '+91-9876543212', 1)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    address = VALUES(address),
    latitude = VALUES(latitude),
    longitude = VALUES(longitude),
    phone = VALUES(phone),
    active = VALUES(active);

-- Sample admin user (password: admin123)
INSERT INTO users (username, email, password, role, approved) VALUES
('admin', 'admin@autocare.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewFBNbLhOvjHnI3m', 'admin', TRUE)
ON DUPLICATE KEY UPDATE
    username = VALUES(username),
    password = VALUES(password),
    role = VALUES(role),
    approved = VALUES(approved);


-- Workshop users (password: workshop123)
INSERT INTO users (username, email, password, role, approved) VALUES
('workshop1', 'workshop1@autocare.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewFBNbLhOvjHnI3m', 'workshop', TRUE),
('workshop2', 'workshop2@autocare.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewFBNbLhOvjHnI3m', 'workshop', TRUE),
('workshop3', 'workshop3@autocare.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewFBNbLhOvjHnI3m', 'workshop', TRUE),
('workshop4', 'workshop4@autocare.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewFBNbLhOvjHnI3m', 'workshop', TRUE),
('workshop5', 'workshop5@autocare.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewFBNbLhOvjHnI3m', 'workshop', TRUE)

ON DUPLICATE KEY UPDATE
    username = VALUES(username),
    password = VALUES(password),
    role = VALUES(role),
    approved = VALUES(approved);


-- Create workshop records for all workshops
INSERT INTO workshops (user_id, name, address, phone, latitude, longitude, approved)

SELECT u.id, 'City Auto Service', '123 Main St, Vadodara', '+91-9876543210', 22.3072, 73.1812, TRUE
FROM users u WHERE u.email = 'workshop1@autocare.com'

UNION ALL
SELECT u.id, 'Speed Auto Garage', 'Ring Road, Ahmedabad', '+91-9876543211', 23.0225, 72.5714, TRUE
FROM users u WHERE u.email = 'workshop2@autocare.com'

UNION ALL
SELECT u.id, 'Prime Car Care', 'Satellite, Ahmedabad', '+91-9876543212', 23.0300, 72.5500, TRUE
FROM users u WHERE u.email = 'workshop3@autocare.com'

UNION ALL
SELECT u.id, 'AutoFix Hub', 'Navrangpura, Ahmedabad', '+91-9876543213', 23.0370, 72.5600, TRUE
FROM users u WHERE u.email = 'workshop4@autocare.com'

UNION ALL
SELECT u.id, 'Urban Mechanic', 'Maninagar, Ahmedabad', '+91-9876543214', 22.9900, 72.6000, TRUE
FROM users u WHERE u.email = 'workshop5@autocare.com'

ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    address = VALUES(address),
    phone = VALUES(phone),
    latitude = VALUES(latitude),
    longitude = VALUES(longitude),
    approved = VALUES(approved);


-- Customer preferences and notification settings
CREATE TABLE IF NOT EXISTS customer_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    sms_notifications BOOLEAN DEFAULT TRUE,
    email_notifications BOOLEAN DEFAULT TRUE,
    reminder_days_before INT DEFAULT 1,
    preferred_contact_method ENUM('sms', 'email', 'both') DEFAULT 'both',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_customer_id (customer_id)
);

-- Workshop inventory management
CREATE TABLE IF NOT EXISTS workshop_inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workshop_id INT NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    item_code VARCHAR(100),
    quantity INT DEFAULT 0,
    min_quantity INT DEFAULT 5,
    unit_price DECIMAL(10, 2),
    supplier_name VARCHAR(255),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (workshop_id) REFERENCES workshops(id) ON DELETE CASCADE,
    INDEX idx_workshop_id (workshop_id),
    INDEX idx_item_code (item_code)
);

-- Equipment maintenance tracking
CREATE TABLE IF NOT EXISTS equipment_maintenance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workshop_id INT NOT NULL,
    equipment_name VARCHAR(255) NOT NULL,
    equipment_type VARCHAR(100),
    purchase_date DATE,
    last_maintenance_date DATE,
    next_maintenance_date DATE,
    maintenance_cost DECIMAL(10, 2),
    status ENUM('operational', 'maintenance', 'out_of_service') DEFAULT 'operational',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (workshop_id) REFERENCES workshops(id) ON DELETE CASCADE,
    INDEX idx_workshop_id (workshop_id),
    INDEX idx_status (status)
);

-- Service packages
CREATE TABLE IF NOT EXISTS service_packages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workshop_id INT NOT NULL,
    package_name VARCHAR(255) NOT NULL,
    description TEXT,
    services_included JSON,
    package_price DECIMAL(10, 2) NOT NULL,
    duration_months INT DEFAULT 12,
    max_services INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (workshop_id) REFERENCES workshops(id) ON DELETE CASCADE,
    INDEX idx_workshop_id (workshop_id),
    INDEX idx_active (is_active)
);

-- Customer service subscriptions
CREATE TABLE IF NOT EXISTS service_subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    package_id INT NOT NULL,
    workshop_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    services_used INT DEFAULT 0,
    max_services INT,
    status ENUM('active', 'expired', 'cancelled') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES service_packages(id) ON DELETE CASCADE,
    FOREIGN KEY (workshop_id) REFERENCES workshops(id) ON DELETE CASCADE,
    INDEX idx_customer_id (customer_id),
    INDEX idx_package_id (package_id),
    INDEX idx_status (status)
);

-- Enhanced logging system
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    log_level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL,
    category VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    user_id INT,
    booking_id INT,
    workshop_id INT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_log_level (log_level),
    INDEX idx_category (category),
    INDEX idx_user_id (user_id),
    INDEX idx_booking_id (booking_id),
    INDEX idx_workshop_id (workshop_id),
    INDEX idx_created_at (created_at)
);

-- Notification templates
CREATE TABLE IF NOT EXISTS notification_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_name VARCHAR(100) UNIQUE NOT NULL,
    template_type ENUM('sms', 'email', 'both') NOT NULL,
    subject VARCHAR(255),
    sms_content TEXT,
    email_content TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_template_name (template_name),
    INDEX idx_active (is_active)
);

-- Sent notifications tracking
CREATE TABLE IF NOT EXISTS sent_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT,
    recipient_type ENUM('customer', 'workshop', 'admin') NOT NULL,
    recipient_id INT,
    notification_type VARCHAR(100) NOT NULL,
    subject VARCHAR(255),
    content TEXT NOT NULL,
    delivery_method ENUM('sms', 'email', 'push') NOT NULL,
    status ENUM('sent', 'delivered', 'failed', 'pending') DEFAULT 'pending',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP NULL,
    error_message TEXT,
    FOREIGN KEY (template_id) REFERENCES notification_templates(id) ON DELETE SET NULL,
    INDEX idx_recipient_type (recipient_type),
    INDEX idx_recipient_id (recipient_id),
    INDEX idx_status (status),
    INDEX idx_sent_at (sent_at)
);

-- Payment gateway configuration
CREATE TABLE IF NOT EXISTS payment_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    gateway_name VARCHAR(100) UNIQUE NOT NULL,
    gateway_type ENUM('razorpay', 'stripe', 'paypal') NOT NULL,
    api_key VARCHAR(255),
    api_secret VARCHAR(255),
    webhook_secret VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    test_mode BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_gateway_name (gateway_name),
    INDEX idx_active (is_active)
);

-- Enhanced analytics data
CREATE TABLE IF NOT EXISTS analytics_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 2),
    metric_type ENUM('counter', 'gauge', 'histogram') DEFAULT 'counter',
    date_recorded DATE NOT NULL,
    workshop_id INT,
    customer_id INT,
    booking_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_metric_name (metric_name),
    INDEX idx_date_recorded (date_recorded),
    INDEX idx_workshop_id (workshop_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_booking_id (booking_id)
);

-- Customer feedback and ratings
CREATE TABLE IF NOT EXISTS customer_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    customer_id INT NOT NULL,
    workshop_id INT NOT NULL,
    rating_overall TINYINT CHECK (rating_overall >= 1 AND rating_overall <= 5),
    rating_service_quality TINYINT CHECK (rating_service_quality >= 1 AND rating_service_quality <= 5),
    rating_staff_behavior TINYINT CHECK (rating_staff_behavior >= 1 AND rating_staff_behavior <= 5),
    rating_value_for_money TINYINT CHECK (rating_value_for_money >= 1 AND rating_value_for_money <= 5),
    comments TEXT,
    would_recommend BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (workshop_id) REFERENCES workshops(id) ON DELETE CASCADE,
    INDEX idx_booking_id (booking_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_workshop_id (workshop_id)
);

-- Service reminders
CREATE TABLE IF NOT EXISTS service_reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    vehicle_info TEXT,
    service_type VARCHAR(100),
    last_service_date DATE,
    next_service_date DATE,
    reminder_sent BOOLEAN DEFAULT FALSE,
    reminder_date TIMESTAMP NULL,
    status ENUM('pending', 'sent', 'completed', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_customer_id (customer_id),
    INDEX idx_next_service_date (next_service_date),
    INDEX idx_status (status)
);

-- Insert default notification templates
INSERT INTO notification_templates (template_name, template_type, subject, sms_content, email_content, is_active) VALUES
('booking_confirmed', 'both', 'Booking Confirmed - AutoCare Services',
 'Your booking #{booking_id} has been confirmed. Workshop: {workshop_name}. Date: {date}',
 '<h2>Booking Confirmed</h2><p>Your booking #{booking_id} has been confirmed.</p><p><strong>Workshop:</strong> {workshop_name}</p><p><strong>Date:</strong> {date}</p><p><strong>Services:</strong> {services}</p>',
 TRUE),
('payment_received', 'both', 'Payment Received - AutoCare Services',
 'Payment of Rs.{amount} received for booking #{booking_id}. Thank you!',
 '<h2>Payment Received</h2><p>Payment of Rs.{amount} has been received for booking #{booking_id}.</p><p><strong>Amount:</strong> Rs.{amount}</p><p><strong>Booking ID:</strong> #{booking_id}</p><p>Thank you for your payment!</p>',
 TRUE),
('service_completed', 'both', 'Service Completed - AutoCare Services',
 'Your vehicle service is completed. Booking #{booking_id}. Please collect your vehicle.',
 '<h2>Service Completed</h2><p>Your vehicle service has been completed.</p><p><strong>Booking ID:</strong> #{booking_id}</p><p><strong>Workshop:</strong> {workshop_name}</p><p>Please collect your vehicle at your earliest convenience.</p>',
 TRUE),
('service_reminder', 'both', 'Service Reminder - AutoCare Services',
 'Reminder: Your vehicle service is due. Book now to avoid inconvenience.',
 '<h2>Service Reminder</h2><p>This is a reminder that your vehicle service is due.</p><p><strong>Vehicle:</strong> {vehicle_info}</p><p><strong>Service Type:</strong> {service_type}</p><p>Book your service now to avoid any inconvenience.</p>',
 TRUE)
ON DUPLICATE KEY UPDATE
    template_name = VALUES(template_name),
    subject = VALUES(subject),
    sms_content = VALUES(sms_content),
    email_content = VALUES(email_content),
    is_active = VALUES(is_active);

-- Insert default payment gateway configuration
INSERT INTO payment_config (gateway_name, gateway_type, is_active, test_mode) VALUES
('razorpay', 'razorpay', TRUE, TRUE)
ON DUPLICATE KEY UPDATE
    gateway_name = VALUES(gateway_name),
    gateway_type = VALUES(gateway_type),
    is_active = VALUES(is_active),
    test_mode = VALUES(test_mode);