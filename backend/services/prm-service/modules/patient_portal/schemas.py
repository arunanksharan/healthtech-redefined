"""
Patient Portal Platform - Pydantic Schemas
EPIC-014: Request/Response schemas for Patient Portal API
"""
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


# ==================== Enums ====================

class PortalUserStatusEnum(str, Enum):
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    DEACTIVATED = "deactivated"


class MFAMethodEnum(str, Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BIOMETRIC = "biometric"
    BACKUP_CODE = "backup_code"


class ProxyRelationshipEnum(str, Enum):
    PARENT = "parent"
    GUARDIAN = "guardian"
    SPOUSE = "spouse"
    CHILD = "child"
    CAREGIVER = "caregiver"
    POWER_OF_ATTORNEY = "power_of_attorney"
    HEALTHCARE_PROXY = "healthcare_proxy"
    OTHER = "other"


class ProxyAccessLevelEnum(str, Enum):
    FULL = "full"
    READ_ONLY = "read_only"
    APPOINTMENTS_ONLY = "appointments_only"
    MESSAGES_ONLY = "messages_only"
    BILLING_ONLY = "billing_only"
    CUSTOM = "custom"


class MessageFolderEnum(str, Enum):
    INBOX = "inbox"
    SENT = "sent"
    DRAFTS = "drafts"
    ARCHIVED = "archived"
    TRASH = "trash"


class MessagePriorityEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class PaymentMethodEnum(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ACH = "ach"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    HSA = "hsa"
    FSA = "fsa"


class PaymentStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class RefillStatusEnum(str, Enum):
    REQUESTED = "requested"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DENIED = "denied"
    PROCESSING = "processing"
    READY_FOR_PICKUP = "ready_for_pickup"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ==================== Base Schemas ====================

class BaseSchema(BaseModel):
    """Base schema with common config"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ==================== Authentication Schemas ====================

class RegisterRequest(BaseModel):
    """Patient portal registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')

    # Identity verification
    mrn: Optional[str] = None  # Medical record number
    ssn_last_four: Optional[str] = Field(None, min_length=4, max_length=4)

    # Consent
    accept_terms: bool = Field(..., description="Must accept terms of service")
    accept_privacy: bool = Field(..., description="Must accept privacy policy")

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v


class RegisterResponse(BaseSchema):
    """Registration response"""
    user_id: UUID
    email: str
    status: PortalUserStatusEnum
    verification_required: bool
    verification_method: str
    message: str


class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str
    mfa_code: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    remember_me: bool = False


class LoginResponse(BaseSchema):
    """Login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_mfa: bool = False
    mfa_method: Optional[MFAMethodEnum] = None
    user: Optional["PortalUserResponse"] = None


class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class TokenResponse(BaseSchema):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordResetRequest(BaseModel):
    """Password reset initiation request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str


class MFASetupRequest(BaseModel):
    """MFA setup request"""
    method: MFAMethodEnum
    phone_number: Optional[str] = None  # Required for SMS method


class MFASetupResponse(BaseSchema):
    """MFA setup response"""
    method: MFAMethodEnum
    secret: Optional[str] = None  # For TOTP
    qr_code_url: Optional[str] = None  # For TOTP
    backup_codes: Optional[List[str]] = None
    verification_required: bool = True


class MFAVerifyRequest(BaseModel):
    """MFA verification request"""
    code: str = Field(..., min_length=6, max_length=8)


class VerifyEmailRequest(BaseModel):
    """Email verification request"""
    token: str


class VerifyPhoneRequest(BaseModel):
    """Phone verification request"""
    code: str = Field(..., min_length=4, max_length=8)


class SendVerificationRequest(BaseModel):
    """Send verification code request"""
    method: str = Field(..., pattern="^(email|sms)$")


# ==================== User Profile Schemas ====================

class PortalUserResponse(BaseSchema, TimestampMixin):
    """Portal user response"""
    id: UUID
    patient_id: UUID
    email: str
    status: PortalUserStatusEnum
    email_verified: bool
    phone_number: Optional[str] = None
    phone_verified: bool
    mfa_enabled: bool
    mfa_method: Optional[MFAMethodEnum] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_language: str
    timezone: str
    last_login_at: Optional[datetime] = None
    terms_accepted: bool
    privacy_accepted: bool


class ProfileUpdateRequest(BaseModel):
    """Profile update request"""
    display_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    preferred_language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)


class EmergencyContact(BaseModel):
    """Emergency contact info"""
    name: str
    relationship: str
    phone: str
    email: Optional[EmailStr] = None
    is_primary: bool = False


class PatientProfileResponse(BaseSchema):
    """Complete patient profile for portal"""
    id: UUID
    mrn: Optional[str] = None
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    date_of_birth: date
    gender: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    emergency_contacts: Optional[List[EmergencyContact]] = None
    insurance_info: Optional[Dict[str, Any]] = None
    preferred_language: Optional[str] = None
    preferred_pharmacy: Optional[Dict[str, Any]] = None
    photo_url: Optional[str] = None

    # Summary stats
    total_appointments: Optional[int] = None
    active_medications: Optional[int] = None
    active_allergies: Optional[int] = None
    last_visit_date: Optional[date] = None


class PatientProfileUpdateRequest(BaseModel):
    """Patient profile update request"""
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[Dict[str, Any]] = None
    emergency_contacts: Optional[List[EmergencyContact]] = None
    preferred_language: Optional[str] = None
    communication_preferences: Optional[Dict[str, Any]] = None


# ==================== Preferences Schemas ====================

class AccessibilitySettings(BaseModel):
    """Accessibility settings"""
    font_size: str = "medium"  # small, medium, large, x-large
    high_contrast: bool = False
    screen_reader_optimized: bool = False
    reduce_motion: bool = False
    color_blind_mode: Optional[str] = None  # protanopia, deuteranopia, tritanopia


class NotificationSettings(BaseModel):
    """Notification settings"""
    email_enabled: bool = True
    sms_enabled: bool = True
    push_enabled: bool = True
    appointment_reminders: bool = True
    appointment_reminder_hours: List[int] = [24, 2]
    lab_results_available: bool = True
    new_messages: bool = True
    billing_notifications: bool = True
    prescription_ready: bool = True
    health_tips: bool = False
    marketing: bool = False


class DashboardWidget(BaseModel):
    """Dashboard widget configuration"""
    id: str
    position: int
    visible: bool = True


class PrivacySettings(BaseModel):
    """Privacy settings"""
    show_photo: bool = True
    share_health_data_research: bool = False
    allow_care_team_access: bool = True


class CommunicationPreferences(BaseModel):
    """Communication preferences"""
    preferred_contact_method: str = "email"
    appointment_confirmation: str = "email"
    lab_results_notification: str = "email"
    billing_statements: str = "email"
    do_not_disturb_start: Optional[time] = None
    do_not_disturb_end: Optional[time] = None


class PortalPreferencesResponse(BaseSchema):
    """Portal preferences response"""
    language: str
    timezone: str
    date_format: str
    time_format: str
    theme: str
    accessibility_settings: AccessibilitySettings
    notification_settings: NotificationSettings
    dashboard_layout: Dict[str, Any]
    privacy_settings: PrivacySettings
    communication_preferences: CommunicationPreferences
    favorite_actions: List[str]
    onboarding_completed: bool
    tour_completed: bool


class PortalPreferencesUpdate(BaseModel):
    """Portal preferences update request"""
    language: Optional[str] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    theme: Optional[str] = None
    accessibility_settings: Optional[AccessibilitySettings] = None
    notification_settings: Optional[NotificationSettings] = None
    dashboard_layout: Optional[Dict[str, Any]] = None
    privacy_settings: Optional[PrivacySettings] = None
    communication_preferences: Optional[CommunicationPreferences] = None
    favorite_actions: Optional[List[str]] = None


# ==================== Health Records Schemas ====================

class RecordFilter(BaseModel):
    """Health record filter"""
    record_type: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    provider_id: Optional[UUID] = None
    search: Optional[str] = None


class HealthRecordResponse(BaseSchema):
    """Health record response"""
    id: UUID
    record_type: str
    encounter_id: Optional[UUID] = None
    provider_name: Optional[str] = None
    record_date: datetime
    title: str
    content: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    is_sensitive: bool = False
    visit_type: Optional[str] = None
    facility_name: Optional[str] = None
    created_at: datetime


class LabResultResponse(BaseSchema):
    """Lab result response"""
    id: UUID
    test_name: str
    test_code: Optional[str] = None
    result_value: str
    result_unit: Optional[str] = None
    reference_range: Optional[str] = None
    abnormal_flag: Optional[str] = None
    result_date: datetime
    ordering_provider: Optional[str] = None
    performing_lab: Optional[str] = None
    status: str
    comments: Optional[str] = None
    previous_value: Optional[str] = None
    previous_date: Optional[datetime] = None
    trend: Optional[str] = None  # up, down, stable
    in_range: bool = True


class HealthMetrics(BaseModel):
    """Health metrics summary"""
    overall_score: Optional[float] = None
    blood_pressure: Optional[str] = None
    bp_trend: Optional[str] = None
    blood_sugar: Optional[float] = None
    sugar_trend: Optional[str] = None
    weight: Optional[float] = None
    weight_trend: Optional[str] = None
    bmi: Optional[float] = None
    heart_rate: Optional[int] = None
    last_updated: Optional[datetime] = None


class HealthSummaryResponse(BaseSchema):
    """Health summary response"""
    patient_id: UUID
    metrics: HealthMetrics
    allergies: List[Dict[str, Any]]
    conditions: List[Dict[str, Any]]
    medications: List[Dict[str, Any]]
    immunizations: List[Dict[str, Any]]
    care_gaps: List[Dict[str, Any]]
    preventive_care_due: List[Dict[str, Any]]


class RecordDownloadRequest(BaseModel):
    """Record download request"""
    record_ids: List[UUID]
    format: str = Field(..., pattern="^(pdf|json|xml|ccd)$")
    include_attachments: bool = False
    date_range_label: Optional[str] = None


class RecordShareRequest(BaseModel):
    """Record share request"""
    record_type: Optional[str] = None
    record_ids: Optional[List[UUID]] = None
    recipient_name: str
    recipient_email: EmailStr
    recipient_organization: Optional[str] = None
    purpose: str
    include_attachments: bool = False
    password_protected: bool = True
    expires_in_days: int = Field(7, ge=1, le=90)
    max_access_count: Optional[int] = Field(None, ge=1, le=100)


class RecordShareResponse(BaseSchema):
    """Record share response"""
    share_id: UUID
    share_url: str
    expires_at: datetime
    password: Optional[str] = None  # Only returned if password_protected
    notification_sent: bool


# ==================== Appointment Schemas ====================

class AppointmentSlot(BaseModel):
    """Available appointment slot"""
    datetime: datetime
    duration: int
    provider_id: UUID
    provider_name: str
    specialty: str
    location: Optional[str] = None
    telehealth_available: bool = False
    new_patient_available: bool = True


class AppointmentSearchRequest(BaseModel):
    """Appointment availability search"""
    provider_id: Optional[UUID] = None
    specialty: Optional[str] = None
    date_from: date
    date_to: date
    appointment_type: str
    telehealth_only: bool = False
    location_id: Optional[UUID] = None


class AppointmentSearchResponse(BaseSchema):
    """Appointment search response"""
    available_slots: List[AppointmentSlot]
    total_count: int


class AppointmentBookRequest(BaseModel):
    """Book appointment request"""
    provider_id: UUID
    datetime: datetime
    appointment_type: str
    duration: Optional[int] = 30
    location_id: Optional[UUID] = None
    reason: Optional[str] = Field(None, max_length=500)
    telehealth: bool = False
    notes: Optional[str] = Field(None, max_length=1000)

    # For proxy bookings
    on_behalf_of_patient_id: Optional[UUID] = None


class AppointmentResponse(BaseSchema, TimestampMixin):
    """Appointment response"""
    id: UUID
    patient_id: UUID
    provider_id: UUID
    provider_name: str
    specialty: Optional[str] = None
    appointment_datetime: datetime
    appointment_type: str
    duration_minutes: int
    location: Optional[str] = None
    room: Optional[str] = None
    reason_for_visit: Optional[str] = None
    status: str
    telehealth: bool
    telehealth_link: Optional[str] = None
    check_in_available: bool = False
    check_in_at: Optional[datetime] = None
    preparation_instructions: Optional[str] = None
    cancellation_reason: Optional[str] = None


class AppointmentRescheduleRequest(BaseModel):
    """Reschedule appointment request"""
    new_datetime: datetime
    reason: Optional[str] = None


class AppointmentCancelRequest(BaseModel):
    """Cancel appointment request"""
    reason: str = Field(..., min_length=1, max_length=500)
    request_reschedule: bool = False


class AppointmentCheckInRequest(BaseModel):
    """Check-in for appointment"""
    location_confirmed: bool = True
    insurance_confirmed: bool = True
    questionnaire_completed: bool = False
    signature_provided: bool = False


# ==================== Messaging Schemas ====================

class MessageThreadCreate(BaseModel):
    """Create message thread"""
    subject: str = Field(..., min_length=1, max_length=255)
    recipient_id: UUID  # Provider ID
    category: Optional[str] = None
    is_urgent: bool = False
    initial_message: str = Field(..., min_length=1, max_length=10000)

    # Related context
    related_appointment_id: Optional[UUID] = None


class MessageThreadResponse(BaseSchema, TimestampMixin):
    """Message thread response"""
    id: UUID
    subject: str
    category: Optional[str] = None
    provider_id: Optional[UUID] = None
    provider_name: Optional[str] = None
    department: Optional[str] = None
    is_open: bool
    is_urgent: bool
    message_count: int
    unread_count: int
    last_message_at: Optional[datetime] = None
    response_due_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class MessageCreate(BaseModel):
    """Create/reply to message"""
    content: str = Field(..., min_length=1, max_length=10000)
    priority: MessagePriorityEnum = MessagePriorityEnum.NORMAL


class MessageResponse(BaseSchema, TimestampMixin):
    """Message response"""
    id: UUID
    thread_id: UUID
    sender_type: str
    sender_name: str
    content: str
    has_attachments: bool
    attachment_count: int
    priority: MessagePriorityEnum
    status: str
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    is_auto_response: bool


class MessageAttachmentUpload(BaseModel):
    """Message attachment upload metadata"""
    file_name: str
    file_type: str
    file_size: int


class MessageListResponse(BaseSchema):
    """Message list response"""
    threads: List[MessageThreadResponse]
    total_count: int
    unread_count: int


class MessageSearchRequest(BaseModel):
    """Search messages"""
    query: Optional[str] = None
    folder: Optional[MessageFolderEnum] = None
    provider_id: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    is_unread: Optional[bool] = None
    is_urgent: Optional[bool] = None


# ==================== Billing Schemas ====================

class BillingStatementResponse(BaseSchema):
    """Billing statement response"""
    id: UUID
    statement_date: date
    due_date: date
    total_amount: float
    paid_amount: float
    balance_due: float
    status: str
    items: List[Dict[str, Any]]
    insurance_applied: bool
    download_url: Optional[str] = None


class BillingSummaryResponse(BaseSchema):
    """Billing summary response"""
    current_balance: float
    total_due: float
    past_due_amount: float
    last_payment_date: Optional[date] = None
    last_payment_amount: Optional[float] = None
    payment_plan_active: bool
    statements: List[BillingStatementResponse]


class PaymentMethodCreate(BaseModel):
    """Add payment method"""
    payment_type: PaymentMethodEnum
    nickname: Optional[str] = Field(None, max_length=50)
    is_default: bool = False

    # Card info (tokenized before submission)
    card_token: Optional[str] = None
    card_brand: Optional[str] = None
    card_last_four: Optional[str] = None
    card_exp_month: Optional[int] = None
    card_exp_year: Optional[int] = None
    card_holder_name: Optional[str] = None

    # Bank info (tokenized before submission)
    bank_token: Optional[str] = None
    bank_name: Optional[str] = None
    account_type: Optional[str] = None
    account_last_four: Optional[str] = None

    # Billing address
    billing_address: Optional[Dict[str, Any]] = None


class PaymentMethodResponse(BaseSchema, TimestampMixin):
    """Payment method response"""
    id: UUID
    payment_type: PaymentMethodEnum
    nickname: Optional[str] = None
    is_default: bool
    card_brand: Optional[str] = None
    card_last_four: Optional[str] = None
    card_exp_month: Optional[int] = None
    card_exp_year: Optional[int] = None
    bank_name: Optional[str] = None
    account_type: Optional[str] = None
    account_last_four: Optional[str] = None
    is_active: bool
    is_verified: bool


class PaymentRequest(BaseModel):
    """Make payment request"""
    amount: float = Field(..., gt=0)
    payment_method_id: Optional[UUID] = None

    # One-time payment info
    payment_type: Optional[PaymentMethodEnum] = None
    card_token: Optional[str] = None

    # Allocation
    statement_ids: Optional[List[UUID]] = None
    payment_plan_id: Optional[UUID] = None

    # Save card for future use
    save_payment_method: bool = False


class PaymentResponse(BaseSchema, TimestampMixin):
    """Payment response"""
    id: UUID
    amount: float
    currency: str
    status: PaymentStatusEnum
    confirmation_number: str
    receipt_url: Optional[str] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class PaymentPlanRequest(BaseModel):
    """Setup payment plan"""
    total_amount: float = Field(..., gt=0)
    number_of_payments: int = Field(..., ge=2, le=24)
    start_date: date
    payment_day_of_month: int = Field(..., ge=1, le=28)
    auto_pay_enabled: bool = True
    payment_method_id: Optional[UUID] = None


class PaymentPlanResponse(BaseSchema, TimestampMixin):
    """Payment plan response"""
    id: UUID
    name: Optional[str] = None
    total_amount: float
    remaining_amount: float
    monthly_payment: float
    number_of_payments: int
    payments_made: int
    start_date: date
    next_payment_date: Optional[date] = None
    payment_day_of_month: int
    auto_pay_enabled: bool
    is_active: bool
    status: str


class PaymentHistoryResponse(BaseSchema):
    """Payment history response"""
    payments: List[PaymentResponse]
    total_count: int
    total_paid: float


# ==================== Prescription Schemas ====================

class PrescriptionResponse(BaseSchema):
    """Prescription/medication response"""
    id: UUID
    medication_name: str
    generic_name: Optional[str] = None
    dosage: str
    frequency: str
    instructions: Optional[str] = None
    prescriber_name: str
    prescriber_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool
    refills_remaining: int
    refills_total: int
    last_fill_date: Optional[date] = None
    next_fill_date: Optional[date] = None
    days_supply: Optional[int] = None
    pharmacy_name: Optional[str] = None
    pharmacy_phone: Optional[str] = None
    prior_auth_required: bool = False
    prior_auth_status: Optional[str] = None


class RefillRequest(BaseModel):
    """Request prescription refill"""
    prescription_id: UUID
    quantity_requested: Optional[int] = None
    days_supply_requested: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=500)
    urgent: bool = False

    # Pharmacy
    pharmacy_id: Optional[UUID] = None
    delivery_requested: bool = False
    delivery_address: Optional[Dict[str, Any]] = None


class RefillResponse(BaseSchema, TimestampMixin):
    """Refill request response"""
    id: UUID
    prescription_id: UUID
    medication_name: str
    medication_dosage: Optional[str] = None
    status: RefillStatusEnum
    pharmacy_name: Optional[str] = None
    delivery_requested: bool
    tracking_number: Optional[str] = None
    estimated_cost: Optional[float] = None
    copay_amount: Optional[float] = None
    ready_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    denial_reason: Optional[str] = None
    requires_appointment: bool


class MedicationAdherenceLog(BaseModel):
    """Log medication adherence"""
    prescription_id: UUID
    taken_at: datetime
    taken: bool = True
    notes: Optional[str] = None


# ==================== Proxy Access Schemas ====================

class ProxyAccessRequest(BaseModel):
    """Request proxy access"""
    grantee_email: EmailStr
    relationship_type: ProxyRelationshipEnum
    relationship_description: Optional[str] = None
    access_level: ProxyAccessLevelEnum

    # Custom permissions (for CUSTOM access level)
    custom_permissions: Optional[Dict[str, bool]] = None

    # Permission flags
    can_view_records: bool = True
    can_download_records: bool = False
    can_book_appointments: bool = True
    can_send_messages: bool = True
    can_view_billing: bool = True
    can_make_payments: bool = False
    can_request_refills: bool = True

    # Validity
    valid_until: Optional[date] = None
    is_permanent: bool = False


class ProxyAccessResponse(BaseSchema, TimestampMixin):
    """Proxy access response"""
    id: UUID
    grantor_name: str
    grantee_name: str
    relationship_type: ProxyRelationshipEnum
    access_level: ProxyAccessLevelEnum

    # Permissions
    can_view_records: bool
    can_download_records: bool
    can_book_appointments: bool
    can_send_messages: bool
    can_view_billing: bool
    can_make_payments: bool
    can_request_refills: bool

    # Status
    is_active: bool
    verified: bool
    valid_from: datetime
    valid_until: Optional[datetime] = None
    is_permanent: bool


class ProxyAccessUpdate(BaseModel):
    """Update proxy access"""
    access_level: Optional[ProxyAccessLevelEnum] = None
    can_view_records: Optional[bool] = None
    can_download_records: Optional[bool] = None
    can_book_appointments: Optional[bool] = None
    can_send_messages: Optional[bool] = None
    can_view_billing: Optional[bool] = None
    can_make_payments: Optional[bool] = None
    can_request_refills: Optional[bool] = None
    valid_until: Optional[date] = None


class ProxyAccessRevoke(BaseModel):
    """Revoke proxy access"""
    reason: Optional[str] = None


class ProxyPatientSummary(BaseSchema):
    """Summary for proxy patient view"""
    patient_id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    relationship: ProxyRelationshipEnum
    access_level: ProxyAccessLevelEnum
    photo_url: Optional[str] = None

    # Quick stats
    upcoming_appointments: int
    unread_messages: int
    pending_refills: int


# ==================== Notification Schemas ====================

class NotificationResponse(BaseSchema):
    """Notification response"""
    id: UUID
    notification_type: str
    title: str
    message: str
    icon: Optional[str] = None
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    priority: str
    is_urgent: bool
    is_read: bool
    read_at: Optional[datetime] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    created_at: datetime


class NotificationListResponse(BaseSchema):
    """Notification list response"""
    notifications: List[NotificationResponse]
    total_count: int
    unread_count: int


class MarkNotificationsRead(BaseModel):
    """Mark notifications as read"""
    notification_ids: Optional[List[UUID]] = None
    mark_all: bool = False


# ==================== Session Schemas ====================

class SessionResponse(BaseSchema):
    """Active session response"""
    id: UUID
    device_type: Optional[str] = None
    device_name: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    is_current: bool
    created_at: datetime
    last_activity_at: datetime


class SessionListResponse(BaseSchema):
    """List of active sessions"""
    sessions: List[SessionResponse]
    total_count: int


class RevokeSessionRequest(BaseModel):
    """Revoke session request"""
    session_id: Optional[UUID] = None
    revoke_all_except_current: bool = False


# ==================== Dashboard Schemas ====================

class DashboardResponse(BaseSchema):
    """Main dashboard data"""
    patient: PatientProfileResponse
    health_summary: HealthSummaryResponse
    upcoming_appointments: List[AppointmentResponse]
    medications_due_today: List[PrescriptionResponse]
    unread_messages: int
    billing_summary: BillingSummaryResponse
    notifications: List[NotificationResponse]
    quick_actions: List[str]


# ==================== Pagination ====================

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
