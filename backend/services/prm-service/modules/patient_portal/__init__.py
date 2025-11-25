"""
Patient Portal Platform Module
EPIC-014: Comprehensive patient self-service portal

This module provides a complete patient portal platform including:

1. User Authentication & Security
   - Email/password registration with identity verification
   - Multi-factor authentication (TOTP, SMS, Email)
   - JWT token-based session management
   - Account lockout and security policies
   - SSO integration support

2. Patient Profile Management
   - View and update personal information
   - Emergency contact management
   - Insurance information
   - Communication preferences

3. Health Records Access
   - View medical records, lab results, and imaging
   - Download records in multiple formats (PDF, JSON, XML, CCD)
   - Share records via secure links
   - Track record access history (HIPAA compliant)

4. Appointment Management
   - Search available slots by provider/specialty
   - Book, reschedule, and cancel appointments
   - Pre-visit questionnaires
   - Online check-in
   - Telehealth integration

5. Secure Messaging
   - Send and receive messages with care team
   - Message threading and history
   - File attachments
   - SLA tracking for response times
   - Auto-response configuration

6. Billing & Payments
   - View statements and balances
   - Saved payment methods
   - Process payments (Stripe integration)
   - Payment plans with auto-pay
   - Payment history and receipts

7. Prescription Management
   - View active prescriptions
   - Request refills
   - Track refill status
   - Medication adherence logging
   - Pharmacy management

8. Proxy Access (Family/Caregiver)
   - Grant access to family members
   - Configurable permission levels
   - Time-limited access support
   - Minor child automatic access
   - Audit trail for proxy actions

9. Notifications
   - In-app notifications
   - Email, SMS, push notification preferences
   - Real-time notification delivery

10. Dashboard & Analytics
    - Personalized health dashboard
    - Health metrics trending
    - Quick actions
    - Care gaps alerts

Key Features:
- HIPAA-compliant audit logging
- Multi-tenant architecture
- WCAG 2.1 AA accessibility support
- Mobile-responsive design (PWA ready)
- 15+ language support structure
"""

from modules.patient_portal.router import router
from modules.patient_portal.services import (
    AuthService,
    PatientPortalService,
    BillingService,
    PrescriptionService,
)
from modules.patient_portal.schemas import (
    # Auth
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    RefreshTokenRequest, TokenResponse,
    PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm,
    MFASetupRequest, MFASetupResponse, MFAVerifyRequest,
    # Profile
    PortalUserResponse, ProfileUpdateRequest,
    PatientProfileResponse, PatientProfileUpdateRequest,
    EmergencyContact,
    # Preferences
    PortalPreferencesResponse, PortalPreferencesUpdate,
    AccessibilitySettings, NotificationSettings, PrivacySettings,
    CommunicationPreferences,
    # Health Records
    HealthRecordResponse, LabResultResponse, HealthSummaryResponse,
    HealthMetrics, RecordFilter,
    RecordDownloadRequest, RecordShareRequest, RecordShareResponse,
    # Appointments
    AppointmentSlot, AppointmentSearchRequest, AppointmentSearchResponse,
    AppointmentBookRequest, AppointmentResponse,
    AppointmentRescheduleRequest, AppointmentCancelRequest,
    # Messaging
    MessageThreadCreate, MessageThreadResponse,
    MessageCreate, MessageResponse,
    MessageListResponse, MessageSearchRequest,
    # Billing
    BillingSummaryResponse, BillingStatementResponse,
    PaymentMethodCreate, PaymentMethodResponse,
    PaymentRequest, PaymentResponse,
    PaymentPlanRequest, PaymentPlanResponse,
    PaymentHistoryResponse,
    # Prescriptions
    PrescriptionResponse,
    RefillRequest, RefillResponse,
    # Proxy Access
    ProxyAccessRequest, ProxyAccessResponse, ProxyAccessUpdate,
    ProxyPatientSummary,
    # Notifications
    NotificationResponse, NotificationListResponse, MarkNotificationsRead,
    # Sessions
    SessionResponse, SessionListResponse, RevokeSessionRequest,
    # Dashboard
    DashboardResponse,
    # Enums
    PortalUserStatusEnum, MFAMethodEnum, ProxyRelationshipEnum,
    ProxyAccessLevelEnum, MessageFolderEnum, MessagePriorityEnum,
    PaymentMethodEnum, PaymentStatusEnum, RefillStatusEnum,
)
from modules.patient_portal.models import (
    # Enums
    PortalUserStatus, MFAMethod, SessionStatus,
    ProxyRelationship, ProxyAccessLevel,
    MessageFolder, MessagePriority, MessageStatus,
    AuditAction, PaymentMethod, PaymentStatus, RefillStatus,
    VerificationType,
    # Models
    PortalUser, PortalSession, PortalPreference,
    ProxyAccess, MessageThread, SecureMessage, MessageAttachmentPortal,
    SavedPaymentMethod, PortalPayment, PaymentPlan,
    RefillRequest as RefillRequestModel,
    PortalNotification, RecordAccessLog, RecordShareLink,
    PortalAuditLog, IdentityVerification,
)

__all__ = [
    # Router
    "router",
    # Services
    "AuthService",
    "PatientPortalService",
    "BillingService",
    "PrescriptionService",
    # Auth Schemas
    "RegisterRequest", "RegisterResponse",
    "LoginRequest", "LoginResponse",
    "RefreshTokenRequest", "TokenResponse",
    "PasswordChangeRequest", "PasswordResetRequest", "PasswordResetConfirm",
    "MFASetupRequest", "MFASetupResponse", "MFAVerifyRequest",
    # Profile Schemas
    "PortalUserResponse", "ProfileUpdateRequest",
    "PatientProfileResponse", "PatientProfileUpdateRequest",
    "EmergencyContact",
    # Preference Schemas
    "PortalPreferencesResponse", "PortalPreferencesUpdate",
    "AccessibilitySettings", "NotificationSettings", "PrivacySettings",
    "CommunicationPreferences",
    # Health Record Schemas
    "HealthRecordResponse", "LabResultResponse", "HealthSummaryResponse",
    "HealthMetrics", "RecordFilter",
    "RecordDownloadRequest", "RecordShareRequest", "RecordShareResponse",
    # Appointment Schemas
    "AppointmentSlot", "AppointmentSearchRequest", "AppointmentSearchResponse",
    "AppointmentBookRequest", "AppointmentResponse",
    "AppointmentRescheduleRequest", "AppointmentCancelRequest",
    # Messaging Schemas
    "MessageThreadCreate", "MessageThreadResponse",
    "MessageCreate", "MessageResponse",
    "MessageListResponse", "MessageSearchRequest",
    # Billing Schemas
    "BillingSummaryResponse", "BillingStatementResponse",
    "PaymentMethodCreate", "PaymentMethodResponse",
    "PaymentRequest", "PaymentResponse",
    "PaymentPlanRequest", "PaymentPlanResponse",
    "PaymentHistoryResponse",
    # Prescription Schemas
    "PrescriptionResponse", "RefillRequest", "RefillResponse",
    # Proxy Access Schemas
    "ProxyAccessRequest", "ProxyAccessResponse", "ProxyAccessUpdate",
    "ProxyPatientSummary",
    # Notification Schemas
    "NotificationResponse", "NotificationListResponse", "MarkNotificationsRead",
    # Session Schemas
    "SessionResponse", "SessionListResponse", "RevokeSessionRequest",
    # Dashboard Schema
    "DashboardResponse",
    # Schema Enums
    "PortalUserStatusEnum", "MFAMethodEnum", "ProxyRelationshipEnum",
    "ProxyAccessLevelEnum", "MessageFolderEnum", "MessagePriorityEnum",
    "PaymentMethodEnum", "PaymentStatusEnum", "RefillStatusEnum",
    # Model Enums
    "PortalUserStatus", "MFAMethod", "SessionStatus",
    "ProxyRelationship", "ProxyAccessLevel",
    "MessageFolder", "MessagePriority", "MessageStatus",
    "AuditAction", "PaymentMethod", "PaymentStatus", "RefillStatus",
    "VerificationType",
    # Models
    "PortalUser", "PortalSession", "PortalPreference",
    "ProxyAccess", "MessageThread", "SecureMessage", "MessageAttachmentPortal",
    "SavedPaymentMethod", "PortalPayment", "PaymentPlan",
    "RefillRequestModel",
    "PortalNotification", "RecordAccessLog", "RecordShareLink",
    "PortalAuditLog", "IdentityVerification",
]
