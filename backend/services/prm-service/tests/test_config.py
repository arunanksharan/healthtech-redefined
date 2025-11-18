"""
Test configuration and constants
"""
from datetime import datetime, timedelta

# Test Organization
TEST_ORG_NAME = "Test Healthcare Org"
TEST_ORG_TYPE = "hospital"

# Test Patient
TEST_PATIENT_FIRST_NAME = "John"
TEST_PATIENT_LAST_NAME = "Doe"
TEST_PATIENT_PHONE = "+12345678901"
TEST_PATIENT_EMAIL = "john.doe@example.com"

# Test Practitioner
TEST_DOCTOR_NAME = "Dr. Smith"
TEST_DOCTOR_SPECIALTY = "General Practice"

# Test Communication
TEST_WHATSAPP_NUMBER = "+12345678901"
TEST_SMS_NUMBER = "+12345678901"
TEST_EMAIL_ADDRESS = "patient@example.com"

# Test Appointment
TEST_APPOINTMENT_DURATION = timedelta(minutes=30)
TEST_APPOINTMENT_TYPE = "consultation"

# Test Journey
TEST_JOURNEY_NAME = "Patient Onboarding"

# Test Ticket
TEST_TICKET_TITLE = "Test Support Ticket"
TEST_TICKET_CATEGORY = "inquiry"

# Test Intake
TEST_CHIEF_COMPLAINT = "Headache"
TEST_SYMPTOM = "Persistent headache"

# API Endpoints
API_PREFIX = "/api/v1/prm"

# Test Timeouts
SHORT_TIMEOUT = 1  # 1 second
MEDIUM_TIMEOUT = 5  # 5 seconds
LONG_TIMEOUT = 30  # 30 seconds

# Test Retries
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Mock Data Sizes
SMALL_DATASET = 10
MEDIUM_DATASET = 100
LARGE_DATASET = 1000
