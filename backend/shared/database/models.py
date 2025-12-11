"""
Core database models for the healthcare platform
SQLAlchemy ORM models representing the complete data schema
"""
from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSON, JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


def generate_uuid() -> uuid.UUID:
    """Generate a new UUID4"""
    return uuid.uuid4()


# ============================================================================
# IDENTITY & CORE ENTITIES
# ============================================================================


class Tenant(Base):
    """Multi-tenancy support for hospital/clinic organizations"""

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    domain = Column(String(255))

    # Configuration
    config = Column(JSONB, nullable=False, default=dict)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class Patient(Base):
    """Patient demographic and contact information"""

    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Demographics
    first_name = Column(String(100))
    last_name = Column(String(100))
    middle_name = Column(String(100))
    date_of_birth = Column(Date)
    gender = Column(String(20))  # male, female, other, unknown

    # Contact Information
    phone_primary = Column(String(20))
    phone_secondary = Column(String(20))
    email_primary = Column(String(255))
    email_secondary = Column(String(255))

    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="India")

    # Additional Demographics
    marital_status = Column(String(20))
    blood_group = Column(String(10))
    language_preferred = Column(String(50))

    # Status
    is_deceased = Column(Boolean, nullable=False, default=False)
    deceased_date = Column(DateTime(timezone=True))

    # FHIR Resource
    fhir_resource = Column(JSONB, nullable=False, default=dict)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    identifiers = relationship(
        "PatientIdentifier", back_populates="patient", cascade="all, delete-orphan"
    )
    consents = relationship(
        "Consent", back_populates="patient", cascade="all, delete-orphan"
    )
    # Phase 2 relationships
    appointments = relationship("Appointment", back_populates="patient")
    encounters = relationship("Encounter", back_populates="patient")
    journey_instances = relationship("JourneyInstance", back_populates="patient")
    communications = relationship("Communication", back_populates="patient")
    tickets = relationship("Ticket", back_populates="patient")

    # Indexes
    __table_args__ = (
        Index("idx_patients_tenant", "tenant_id"),
        Index("idx_patients_phone", "phone_primary"),
        Index("idx_patients_name", "first_name", "last_name"),
        Index("idx_patients_dob", "date_of_birth"),
    )


class PatientIdentifier(Base):
    """Patient identifiers from various systems (MRN, ABHA, National ID, etc.)"""

    __tablename__ = "patient_identifiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Identifier Details
    system = Column(String(100), nullable=False)  # MRN, ABHA, NATIONAL_ID, etc.
    value = Column(String(255), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)

    # Period of validity
    valid_from = Column(DateTime(timezone=True))
    valid_to = Column(DateTime(timezone=True))

    # Relationships
    patient = relationship("Patient", back_populates="identifiers")

    # Indexes
    __table_args__ = (
        Index("uniq_patient_identifier", "system", "value", unique=True),
        Index("idx_patient_identifiers_patient", "patient_id"),
    )


class Practitioner(Base):
    """Healthcare practitioners (doctors, nurses, etc.)"""

    __tablename__ = "practitioners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Demographics
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    gender = Column(String(20))

    # Professional Information
    qualification = Column(String(255))
    speciality = Column(String(100))
    sub_speciality = Column(String(100))
    license_number = Column(String(100))
    registration_number = Column(String(100))

    # Contact
    phone_primary = Column(String(20))
    email_primary = Column(String(255))

    # FHIR Resource
    fhir_resource = Column(JSONB, nullable=False, default=dict)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    # Phase 2 relationships
    schedules = relationship("ProviderSchedule", back_populates="practitioner")

    # Indexes
    __table_args__ = (
        Index("idx_practitioners_tenant", "tenant_id"),
        Index("idx_practitioners_speciality", "speciality"),
        Index("idx_practitioners_active", "is_active"),
    )


class Organization(Base):
    """Healthcare organizations (hospitals, clinics, labs, etc.)"""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Basic Information
    name = Column(String(255), nullable=False)
    type = Column(String(100))  # hospital, clinic, lab, pharmacy, imaging

    # Contact
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))

    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))

    # FHIR Resource
    fhir_resource = Column(JSONB, nullable=False, default=dict)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Indexes
    __table_args__ = (
        Index("idx_organizations_tenant", "tenant_id"),
        Index("idx_organizations_type", "type"),
    )


class Location(Base):
    """Physical locations (wards, rooms, beds, clinics, departments)"""

    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    parent_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"))

    # Location Details
    name = Column(String(255), nullable=False)
    type = Column(String(100))  # ward, room, bed, clinic, department
    code = Column(String(50))

    # Physical Location
    building = Column(String(100))
    floor = Column(String(50))
    room = Column(String(50))

    # FHIR Resource
    fhir_resource = Column(JSONB, nullable=False, default=dict)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    operational_status = Column(String(50))  # active, suspended, inactive

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    # Phase 2 relationships
    schedules = relationship("ProviderSchedule", back_populates="location")

    # Indexes
    __table_args__ = (
        Index("idx_locations_tenant", "tenant_id"),
        Index("idx_locations_organization", "organization_id"),
        Index("idx_locations_type", "type"),
        Index("idx_locations_parent", "parent_location_id"),
    )


# ============================================================================
# CONSENT & PRIVACY
# ============================================================================


class Consent(Base):
    """Patient consent records for data sharing and usage"""

    __tablename__ = "consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    # Consent Details
    status = Column(
        String(20), nullable=False, default="active"
    )  # active, inactive, draft, rejected
    category = Column(String(50))  # treatment, research, marketing, sharing

    # Scope
    purpose = Column(String(100))  # What the consent is for
    data_types = Column(JSONB, default=list)  # Types of data covered

    # Validity Period
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))

    # Source
    channel = Column(String(50))  # web, whatsapp, phone, in_clinic, email
    note = Column(Text)

    # FHIR Resource
    consent_fhir = Column(JSONB, nullable=False, default=dict)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    patient = relationship("Patient", back_populates="consents")

    # Indexes
    __table_args__ = (
        Index("idx_consents_patient", "patient_id", "status"),
        Index("idx_consents_validity", "valid_from", "valid_until"),
    )


# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================


class User(Base):
    """System users with authentication credentials"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Credentials
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))

    # Links to practitioners/patients
    practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    is_verified = Column(Boolean, nullable=False, default=False)

    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    last_login = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("uniq_users_email_tenant", "tenant_id", "email", unique=True),
        Index("idx_users_practitioner", "practitioner_id"),
        Index("idx_users_patient", "patient_id"),
    )


class Role(Base):
    """User roles for RBAC"""

    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Role Details
    name = Column(String(100), nullable=False)
    description = Column(Text)
    code = Column(String(50))  # ADMIN, DOCTOR, NURSE, RECEPTIONIST

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    permissions = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (Index("idx_roles_tenant", "tenant_id"),)


class Permission(Base):
    """System permissions for RBAC"""

    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)

    # Permission Details
    resource = Column(
        String(100), nullable=False
    )  # patient, appointment, order, encounter
    action = Column(String(50), nullable=False)  # read, write, delete, approve
    scope = Column(String(50))  # own, department, organization, all

    # Description
    description = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("uniq_permission", "resource", "action", "scope", unique=True),
    )


class UserRole(Base):
    """Many-to-many relationship between users and roles"""

    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_id = Column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role")

    # Indexes
    __table_args__ = (
        Index("uniq_user_role", "user_id", "role_id", unique=True),
    )


class RolePermission(Base):
    """Many-to-many relationship between roles and permissions"""

    __tablename__ = "role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    role_id = Column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission")

    # Indexes
    __table_args__ = (
        Index("uniq_role_permission", "role_id", "permission_id", unique=True),
    )


# ============================================================================
# FHIR RESOURCES
# ============================================================================


class FHIRResource(Base):
    """Generic FHIR R4 resource storage with versioning"""

    __tablename__ = "fhir_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Resource Identification
    resource_type = Column(
        String(50), nullable=False
    )  # Patient, Encounter, Observation, etc.
    resource_id = Column(String(100), nullable=False)  # FHIR logical ID
    version = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, nullable=False, default=True)

    # The actual FHIR resource (complete JSON)
    resource = Column(JSONB, nullable=False)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Indexes
    __table_args__ = (
        Index("idx_fhir_resources_tenant_type", "tenant_id", "resource_type"),
        Index("idx_fhir_resources_id_type", "resource_type", "resource_id", "is_current"),
        Index("idx_fhir_resources_current", "is_current"),
    )


# ============================================================================
# EVENT LOG
# ============================================================================


class EventLog(Base):
    """Central event log for all system events"""

    __tablename__ = "event_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Event Details
    event_type = Column(
        String(100), nullable=False
    )  # Patient.Created, Appointment.Booked, etc.
    event_payload = Column(JSONB, nullable=False)

    # Event Source
    source_service = Column(String(100))
    source_user_id = Column(UUID(as_uuid=True))

    # Timestamps
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Processing Status
    processed_by_warehouse = Column(Boolean, nullable=False, default=False)
    processed_at = Column(DateTime(timezone=True))

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_event_log_type_time", "event_type", "occurred_at"),
        Index("idx_event_log_tenant", "tenant_id", "occurred_at"),
        Index("idx_event_log_processed", "processed_by_warehouse"),
    )


class StoredEvent(Base):
    """
    Event store for event sourcing pattern
    Stores domain events for aggregate reconstruction and event replay
    """

    __tablename__ = "stored_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Aggregate Information
    aggregate_type = Column(String(100), nullable=False)  # Patient, Appointment, Order, etc.
    aggregate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    version = Column(Integer, nullable=False)  # Version of aggregate when event occurred

    # Event Details
    event_type = Column(String(100), nullable=False)  # Patient.Created, etc.
    event_data = Column(JSONB, nullable=False)  # Event payload

    # Metadata
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    meta_data = Column(JSONB, default=dict)

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_stored_events_aggregate", "aggregate_id", "version"),
        Index("idx_stored_events_type", "event_type", "occurred_at"),
        Index("idx_stored_events_tenant", "tenant_id", "occurred_at"),
        # Unique constraint to prevent duplicate versions
        Index("idx_stored_events_unique_version", "aggregate_id", "version", unique=True),
    )


class AggregateSnapshot(Base):
    """
    Snapshots of aggregate state for performance optimization
    Allows rebuilding aggregates without replaying all events
    """

    __tablename__ = "aggregate_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Aggregate Information
    aggregate_type = Column(String(100), nullable=False)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    version = Column(Integer, nullable=False)  # Version at which snapshot was taken

    # Snapshot Data
    state = Column(JSONB, nullable=False)  # Complete aggregate state

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_aggregate_snapshots_aggregate", "aggregate_id", "version"),
        Index("idx_aggregate_snapshots_type", "aggregate_type", "created_at"),
    )


class FailedEvent(Base):
    """
    Dead Letter Queue for events that failed to process
    Stores failed events for debugging and retry
    """

    __tablename__ = "failed_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Original Event Information
    event_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    event_payload = Column(JSONB, nullable=False)

    # Failure Information
    error_type = Column(String(255), nullable=False)
    error_message = Column(Text)
    retry_count = Column(Integer, nullable=False, default=0)
    failed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Retry Status
    retried = Column(Boolean, nullable=False, default=False)
    retried_at = Column(DateTime(timezone=True))
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime(timezone=True))

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Indexes
    __table_args__ = (
        Index("idx_failed_events_type", "event_type", "failed_at"),
        Index("idx_failed_events_status", "resolved", "failed_at"),
        Index("idx_failed_events_tenant", "tenant_id", "failed_at"),
    )


# ============================================================================
# PHASE 2: SCHEDULING & APPOINTMENTS
# ============================================================================


class ProviderSchedule(Base):
    """Provider schedule templates for recurring availability"""

    __tablename__ = "provider_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)

    specialty_code = Column(String(100))
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date)

    # Recurring schedule
    day_of_week = Column(SmallInteger, nullable=False)  # 1=Mon, 7=Sun
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(Integer, nullable=False)
    max_patients_per_slot = Column(Integer, nullable=False, default=1)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    practitioner = relationship("Practitioner", back_populates="schedules")
    location = relationship("Location", back_populates="schedules")
    slots = relationship("TimeSlot", back_populates="schedule", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_schedules_practitioner", "practitioner_id", "is_active"),
        Index("idx_schedules_location", "location_id"),
    )


class TimeSlot(Base):
    """Materialized appointment slots"""

    __tablename__ = "time_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("provider_schedules.id", ondelete="CASCADE"), nullable=False)

    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)

    capacity = Column(Integer, nullable=False, default=1)
    booked_count = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="available")  # available, full, blocked

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    schedule = relationship("ProviderSchedule", back_populates="slots")
    practitioner = relationship("Practitioner")
    location = relationship("Location")
    appointments = relationship("Appointment", back_populates="time_slot")

    # Indexes
    __table_args__ = (
        Index("idx_timeslots_practitioner_time", "practitioner_id", "start_datetime", "end_datetime"),
        Index("idx_timeslots_location_time", "location_id", "start_datetime", "end_datetime"),
    )


class Appointment(Base):
    """Patient appointments"""

    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    time_slot_id = Column(UUID(as_uuid=True), ForeignKey("time_slots.id"), nullable=False)

    appointment_type = Column(String(50))  # new, followup, procedure
    status = Column(String(50), nullable=False)  # booked, checked_in, cancelled, no_show, completed
    reason_text = Column(Text)
    source_channel = Column(String(50))  # web, whatsapp, callcenter

    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    meta_data = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    practitioner = relationship("Practitioner")
    location = relationship("Location")
    time_slot = relationship("TimeSlot", back_populates="appointments")
    encounter = relationship("Encounter", back_populates="appointment", uselist=False)

    # Indexes
    __table_args__ = (
        Index("idx_appointments_patient", "patient_id", "created_at"),
        Index("idx_appointments_practitioner_time", "practitioner_id", "status", "time_slot_id"),
    )


# ============================================================================
# PHASE 2: ENCOUNTERS (OPD)
# ============================================================================


class Encounter(Base):
    """Clinical encounters"""

    __tablename__ = "encounters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    encounter_fhir_id = Column(String(255), nullable=False)  # FHIR Encounter.id
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"), nullable=False)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"))

    status = Column(String(50), nullable=False)  # planned, in-progress, completed, cancelled
    class_code = Column(String(50), nullable=False, default="AMB")  # AMB=outpatient

    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="encounters")
    practitioner = relationship("Practitioner")
    appointment = relationship("Appointment", back_populates="encounter")

    # Indexes
    __table_args__ = (
        Index("uniq_encounter_fhir", "tenant_id", "encounter_fhir_id", unique=True),
        Index("idx_encounters_patient", "patient_id", "started_at"),
        Index("idx_encounters_practitioner", "practitioner_id", "started_at"),
    )


# ============================================================================
# PHASE 2: PRM (Patient Relationship Management)
# ============================================================================


class Journey(Base):
    """Journey definitions (PRM programs)"""

    __tablename__ = "journeys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # CARDIO_NEW_OPD
    name = Column(String(255), nullable=False)
    description = Column(Text)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stages = relationship("JourneyStage", back_populates="journey", cascade="all, delete-orphan")
    instances = relationship("JourneyInstance", back_populates="journey")

    # Indexes
    __table_args__ = (Index("uniq_journey_code_tenant", "tenant_id", "code", unique=True),)


class JourneyStage(Base):
    """Stages within a journey"""

    __tablename__ = "journey_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    journey_id = Column(UUID(as_uuid=True), ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    code = Column(String(100), nullable=False)  # PRE_VISIT, DAY_OF_VISIT
    name = Column(String(255), nullable=False)
    description = Column(Text)

    entry_event_type = Column(String(100))  # Appointment.Created
    exit_event_type = Column(String(100))
    auto_advance = Column(Boolean, nullable=False, default=False)

    config = Column(JSONB, default=dict)  # days_before_visit, templates, etc.

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    journey = relationship("Journey", back_populates="stages")

    # Indexes
    __table_args__ = (Index("idx_journey_stages_journey", "journey_id", "sequence"),)


class JourneyInstance(Base):
    """Patient journey instances"""

    __tablename__ = "journey_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    journey_id = Column(UUID(as_uuid=True), ForeignKey("journeys.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    episode_of_care_fhir_id = Column(String(255))
    current_stage_id = Column(UUID(as_uuid=True), ForeignKey("journey_stages.id"))
    status = Column(String(50), nullable=False, default="active")  # active, completed, cancelled

    meta_data = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    journey = relationship("Journey", back_populates="instances")
    patient = relationship("Patient", back_populates="journey_instances")
    current_stage = relationship("JourneyStage", foreign_keys=[current_stage_id])
    stage_statuses = relationship("JourneyInstanceStageStatus", back_populates="journey_instance", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (Index("idx_journey_instances_patient", "patient_id", "status"),)


class JourneyInstanceStageStatus(Base):
    """Track stage progress for each journey instance"""

    __tablename__ = "journey_instance_stage_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    journey_instance_id = Column(UUID(as_uuid=True), ForeignKey("journey_instances.id", ondelete="CASCADE"), nullable=False)
    stage_id = Column(UUID(as_uuid=True), ForeignKey("journey_stages.id"), nullable=False)

    status = Column(String(50), nullable=False)  # pending, in_progress, completed, skipped
    entered_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    meta_data = Column(JSONB, default=dict)

    # Relationships
    journey_instance = relationship("JourneyInstance", back_populates="stage_statuses")
    stage = relationship("JourneyStage")

    # Indexes
    __table_args__ = (Index("idx_jiss_instance", "journey_instance_id"),)


class Communication(Base):
    """Patient communications"""

    __tablename__ = "communications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    journey_instance_id = Column(UUID(as_uuid=True), ForeignKey("journey_instances.id"))

    channel = Column(String(50), nullable=False)  # whatsapp, sms, email, phone, in_app
    direction = Column(String(50), nullable=False)  # outbound, inbound
    template_code = Column(String(100))
    content = Column(Text)
    content_structured = Column(JSONB)

    related_resource_type = Column(String(100))  # Appointment, Encounter, Ticket
    related_resource_id = Column(String(255))

    status = Column(String(50), nullable=False)  # sent, delivered, failed, read
    external_id = Column(String(255))  # provider message id

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="communications")
    journey_instance = relationship("JourneyInstance")
    created_by = relationship("User")

    # Indexes
    __table_args__ = (Index("idx_communications_patient", "patient_id", "created_at"),)


class Ticket(Base):
    """Support tickets"""

    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))

    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(50), nullable=False, default="open")  # open, in_progress, resolved, closed
    priority = Column(String(50), nullable=False, default="medium")  # low, medium, high, urgent

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="tickets")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])

    # Indexes
    __table_args__ = (Index("idx_tickets_patient", "patient_id", "status"),)


# ====================================================================================
# PHASE 3 MODELS: IPD + Nursing + Orders + ICU
# ====================================================================================


class Ward(Base):
    """Hospital wards for inpatient care"""

    __tablename__ = "wards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)

    code = Column(String(50), nullable=False)  # WARD-3A
    name = Column(String(200), nullable=False)  # Ward 3A - General Medicine
    type = Column(String(50))  # general, icu, hdu, pediatrics, maternity
    floor = Column(String(50))
    capacity = Column(Integer)
    is_active = Column(Boolean, nullable=False, default=True)

    meta_data = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    location = relationship("Location")
    beds = relationship("Bed", back_populates="ward", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("uniq_ward_code_tenant", "tenant_id", "code", unique=True),
        Index("idx_wards_type", "type", "is_active"),
    )


class Bed(Base):
    """Hospital beds"""

    __tablename__ = "beds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id"), nullable=False)

    code = Column(String(50), nullable=False)  # 3A-12
    type = Column(String(50))  # standard, icu, isolation, ventilator
    status = Column(String(50), nullable=False, default="available")  # available, occupied, cleaning, maintenance, blocked

    meta_data = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ward = relationship("Ward", back_populates="beds")
    assignments = relationship("BedAssignment", back_populates="bed")

    # Indexes
    __table_args__ = (
        Index("uniq_bed_code_ward", "ward_id", "code", unique=True),
        Index("idx_beds_status_ward", "ward_id", "status"),
    )


class BedAssignment(Base):
    """Tracks patient-to-bed assignments over time"""

    __tablename__ = "bed_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=False)
    admission_id = Column(UUID(as_uuid=True))  # Will reference admissions table

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))  # null = current
    status = Column(String(50), nullable=False, default="active")  # active, transferred, discharged, cancelled

    meta_data = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bed = relationship("Bed", back_populates="assignments")
    patient = relationship("Patient")
    encounter = relationship("Encounter")

    # Indexes
    __table_args__ = (
        Index("idx_bed_assignments_bed", "bed_id", "status"),
        Index("idx_bed_assignments_patient", "patient_id", "start_time"),
    )


class Admission(Base):
    """Inpatient admissions (IPD)"""

    __tablename__ = "admissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    primary_practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=False)

    admitting_department = Column(String(200))  # General Medicine, Surgery, etc.
    admission_type = Column(String(50))  # elective, emergency, transfer
    admission_reason = Column(Text)
    source_type = Column(String(50))  # OPD, ER, REFERRAL, OTHER
    source_appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"))

    episode_of_care_fhir_id = Column(String(100))  # FHIR EpisodeOfCare.id
    status = Column(String(50), nullable=False, default="admitted")  # admitted, transferred, discharged, cancelled

    admitted_at = Column(DateTime(timezone=True), nullable=False)
    discharged_at = Column(DateTime(timezone=True))
    discharge_summary_fhir_id = Column(String(100))

    meta_data = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    practitioner = relationship("Practitioner")
    encounter = relationship("Encounter")
    source_appointment = relationship("Appointment")

    # Indexes
    __table_args__ = (
        Index("idx_admissions_patient", "patient_id", "admitted_at"),
        Index("idx_admissions_status", "status"),
        Index("idx_admissions_doctor", "primary_practitioner_id", "status"),
    )


class NursingTask(Base):
    """Nursing tasks and assignments"""

    __tablename__ = "nursing_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id"))
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    bed_assignment_id = Column(UUID(as_uuid=True), ForeignKey("bed_assignments.id"))
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id"))

    task_type = Column(String(100), nullable=False)  # medication, vitals, procedure, education, assessment
    description = Column(Text, nullable=False)
    priority = Column(String(50), nullable=False, default="normal")  # low, normal, high, critical
    status = Column(String(50), nullable=False, default="open")  # open, in_progress, completed, cancelled

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    due_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    meta_data = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    admission = relationship("Admission")
    ward = relationship("Ward")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])

    # Indexes
    __table_args__ = (
        Index("idx_nursing_tasks_ward_status", "ward_id", "status", "due_at"),
        Index("idx_nursing_tasks_patient", "patient_id", "status"),
        Index("idx_nursing_tasks_assigned", "assigned_to_user_id", "status"),
    )


class NursingObservation(Base):
    """Nursing observations (vitals, I/O, assessments)"""

    __tablename__ = "nursing_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id"))
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    bed_assignment_id = Column(UUID(as_uuid=True), ForeignKey("bed_assignments.id"))

    observation_type = Column(String(50), nullable=False)  # vitals, pain, wound, io, assessment, other
    observation_time = Column(DateTime(timezone=True), nullable=False)
    data = Column(JSONB, nullable=False)  # Structured observation data
    fhir_observation_ids = Column(JSONB)  # List of FHIR Observation.id's

    observed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    admission = relationship("Admission")
    observed_by = relationship("User")

    # Indexes
    __table_args__ = (Index("idx_nursing_obs_patient_time", "patient_id", "observation_time"),)


class Order(Base):
    """Clinical orders (lab, imaging, procedure, medication)"""

    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id"))
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    ordering_practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"), nullable=False)

    order_type = Column(String(50), nullable=False)  # lab, imaging, procedure, medication
    code = Column(String(100))  # LOINC, SNOMED, or internal code
    description = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="requested")  # requested, in_progress, completed, cancelled, rejected
    priority = Column(String(50), nullable=False, default="routine")  # routine, urgent, stat
    reason = Column(Text)

    external_order_id = Column(String(255))  # ID in LIS/RIS/Pharmacy
    fhir_service_request_id = Column(String(100))
    fhir_medication_request_id = Column(String(100))

    meta_data = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    admission = relationship("Admission")
    ordering_practitioner = relationship("Practitioner")

    # Indexes
    __table_args__ = (
        Index("idx_orders_patient", "patient_id", "created_at"),
        Index("idx_orders_encounter", "encounter_id"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_type", "order_type", "status"),
    )


class EWSScore(Base):
    """Early Warning Scores (NEWS2, MEWS, SOFA)"""

    __tablename__ = "ews_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    score_type = Column(String(50), nullable=False)  # NEWS2, MEWS, SOFA, APACHE
    score_value = Column(Integer, nullable=False)
    risk_level = Column(String(50), nullable=False)  # low, medium, high, critical
    calculated_at = Column(DateTime(timezone=True), nullable=False)
    source_observation_ids = Column(JSONB)  # List of nursing_observations.id

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    admission = relationship("Admission")

    # Indexes
    __table_args__ = (Index("idx_ews_patient", "patient_id", "calculated_at"),)


class ICUAlert(Base):
    """ICU/HDU alerts and warnings"""

    __tablename__ = "icu_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    alert_type = Column(String(100), nullable=False)  # ews_high, vitals_trend, device_alarm, medication_due
    message = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False)  # info, warning, critical
    status = Column(String(50), nullable=False, default="open")  # open, acknowledged, resolved

    triggered_at = Column(DateTime(timezone=True), nullable=False)
    acknowledged_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))

    meta_data = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    admission = relationship("Admission")
    acknowledged_by = relationship("User")

    # Indexes
    __table_args__ = (Index("idx_icu_alerts_patient", "patient_id", "status", "triggered_at"),)


# ==================== Phase 4: Outcomes & Quality Models ====================

class Episode(Base):
    """Unified episodes across OPD and IPD for outcome tracking"""
    __tablename__ = "episodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    # FHIR linkage
    episode_of_care_fhir_id = Column(String(100))

    # Index encounter/admission
    index_encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    index_admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id"))

    # Episode characteristics
    care_type = Column(String(50), nullable=False)  # OPD, IPD, OPD_IPD, DAY_CARE
    specialty = Column(String(100))  # CARDIOLOGY, ORTHOPEDICS, etc.
    primary_condition_code = Column(String(100))  # SNOMED or ICD

    # Timeline
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))

    status = Column(String(50), nullable=False, default="active")  # active, completed, abandoned

    # Metadata
    meta_data = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    index_encounter = relationship("Encounter", foreign_keys=[index_encounter_id])
    index_admission = relationship("Admission", foreign_keys=[index_admission_id])
    outcomes = relationship("Outcome", back_populates="episode", cascade="all, delete-orphan")
    proms = relationship("PROM", back_populates="episode", cascade="all, delete-orphan")
    prems = relationship("PREM", back_populates="episode", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_episodes_patient", "patient_id", "started_at"),
        Index("idx_episodes_status", "status"),
    )


class Outcome(Base):
    """Clinical outcomes per episode"""
    __tablename__ = "outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=False)

    # Outcome definition
    outcome_type = Column(String(100), nullable=False)  # mortality, readmission_30d, complication, functional_status
    outcome_subtype = Column(String(100))  # all_cause, cardiac, AKI_stage2

    # Value
    value = Column(Text)  # yes, no, NYHA_II
    numeric_value = Column(Float)  # for scores, LOS
    unit = Column(String(50))

    occurred_at = Column(DateTime(timezone=True))

    # Provenance
    derived_from = Column(String(100))  # manual_entry, rules_engine, ml_model
    source_event_id = Column(Text)
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    episode = relationship("Episode", back_populates="outcomes")

    # Indexes
    __table_args__ = (Index("idx_outcomes_episode_type", "episode_id", "outcome_type"),)


class PROM(Base):
    """Patient-Reported Outcome Measures"""
    __tablename__ = "proms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    # Instrument
    instrument_code = Column(String(100), nullable=False)  # EQ5D, PROMIS_PAIN
    version = Column(String(50))

    # Data
    responses = Column(JSONB, nullable=False)  # question-answer map
    score = Column(Float)  # computed summary score

    completed_at = Column(DateTime(timezone=True), nullable=False)
    mode = Column(String(50))  # web, sms, phone, in_clinic

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    episode = relationship("Episode", back_populates="proms")
    patient = relationship("Patient")

    # Indexes
    __table_args__ = (Index("idx_proms_patient", "patient_id", "completed_at"),)


class PREM(Base):
    """Patient-Reported Experience Measures"""
    __tablename__ = "prems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    # Instrument
    instrument_code = Column(String(100), nullable=False)  # HCAHPS, NPS

    # Data
    responses = Column(JSONB, nullable=False)
    score = Column(Float)

    completed_at = Column(DateTime(timezone=True), nullable=False)
    mode = Column(String(50))

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    episode = relationship("Episode", back_populates="prems")
    patient = relationship("Patient")

    # Indexes
    __table_args__ = (Index("idx_prems_patient", "patient_id", "completed_at"),)


class QualityMetric(Base):
    """Quality metric definitions"""
    __tablename__ = "quality_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Metric identity
    code = Column(String(100), nullable=False)  # HF_30D_READMISSION_RATE
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Metric type
    measure_type = Column(String(50), nullable=False)  # rate, count, ratio, score

    # Definitions (JSON DSL)
    numerator_definition = Column(JSONB, nullable=False)
    denominator_definition = Column(JSONB, nullable=False)

    tags = Column(ARRAY(String))  # cardiology, ipd, readmission
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    values = relationship("QualityMetricValue", back_populates="metric", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("uniq_quality_metric_code_tenant", "tenant_id", "code", unique=True),
    )


class QualityMetricValue(Base):
    """Quality metric values over time"""
    __tablename__ = "quality_metric_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    metric_id = Column(UUID(as_uuid=True), ForeignKey("quality_metrics.id"), nullable=False)

    # Time period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Values
    numerator_value = Column(Float, nullable=False)
    denominator_value = Column(Float, nullable=False)
    value = Column(Float, nullable=False)  # computed measure
    unit = Column(String(50))  # %, count

    # Breakdown
    breakdown = Column(JSONB)  # {ward: ICU, specialty: CARDIOLOGY}

    # Calculation metadata
    calculated_at = Column(DateTime(timezone=True), nullable=False)
    calculation_version = Column(String(50))

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    metric = relationship("QualityMetric", back_populates="values")

    # Indexes
    __table_args__ = (
        Index("idx_qmv_metric_period", "metric_id", "period_start", "period_end"),
    )


class QIProject(Base):
    """Quality Improvement projects"""
    __tablename__ = "qi_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Project identity
    code = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Owner
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Status
    status = Column(String(50), nullable=False, default="active")  # draft, active, on_hold, completed

    # Timeline
    start_date = Column(Date)
    target_date = Column(Date)

    # Target
    target_description = Column(Text)
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User")
    metrics = relationship("QIProjectMetric", back_populates="project", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("uniq_qi_project_code_tenant", "tenant_id", "code", unique=True),
    )


class QIProjectMetric(Base):
    """Metrics tracked by QI projects"""
    __tablename__ = "qi_project_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    qi_project_id = Column(UUID(as_uuid=True), ForeignKey("qi_projects.id", ondelete="CASCADE"), nullable=False)
    metric_id = Column(UUID(as_uuid=True), ForeignKey("quality_metrics.id"), nullable=False)

    baseline_value = Column(Float)
    target_value = Column(Float)
    unit = Column(String(50))

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    project = relationship("QIProject", back_populates="metrics")
    metric = relationship("QualityMetric")


# ==================== Phase 4: Risk Stratification Models ====================

class RiskModel(Base):
    """Risk model definitions"""
    __tablename__ = "risk_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Model identity
    code = Column(String(100), nullable=False)  # READMIT_30D, MORTALITY_ICU
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Target
    target_label = Column(String(100), nullable=False)  # readmission_30d, in_hospital_mortality

    # Default version
    default_version_id = Column(UUID(as_uuid=True))  # FK to risk_model_versions, set via migration

    is_active = Column(Boolean, nullable=False, default=True)
    tags = Column(ARRAY(String))

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    versions = relationship("RiskModelVersion", back_populates="model", cascade="all, delete-orphan", foreign_keys="RiskModelVersion.risk_model_id")

    # Indexes
    __table_args__ = (
        Index("uniq_risk_model_code_tenant", "tenant_id", "code", unique=True),
    )


class RiskModelVersion(Base):
    """Versioned risk models"""
    __tablename__ = "risk_model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    risk_model_id = Column(UUID(as_uuid=True), ForeignKey("risk_models.id", ondelete="CASCADE"), nullable=False)

    # Version
    version = Column(String(50), nullable=False)  # v1, v1.1, 2025-01
    status = Column(String(50), nullable=False, default="active")  # draft, active, deprecated

    # Artifact
    artifact_location = Column(Text)  # model file path / registry URI

    # Schema & config
    input_schema = Column(JSONB, nullable=False)  # expected input features
    hyperparameters = Column(JSONB)
    training_data_period = Column(JSONB)  # {from: ..., to: ...}

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    activated_at = Column(DateTime(timezone=True))
    deprecated_at = Column(DateTime(timezone=True))

    # Relationships
    model = relationship("RiskModel", back_populates="versions", foreign_keys=[risk_model_id])
    scores = relationship("RiskScore", back_populates="version", cascade="all, delete-orphan")
    performance_metrics = relationship("RiskModelPerformance", back_populates="version", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("uniq_risk_model_versions", "risk_model_id", "version", unique=True),
    )


class RiskScore(Base):
    """Risk score predictions"""
    __tablename__ = "risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    risk_model_id = Column(UUID(as_uuid=True), ForeignKey("risk_models.id"), nullable=False)
    risk_model_version_id = Column(UUID(as_uuid=True), ForeignKey("risk_model_versions.id"), nullable=False)

    # Patient context
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"))
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id"))
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))

    # Prediction
    score = Column(Float, nullable=False)
    risk_bucket = Column(String(50), nullable=False)  # low, medium, high, very_high
    input_features = Column(JSONB, nullable=False)

    predicted_at = Column(DateTime(timezone=True), nullable=False)
    prediction_horizon = Column(String(50))  # 30d, in_hospital

    # Outcome (filled in later for evaluation)
    outcome_value = Column(Text)
    outcome_observed_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    episode = relationship("Episode")
    admission = relationship("Admission")
    encounter = relationship("Encounter")
    version = relationship("RiskModelVersion", back_populates="scores")

    # Indexes
    __table_args__ = (
        Index("idx_risk_scores_patient", "patient_id", "predicted_at"),
        Index("idx_risk_scores_model", "risk_model_id", "risk_model_version_id", "predicted_at"),
    )


class RiskModelPerformance(Base):
    """Risk model performance metrics"""
    __tablename__ = "risk_model_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    risk_model_version_id = Column(UUID(as_uuid=True), ForeignKey("risk_model_versions.id"), nullable=False)

    # Evaluation period
    eval_data_period = Column(JSONB, nullable=False)  # {from: ..., to: ...}

    # Metric
    metric_name = Column(String(100), nullable=False)  # auroc, auprc, brier, calibration_slope
    metric_value = Column(Float, nullable=False)
    metric_details = Column(JSONB)  # bins for calibration curve

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    version = relationship("RiskModelVersion", back_populates="performance_metrics")

    # Indexes
    __table_args__ = (
        Index("idx_risk_model_perf", "risk_model_version_id", "metric_name"),
    )


# ==================== Phase 4: Voice & Collaboration Models ====================

class VoiceSession(Base):
    """Voice session metadata"""
    __tablename__ = "voice_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Context
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id"))

    # Session details
    session_type = Column(String(100), nullable=False)  # opd_consult, ward_round, cc_call
    channel = Column(String(50))  # telephony, webrtc, in_app

    # Timeline
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))

    # ASR
    asr_model = Column(String(100))  # whisper-large-v3
    transcript = Column(Text)  # full combined transcript
    transcript_structured = Column(JSONB)  # with speaker labels, segments

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    admission = relationship("Admission")
    created_by = relationship("User")
    segments = relationship("VoiceSegment", back_populates="session", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_voice_sessions_patient", "patient_id", "started_at"),
    )


class VoiceSegment(Base):
    """Transcription segments"""
    __tablename__ = "voice_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    voice_session_id = Column(UUID(as_uuid=True), ForeignKey("voice_sessions.id", ondelete="CASCADE"), nullable=False)

    # Timing
    start_time_ms = Column(Integer, nullable=False)
    end_time_ms = Column(Integer, nullable=False)

    # Content
    speaker_label = Column(String(50))  # doctor, patient, nurse, other
    text = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    session = relationship("VoiceSession", back_populates="segments")

    # Indexes
    __table_args__ = (
        Index("idx_voice_segments_session", "voice_session_id", "start_time_ms"),
    )


class CollabThread(Base):
    """Collaboration threads for case discussions"""
    __tablename__ = "collab_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Thread type
    thread_type = Column(String(100), nullable=False)  # case_discussion, note_review, qi_project

    # Context
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"))
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id"))

    # Related resource
    related_resource_type = Column(String(100))  # Encounter, Order, Note, QIProject
    related_resource_id = Column(Text)

    # Thread details
    title = Column(String(500), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_archived = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    episode = relationship("Episode")
    admission = relationship("Admission")
    created_by = relationship("User")
    messages = relationship("CollabMessage", back_populates="thread", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_collab_threads_patient", "patient_id", "thread_type"),
    )


class CollabMessage(Base):
    """Messages in collaboration threads"""
    __tablename__ = "collab_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("collab_threads.id", ondelete="CASCADE"), nullable=False)

    # Author
    author_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    author_type = Column(String(50), nullable=False)  # user, ai_agent

    # Content
    message = Column(Text, nullable=False)
    mentions = Column(JSONB)  # list of user_ids or role tags

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    thread = relationship("CollabThread", back_populates="messages")
    author = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_collab_messages_thread", "thread_id", "created_at"),
    )


class NoteRevision(Base):
    """Note versioning for collaborative editing"""
    __tablename__ = "note_revisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=False)

    # Note identity
    note_type = Column(String(100), nullable=False)  # opd_note, progress_note, discharge_summary
    version = Column(Integer, nullable=False)

    # Author
    author_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Content
    content_structured = Column(JSONB)  # SOAP or similar
    content_raw = Column(Text)  # raw markdown/HTML

    # Source
    source = Column(String(100))  # doctor, scribe_agent, round_agent
    is_final = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    encounter = relationship("Encounter")
    author = relationship("User")

    # Indexes
    __table_args__ = (
        Index("uniq_note_revision", "encounter_id", "note_type", "version", unique=True),
    )


# ==================== Phase 4: Governance & LLM Audit Models ====================

class LLMSession(Base):
    """LLM session tracking"""
    __tablename__ = "llm_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Session type
    session_type = Column(String(100), nullable=False)  # opd_scribe, cc_agent, prm_bot, icu_monitor

    # Timeline
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))

    # Context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"))
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id"))

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    patient = relationship("Patient")
    episode = relationship("Episode")
    admission = relationship("Admission")
    tool_calls = relationship("LLMToolCall", back_populates="session", cascade="all, delete-orphan")
    responses = relationship("LLMResponse", back_populates="session", cascade="all, delete-orphan")
    policy_violations = relationship("PolicyViolation", back_populates="session", cascade="all, delete-orphan")


class LLMToolCall(Base):
    """LLM tool usage tracking"""
    __tablename__ = "llm_tool_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    session_id = Column(UUID(as_uuid=True), ForeignKey("llm_sessions.id", ondelete="CASCADE"), nullable=False)

    # Tool details
    tool_name = Column(String(200), nullable=False)
    tool_input = Column(JSONB, nullable=False)

    called_at = Column(DateTime(timezone=True), nullable=False)

    # Result
    result_summary = Column(JSONB)  # trimmed representation (no PHI if not needed)
    latency_ms = Column(Integer)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    session = relationship("LLMSession", back_populates="tool_calls")

    # Indexes
    __table_args__ = (
        Index("idx_llm_tool_calls_session", "session_id", "called_at"),
    )


class LLMResponse(Base):
    """LLM responses tracking"""
    __tablename__ = "llm_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    session_id = Column(UUID(as_uuid=True), ForeignKey("llm_sessions.id", ondelete="CASCADE"), nullable=False)

    # Model details
    model_name = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)

    # Response
    response_text = Column(Text)
    safety_flags = Column(JSONB)  # {pii_redacted: true, toxicity: low}

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    session = relationship("LLMSession", back_populates="responses")


class PolicyViolation(Base):
    """Policy violations tracking"""
    __tablename__ = "policy_violations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    session_id = Column(UUID(as_uuid=True), ForeignKey("llm_sessions.id"), nullable=False)

    # Violation details
    violation_type = Column(String(100), nullable=False)  # PHI_leak_risk, disallowed_instruction, hallucination_flag
    description = Column(Text)
    severity = Column(String(50), nullable=False)  # low, medium, high

    # Timeline
    detected_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True))

    # Resolution
    resolved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    session = relationship("LLMSession", back_populates="policy_violations")
    resolved_by = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_policy_violations_session", "session_id", "violation_type"),
    )


# ==================== Phase 5: Open Ecosystem & Network Protocol ====================
# Interoperability Gateway, Referral Network, Remote Monitoring, App Marketplace, Consent Orchestration

# --- Interoperability Gateway Models ---

class ExternalSystem(Base):
    """
    External HIS/EHR/LIS/RIS systems integrated via interoperability gateway
    Examples: Narayana Athma, Apollo EPIC, lab partners, imaging centers
    """
    __tablename__ = "external_systems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'NARAYANA_ATHMA', 'APOLLO_EPIC'
    name = Column(String(255), nullable=False)
    system_type = Column(String(50), nullable=False)  # 'EHR', 'LIS', 'RIS', 'PAYER', 'APP'
    base_url = Column(Text)
    auth_type = Column(String(50))  # 'basic', 'oauth2', 'mutual_tls', 'api_key'
    auth_config = Column(JSONB)  # client_id, secrets, cert fingerprints
    fhir_capability = Column(JSONB)  # supported resources/operations
    hl7v2_capability = Column(JSONB)  # supported message types
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    channels = relationship("InteropChannel", back_populates="external_system")

    # Indexes
    __table_args__ = (
        Index("uniq_external_system_code_tenant", "tenant_id", "code", unique=True),
    )


class InteropChannel(Base):
    """
    Configured integration channel for external system communication
    Examples: FHIR REST push, HL7 TCP feed, webhook, SFTP
    """
    __tablename__ = "interop_channels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    external_system_id = Column(UUID(as_uuid=True), ForeignKey("external_systems.id"), nullable=False)
    channel_type = Column(String(50), nullable=False)  # 'FHIR_REST', 'HL7V2_TCP', 'WEBHOOK', 'SFTP_DROP'
    direction = Column(String(20), nullable=False)  # 'inbound', 'outbound', 'bidirectional'
    resource_scope = Column(JSONB, nullable=False)  # {"fhir_resources": ["Patient", "Encounter", "Observation"]}
    mapping_profile_id = Column(UUID(as_uuid=True), ForeignKey("mapping_profiles.id"))
    is_active = Column(Boolean, default=True)
    config = Column(JSONB)  # endpoint URLs, ports, file paths
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    external_system = relationship("ExternalSystem", back_populates="channels")
    mapping_profile = relationship("MappingProfile")
    message_logs = relationship("InteropMessageLog", back_populates="channel")

    # Indexes
    __table_args__ = (
        Index("idx_interop_channels_system", "external_system_id", "direction"),
    )


class MappingProfile(Base):
    """
    Data mapping rules for transforming between external and internal formats
    FHIR profile mappings, HL7 segment mappings, custom transformations
    """
    __tablename__ = "mapping_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    direction = Column(String(50), nullable=False)  # 'external_to_internal', 'internal_to_external'
    format = Column(String(50), nullable=False)  # 'FHIR_R4', 'HL7V2', 'CUSTOM_JSON'
    resource_type = Column(String(100))  # 'Patient', 'Observation', 'ADT_A01'
    mapping_rules = Column(JSONB, nullable=False)  # JSON-based mapping DSL
    version = Column(String(20), nullable=False, default='v1')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")

    # Indexes
    __table_args__ = (
        Index("idx_mapping_profiles_type", "resource_type", "direction"),
    )


class InteropMessageLog(Base):
    """
    Audit log of all interoperability messages (inbound/outbound)
    Tracks message flow, transformations, success/failure
    """
    __tablename__ = "interop_message_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("interop_channels.id"), nullable=False)
    external_system_id = Column(UUID(as_uuid=True), ForeignKey("external_systems.id"), nullable=False)
    direction = Column(String(20), nullable=False)  # 'inbound', 'outbound'
    message_type = Column(String(100))  # 'FHIR.Patient', 'HL7.ADT_A01'
    correlation_id = Column(String(255))  # for matching req/resp/acks
    raw_payload = Column(Text)  # optionally truncated/redacted
    mapped_resource_type = Column(String(100))
    mapped_resource_id = Column(String(255))
    status = Column(String(50), nullable=False)  # 'received', 'parsed', 'mapped', 'failed', 'sent', 'acknowledged'
    status_detail = Column(Text)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    channel = relationship("InteropChannel", back_populates="message_logs")
    external_system = relationship("ExternalSystem")

    # Indexes
    __table_args__ = (
        Index("idx_interop_message_log_channel_time", "channel_id", "occurred_at"),
    )


# --- Referral Network Models ---

class NetworkOrganization(Base):
    """
    Network partner organizations (hospitals, clinics, labs, imaging centers)
    Represents organizations in the referral network
    """
    __tablename__ = "network_organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    code = Column(String(100), nullable=False, unique=True)  # 'NH_BANGALORE_001', 'APOLLO_BLK'
    name = Column(String(255), nullable=False)
    org_type = Column(String(50), nullable=False)  # 'HOSPITAL', 'CLINIC', 'LAB', 'IMAGING_CENTER', 'HOME_CARE'
    country = Column(String(100))
    region = Column(String(100))
    contact_info = Column(JSONB)
    interop_system_id = Column(UUID(as_uuid=True), ForeignKey("external_systems.id"))
    is_internal = Column(Boolean, nullable=False, default=False)  # part of same tenant group
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    interop_system = relationship("ExternalSystem")
    source_referrals = relationship("Referral", foreign_keys="Referral.source_org_id", back_populates="source_org")
    target_referrals = relationship("Referral", foreign_keys="Referral.target_org_id", back_populates="target_org")


class Referral(Base):
    """
    Multi-organization patient referrals
    Tracks referrals from source to target organization with full lifecycle
    """
    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    source_org_id = Column(UUID(as_uuid=True), ForeignKey("network_organizations.id"), nullable=False)
    target_org_id = Column(UUID(as_uuid=True), ForeignKey("network_organizations.id"), nullable=False)
    source_practitioner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    target_practitioner_id = Column(String(255))  # external identifier
    referral_type = Column(String(50), nullable=False)  # 'OPD', 'IPD_TRANSFER', 'DAY_CARE', 'HOME_CARE'
    service_line = Column(String(100))  # 'CARDIOLOGY', 'ONCOLOGY'
    reason = Column(Text, nullable=False)
    priority = Column(String(20), default='routine')  # 'routine', 'urgent', 'emergent'
    status = Column(String(50), nullable=False, default='draft')  # 'draft', 'sent', 'accepted', 'rejected', 'completed', 'cancelled'
    requested_at = Column(DateTime(timezone=True), nullable=False)
    responded_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    source_episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"))
    source_encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    source_admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id"))
    target_episode_identifier = Column(String(255))
    fhir_service_request_id = Column(String(255))
    meta_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    patient = relationship("Patient")
    source_org = relationship("NetworkOrganization", foreign_keys=[source_org_id], back_populates="source_referrals")
    target_org = relationship("NetworkOrganization", foreign_keys=[target_org_id], back_populates="target_referrals")
    source_practitioner = relationship("User")
    episode = relationship("Episode")
    encounter = relationship("Encounter")
    admission = relationship("Admission")
    documents = relationship("ReferralDocument", back_populates="referral")

    # Indexes
    __table_args__ = (
        Index("idx_referrals_patient", "patient_id", "requested_at"),
        Index("idx_referrals_status", "status", "priority", "requested_at"),
    )


class ReferralDocument(Base):
    """
    Clinical documents attached to referrals
    Summaries, imaging, labs, etc.
    """
    __tablename__ = "referral_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    referral_id = Column(UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(String(50), nullable=False)  # 'summary', 'imaging', 'lab', 'other'
    fhir_document_reference_id = Column(String(255))
    external_link = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    referral = relationship("Referral", back_populates="documents")


# --- Remote Monitoring Models ---

class RemoteDevice(Base):
    """
    Remote patient monitoring devices (wearables, home medical devices)
    BP cuffs, glucometers, scales, pulse oximeters, CGMs, etc.
    """
    __tablename__ = "remote_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    device_type = Column(String(50), nullable=False)  # 'BP_CUFF', 'GLUCOMETER', 'SCALE', 'PULSE_OX', 'ECG', 'CGM'
    manufacturer = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100))
    vendor_system_id = Column(UUID(as_uuid=True), ForeignKey("external_systems.id"))
    meta = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    vendor_system = relationship("ExternalSystem")
    bindings = relationship("DeviceBinding", back_populates="remote_device")

    # Indexes
    __table_args__ = (
        Index("idx_remote_devices_type", "device_type"),
    )


class DeviceBinding(Base):
    """
    Link between remote device and patient
    Represents active remote monitoring program enrollment
    """
    __tablename__ = "device_bindings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    remote_device_id = Column(UUID(as_uuid=True), ForeignKey("remote_devices.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    binding_status = Column(String(20), nullable=False, default='active')  # 'active', 'paused', 'ended'
    bound_at = Column(DateTime(timezone=True), nullable=False)
    unbound_at = Column(DateTime(timezone=True))
    care_program_code = Column(String(100))  # 'HF_HOME_MONITORING', 'DM2_REMOTE'
    home_address = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    remote_device = relationship("RemoteDevice", back_populates="bindings")
    patient = relationship("Patient")
    measurements = relationship("RemoteMeasurement", back_populates="device_binding")
    alerts = relationship("RemoteAlert", back_populates="device_binding")

    # Indexes
    __table_args__ = (
        Index("idx_device_bindings_patient", "patient_id", "binding_status"),
    )


class RemoteMeasurement(Base):
    """
    Remote patient measurements from home devices
    Vitals, glucose, weight, SpO2, etc.
    """
    __tablename__ = "remote_measurements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    device_binding_id = Column(UUID(as_uuid=True), ForeignKey("device_bindings.id"), nullable=False)
    remote_device_id = Column(UUID(as_uuid=True), ForeignKey("remote_devices.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    measurement_type = Column(String(50), nullable=False)  # 'BP', 'GLUCOSE', 'WEIGHT', 'SPO2', 'HR', 'STEP_COUNT'
    measured_at = Column(DateTime(timezone=True), nullable=False)
    payload = Column(JSONB, nullable=False)  # {"systolic": 150, "diastolic": 95}
    fhir_observation_id = Column(String(255))
    ingestion_source = Column(String(50))  # 'vendor_webhook', 'manual', 'file'
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    device_binding = relationship("DeviceBinding", back_populates="measurements")
    remote_device = relationship("RemoteDevice")
    patient = relationship("Patient")

    # Indexes
    __table_args__ = (
        Index("idx_remote_measurements_patient_time", "patient_id", "measured_at"),
        Index("idx_remote_measurements_type_time", "measurement_type", "measured_at"),
    )


class RemoteAlert(Base):
    """
    Alerts triggered by remote monitoring thresholds/trends
    Can auto-create nursing tasks for follow-up
    """
    __tablename__ = "remote_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    device_binding_id = Column(UUID(as_uuid=True), ForeignKey("device_bindings.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # 'threshold', 'trend', 'adherence'
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # 'info', 'warning', 'critical'
    status = Column(String(20), nullable=False, default='open')  # 'open', 'acknowledged', 'resolved'
    triggered_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    linked_task_id = Column(UUID(as_uuid=True))  # nursing task if created
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    device_binding = relationship("DeviceBinding", back_populates="alerts")
    patient = relationship("Patient")
    resolved_by = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_remote_alerts_patient", "patient_id", "status", "triggered_at"),
    )


# --- App Marketplace Models ---

class App(Base):
    """
    Third-party apps/agents in marketplace
    Web apps, mobile apps, AI agents, integrations
    """
    __tablename__ = "apps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'ZOOM_INTEGRATION', 'NLP_TRIAGE_AGENT'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    app_type = Column(String(50), nullable=False)  # 'web_app', 'agent', 'mobile', 'integration'
    callback_url = Column(Text)
    owner_org_id = Column(UUID(as_uuid=True), ForeignKey("network_organizations.id"))
    is_platform_app = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    owner_org = relationship("NetworkOrganization")
    keys = relationship("AppKey", back_populates="app")
    scopes = relationship("AppScope", back_populates="app")
    usage_logs = relationship("AppUsageLog", back_populates="app")

    # Indexes
    __table_args__ = (
        Index("uniq_app_code_tenant", "tenant_id", "code", unique=True),
    )


class AppKey(Base):
    """
    API keys for app authentication
    Hashed for security, tracked for usage auditing
    """
    __tablename__ = "app_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String(255), nullable=False)  # hashed API key
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    is_revoked = Column(Boolean, default=False)

    # Relationships
    app = relationship("App", back_populates="keys")

    # Indexes
    __table_args__ = (
        Index("idx_app_keys_app", "app_id"),
    )


class AppScope(Base):
    """
    Permissions/scopes for apps
    Defines what FHIR resources, tools, events app can access
    """
    __tablename__ = "app_scopes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id", ondelete="CASCADE"), nullable=False)
    scope_type = Column(String(50), nullable=False)  # 'FHIR', 'TOOL', 'EVENT', 'PATIENT'
    scope_code = Column(String(255), nullable=False)  # 'fhir.Patient.read', 'tool.book_appointment', 'event.Admission.Created'
    restrictions = Column(JSONB)  # {"tenant_id": "...", "org_type": "HOSPITAL"}
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    app = relationship("App", back_populates="scopes")

    # Indexes
    __table_args__ = (
        Index("idx_app_scopes_app", "app_id", "scope_type"),
    )


class AppUsageLog(Base):
    """
    Usage tracking for marketplace apps
    Audit trail of all app API calls, event deliveries, tool invocations
    """
    __tablename__ = "app_usage_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"), nullable=False)
    usage_type = Column(String(50), nullable=False)  # 'api_call', 'event_delivery', 'tool_invocation'
    scope_code = Column(String(255))
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    meta_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    app = relationship("App", back_populates="usage_logs")

    # Indexes
    __table_args__ = (
        Index("idx_app_usage_app_time", "app_id", "occurred_at"),
    )


# --- Consent Orchestration Models ---

class ConsentPolicy(Base):
    """
    Organization-level consent policy templates
    Defines default data categories, use cases, duration
    """
    __tablename__ = "consent_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'DEFAULT_OPD', 'REMOTE_MONITORING_DM2', 'RESEARCH_REGISTRY'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    data_categories = Column(JSONB, nullable=False)  # ["demographics", "labs", "imaging", "notes"]
    permitted_use_cases = Column(JSONB, nullable=False)  # ["treatment", "payment", "operations", "research"]
    default_duration_days = Column(Integer)
    can_be_withdrawn = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    consent_records = relationship("ConsentRecord", back_populates="policy")

    # Indexes
    __table_args__ = (
        Index("uniq_consent_policy_code_tenant", "tenant_id", "code", unique=True),
    )


class ConsentRecord(Base):
    """
    Patient consent records for cross-org data sharing
    Tracks what data can flow between organizations/apps
    """
    __tablename__ = "consent_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("consent_policies.id"), nullable=False)
    data_controller_org_id = Column(UUID(as_uuid=True), ForeignKey("network_organizations.id"), nullable=False)
    data_processor_org_id = Column(UUID(as_uuid=True), ForeignKey("network_organizations.id"))
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"))
    granted_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    revoked_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    scope_overrides = Column(JSONB)  # allow/deny for specific data categories
    purpose_override = Column(JSONB)
    status = Column(String(20), nullable=False, default='active')  # 'active', 'expired', 'revoked'
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    patient = relationship("Patient")
    policy = relationship("ConsentPolicy", back_populates="consent_records")
    data_controller_org = relationship("NetworkOrganization", foreign_keys=[data_controller_org_id])
    data_processor_org = relationship("NetworkOrganization", foreign_keys=[data_processor_org_id])
    app = relationship("App")
    revoked_by = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_consent_patient", "patient_id", "status", "granted_at"),
        Index("idx_consent_orgs", "data_controller_org_id", "data_processor_org_id"),
    )


# ==================== Phase 6: Research, Trials & Learning Health System ====================

# --- De-identification Service Models ---

class DeidConfig(Base):
    """
    De-identification configuration templates
    Defines rules for removing/generalizing PHI
    """
    __tablename__ = "deid_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'SAFE_HARBOR', 'LIMITED_DATASET', 'TRIAL_FEASIBILITY'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    mode = Column(String(50), nullable=False)  # 'deidentification', 'pseudonymization', 'both'
    rules = Column(JSONB, nullable=False)  # { "remove": [...], "generalize": [...], "mask": [...] }
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    deid_jobs = relationship("DeidJob", back_populates="deid_config")

    # Indexes
    __table_args__ = (
        Index("uniq_deid_config_code_tenant", "tenant_id", "code", unique=True),
    )


class PseudoIdSpace(Base):
    """
    Pseudonymization universes for different use cases
    Each space has separate ID mappings
    """
    __tablename__ = "pseudo_id_spaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'RESEARCH_SPACE_1', 'TRIAL_XYZ'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    scope = Column(String(50), nullable=False)  # 'patient', 'practitioner', 'org'
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    pseudo_id_mappings = relationship("PseudoIdMapping", back_populates="pseudo_id_space")

    # Indexes
    __table_args__ = (
        Index("uniq_pseudo_space_code_tenant", "tenant_id", "code", unique=True),
    )


class PseudoIdMapping(Base):
    """
    Mapping between real IDs and pseudonymized IDs
    HIGHLY SENSITIVE - should be super-locked in production
    """
    __tablename__ = "pseudo_id_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    pseudo_id_space_id = Column(UUID(as_uuid=True), ForeignKey("pseudo_id_spaces.id"), nullable=False)
    real_id = Column(String(255), nullable=False)  # patients.id, practitioners.id, etc.
    pseudo_id = Column(String(255), nullable=False)  # random or hashed ID
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_used_at = Column(DateTime(timezone=True))

    # Relationships
    pseudo_id_space = relationship("PseudoIdSpace", back_populates="pseudo_id_mappings")

    # Indexes
    __table_args__ = (
        Index("uniq_pseudo_mapping_real", "pseudo_id_space_id", "real_id", unique=True),
        Index("uniq_pseudo_mapping_pseudo", "pseudo_id_space_id", "pseudo_id", unique=True),
    )


class DeidJob(Base):
    """
    De-identification batch jobs
    Processes FHIR/analytics data through de-id rules
    """
    __tablename__ = "deid_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    deid_config_id = Column(UUID(as_uuid=True), ForeignKey("deid_configs.id"), nullable=False)
    pseudo_id_space_id = Column(UUID(as_uuid=True), ForeignKey("pseudo_id_spaces.id"))
    job_type = Column(String(50), nullable=False)  # 'snapshot', 'incremental', 'export'
    status = Column(String(50), nullable=False, default='queued')  # 'queued', 'running', 'completed', 'failed'
    requested_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description = Column(Text)
    filters = Column(JSONB)  # cohort/time filters
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    deid_config = relationship("DeidConfig", back_populates="deid_jobs")
    pseudo_id_space = relationship("PseudoIdSpace")
    requested_by = relationship("User")
    outputs = relationship("DeidJobOutput", back_populates="deid_job", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_deid_job_status", "status", "created_at"),
    )


class DeidJobOutput(Base):
    """
    Outputs generated by de-identification jobs
    Links to storage location
    """
    __tablename__ = "deid_job_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    deid_job_id = Column(UUID(as_uuid=True), ForeignKey("deid_jobs.id", ondelete="CASCADE"), nullable=False)
    output_type = Column(String(50), nullable=False)  # 'fhir_bundle', 'parquet', 'csv', 'db_table'
    location = Column(Text, nullable=False)  # URI or table name
    row_count = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    deid_job = relationship("DeidJob", back_populates="outputs")


# --- Research Registry Models ---

class Registry(Base):
    """
    Disease/condition registries for research
    Defines populations to track longitudinally
    """
    __tablename__ = "registries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'HF_REGISTRY', 'CKD_REGISTRY'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    specialty = Column(String(100))
    inclusion_criteria = Column(JSONB)  # high-level description
    exclusion_criteria = Column(JSONB)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    criteria = relationship("RegistryCriteria", back_populates="registry", cascade="all, delete-orphan")
    enrollments = relationship("RegistryEnrollment", back_populates="registry")
    data_elements = relationship("RegistryDataElement", back_populates="registry", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("uniq_registry_code_tenant", "tenant_id", "code", unique=True),
    )


class RegistryCriteria(Base):
    """
    Machine-readable eligibility criteria for registries
    Evaluated via analytics-hub DSL
    """
    __tablename__ = "registry_criteria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    registry_id = Column(UUID(as_uuid=True), ForeignKey("registries.id", ondelete="CASCADE"), nullable=False)
    criteria_type = Column(String(20), nullable=False)  # 'inclusion', 'exclusion'
    dsl_definition = Column(JSONB, nullable=False)  # expression to be evaluated
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    registry = relationship("Registry", back_populates="criteria")


class RegistryEnrollment(Base):
    """
    Patient enrollments in registries
    Tracks active participation
    """
    __tablename__ = "registry_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    registry_id = Column(UUID(as_uuid=True), ForeignKey("registries.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"))
    status = Column(String(20), nullable=False, default='active')  # 'active', 'withdrawn', 'completed'
    enrolled_at = Column(DateTime(timezone=True), nullable=False)
    withdrawn_at = Column(DateTime(timezone=True))
    withdrawal_reason = Column(Text)
    source = Column(String(20), nullable=False)  # 'auto', 'manual', 'trial'
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    registry = relationship("Registry", back_populates="enrollments")
    patient = relationship("Patient")
    episode = relationship("Episode")
    data_values = relationship("RegistryDataValue", back_populates="registry_enrollment", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_registry_enrollments_reg", "registry_id", "status"),
        Index("idx_registry_enrollments_patient", "patient_id", "enrolled_at"),
    )


class RegistryDataElement(Base):
    """
    Data elements (variables) tracked for each registry
    Defines what data to collect
    """
    __tablename__ = "registry_data_elements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    registry_id = Column(UUID(as_uuid=True), ForeignKey("registries.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(100), nullable=False)  # 'LVEF', 'NYHA_CLASS', 'NT_PROBNP'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    value_type = Column(String(50), nullable=False)  # 'string', 'number', 'date', 'code'
    source_type = Column(String(50), nullable=False)  # 'fhir', 'analytics', 'manual'
    source_definition = Column(JSONB)  # FHIR Observation codes or SQL/DSL
    is_required = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    registry = relationship("Registry", back_populates="data_elements")
    data_values = relationship("RegistryDataValue", back_populates="data_element")

    # Indexes
    __table_args__ = (
        Index("uniq_registry_data_element_code", "registry_id", "code", unique=True),
    )


class RegistryDataValue(Base):
    """
    Actual data values for registry enrollments
    Time-series snapshots
    """
    __tablename__ = "registry_data_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    registry_enrollment_id = Column(UUID(as_uuid=True), ForeignKey("registry_enrollments.id", ondelete="CASCADE"), nullable=False)
    data_element_id = Column(UUID(as_uuid=True), ForeignKey("registry_data_elements.id"), nullable=False)
    as_of_date = Column(Date, nullable=False)
    value_string = Column(Text)
    value_number = Column(Numeric)
    value_date = Column(Date)
    value_code = Column(String(100))
    source = Column(String(50))  # 'auto_extract', 'manual_entry'
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    registry_enrollment = relationship("RegistryEnrollment", back_populates="data_values")
    data_element = relationship("RegistryDataElement", back_populates="data_values")

    # Indexes
    __table_args__ = (
        Index("idx_registry_data_values_enrollment_date", "registry_enrollment_id", "as_of_date"),
    )


# --- Trial Management Models ---

class Trial(Base):
    """
    Clinical trials with protocol and eligibility criteria
    """
    __tablename__ = "trials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'HF_TRIAL_001'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    phase = Column(String(50))  # 'Phase II', 'Phase III', 'Registry'
    sponsor_org_id = Column(UUID(as_uuid=True), ForeignKey("network_organizations.id"))
    principal_investigator_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    protocol_version = Column(String(50))
    status = Column(String(50), nullable=False, default='draft')  # 'draft', 'recruiting', 'active', 'completed', 'terminated'
    start_date = Column(Date)
    end_date = Column(Date)
    target_sample_size = Column(Integer)
    inclusion_criteria = Column(JSONB)
    exclusion_criteria = Column(JSONB)
    registry_reference = Column(String(255))  # clinicaltrials.gov ID
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    sponsor_org = relationship("NetworkOrganization")
    principal_investigator = relationship("User")
    arms = relationship("TrialArm", back_populates="trial", cascade="all, delete-orphan")
    visits = relationship("TrialVisit", back_populates="trial", cascade="all, delete-orphan")
    subjects = relationship("TrialSubject", back_populates="trial")
    crfs = relationship("TrialCRF", back_populates="trial", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("uniq_trial_code_tenant", "tenant_id", "code", unique=True),
    )


class TrialArm(Base):
    """
    Trial arms for randomization
    """
    __tablename__ = "trial_arms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    trial_id = Column(UUID(as_uuid=True), ForeignKey("trials.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False)  # 'A', 'B', 'CONTROL', 'INTERVENTION'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    randomization_ratio = Column(Numeric)  # e.g., 1, 2 for 1:2 randomization
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    trial = relationship("Trial", back_populates="arms")
    subjects = relationship("TrialSubject", back_populates="arm")

    # Indexes
    __table_args__ = (
        Index("uniq_trial_arm_code", "trial_id", "code", unique=True),
    )


class TrialVisit(Base):
    """
    Visit schedule definition for trials
    """
    __tablename__ = "trial_visits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    trial_id = Column(UUID(as_uuid=True), ForeignKey("trials.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False)  # 'V1', 'V2', 'V3'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    day_offset = Column(Integer, nullable=False)  # e.g., 0, 7, 30 relative to reference
    window_minus = Column(Integer)  # allowed negative deviation (days)
    window_plus = Column(Integer)  # allowed positive deviation (days)
    required = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    trial = relationship("Trial", back_populates="visits")
    subject_visits = relationship("TrialSubjectVisit", back_populates="trial_visit")

    # Indexes
    __table_args__ = (
        Index("uniq_trial_visit_code", "trial_id", "code", unique=True),
    )


class TrialSubject(Base):
    """
    Trial participants with screening and enrollment status
    """
    __tablename__ = "trial_subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    trial_id = Column(UUID(as_uuid=True), ForeignKey("trials.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    pseudo_id_space_id = Column(UUID(as_uuid=True), ForeignKey("pseudo_id_spaces.id"))
    pseudo_patient_id = Column(String(255))  # if pseudonymized
    arm_id = Column(UUID(as_uuid=True), ForeignKey("trial_arms.id"))
    screening_status = Column(String(50), nullable=False, default='screening')  # 'screening', 'screen_failed', 'enrolled', 'withdrawn', 'completed'
    screening_date = Column(Date)
    randomization_date = Column(Date)
    consent_record_id = Column(UUID(as_uuid=True), ForeignKey("consent_records.id"))
    withdrawal_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    trial = relationship("Trial", back_populates="subjects")
    patient = relationship("Patient")
    pseudo_id_space = relationship("PseudoIdSpace")
    arm = relationship("TrialArm", back_populates="subjects")
    consent_record = relationship("ConsentRecord")
    subject_visits = relationship("TrialSubjectVisit", back_populates="trial_subject", cascade="all, delete-orphan")
    crf_responses = relationship("TrialCRFResponse", back_populates="trial_subject", cascade="all, delete-orphan")
    protocol_deviations = relationship("TrialProtocolDeviation", back_populates="trial_subject", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_trial_subjects_trial", "trial_id", "screening_status"),
        Index("idx_trial_subjects_patient", "patient_id", "trial_id"),
    )


class TrialSubjectVisit(Base):
    """
    Actual visit occurrences for trial subjects
    """
    __tablename__ = "trial_subject_visits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    trial_subject_id = Column(UUID(as_uuid=True), ForeignKey("trial_subjects.id", ondelete="CASCADE"), nullable=False)
    trial_visit_id = Column(UUID(as_uuid=True), ForeignKey("trial_visits.id"), nullable=False)
    planned_date = Column(Date, nullable=False)
    actual_date = Column(Date)
    status = Column(String(50), nullable=False, default='planned')  # 'planned', 'completed', 'missed'
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    protocol_deviation = Column(Boolean, nullable=False, default=False)
    deviation_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trial_subject = relationship("TrialSubject", back_populates="subject_visits")
    trial_visit = relationship("TrialVisit", back_populates="subject_visits")
    encounter = relationship("Encounter")
    crf_responses = relationship("TrialCRFResponse", back_populates="trial_subject_visit")

    # Indexes
    __table_args__ = (
        Index("idx_trial_subject_visits_subject", "trial_subject_id", "planned_date"),
    )


class TrialCRF(Base):
    """
    Case Report Forms definition for trials
    """
    __tablename__ = "trial_crfs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    trial_id = Column(UUID(as_uuid=True), ForeignKey("trials.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(100), nullable=False)  # 'BASELINE', 'V1', 'ADVERSE_EVENT'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    visit_code = Column(String(50))  # link to trial_visits.code
    schema = Column(JSONB, nullable=False)  # form fields, types, constraints
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    trial = relationship("Trial", back_populates="crfs")
    responses = relationship("TrialCRFResponse", back_populates="trial_crf")

    # Indexes
    __table_args__ = (
        Index("uniq_trial_crf_code", "trial_id", "code", unique=True),
    )


class TrialCRFResponse(Base):
    """
    Completed CRF responses from trial subjects
    """
    __tablename__ = "trial_crf_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    trial_subject_id = Column(UUID(as_uuid=True), ForeignKey("trial_subjects.id", ondelete="CASCADE"), nullable=False)
    trial_crf_id = Column(UUID(as_uuid=True), ForeignKey("trial_crfs.id"), nullable=False)
    trial_subject_visit_id = Column(UUID(as_uuid=True), ForeignKey("trial_subject_visits.id"))
    responses = Column(JSONB, nullable=False)
    completed_at = Column(DateTime(timezone=True))
    completed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    source = Column(String(50), nullable=False)  # 'research_staff', 'patient_portal', 'import'
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trial_subject = relationship("TrialSubject", back_populates="crf_responses")
    trial_crf = relationship("TrialCRF", back_populates="responses")
    trial_subject_visit = relationship("TrialSubjectVisit", back_populates="crf_responses")
    completed_by = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_trial_crf_responses_subj_crf", "trial_subject_id", "trial_crf_id"),
    )


class TrialProtocolDeviation(Base):
    """
    Protocol deviations tracking for trials
    """
    __tablename__ = "trial_protocol_deviations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    trial_subject_id = Column(UUID(as_uuid=True), ForeignKey("trial_subjects.id", ondelete="CASCADE"), nullable=False)
    trial_visit_id = Column(UUID(as_uuid=True), ForeignKey("trial_visits.id"))
    deviation_date = Column(Date, nullable=False)
    deviation_type = Column(String(100), nullable=False)  # 'missed_visit', 'out_of_window', 'unauthorized_med', 'other'
    description = Column(Text)
    severity = Column(String(20))  # 'minor', 'major', 'critical'
    reported_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    trial_subject = relationship("TrialSubject", back_populates="protocol_deviations")
    trial_visit = relationship("TrialVisit")
    reported_by = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_trial_protocol_deviations_subject", "trial_subject_id", "deviation_date"),
    )


# --- Guideline/CDS Models ---

class Guideline(Base):
    """
    Clinical guidelines/protocols for decision support
    """
    __tablename__ = "guidelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'HF_CHRONIC', 'SEPSIS_ED', 'STROKE_TPA'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    specialty = Column(String(100))
    source_reference = Column(Text)  # URL/identifier of original guideline
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    versions = relationship("GuidelineVersion", back_populates="guideline", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("uniq_guideline_code_tenant", "tenant_id", "code", unique=True),
    )


class GuidelineVersion(Base):
    """
    Versioned guideline implementations
    """
    __tablename__ = "guideline_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    guideline_id = Column(UUID(as_uuid=True), ForeignKey("guidelines.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(50), nullable=False)  # 'v1', 'v1.1', '2025'
    status = Column(String(50), nullable=False, default='draft')  # 'draft', 'active', 'deprecated'
    narrative_summary = Column(Text)  # human-readable summary
    logic_bundle = Column(JSONB, nullable=False)  # aggregated DSL for all rules/flows
    effective_from = Column(Date)
    effective_to = Column(Date)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    activated_at = Column(DateTime(timezone=True))
    deprecated_at = Column(DateTime(timezone=True))

    # Relationships
    guideline = relationship("Guideline", back_populates="versions")
    cds_rules = relationship("CDSRule", back_populates="guideline_version", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("uniq_guideline_version", "guideline_id", "version", unique=True),
    )


class CDSRule(Base):
    """
    Individual CDS rules within guideline versions
    """
    __tablename__ = "cds_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    guideline_version_id = Column(UUID(as_uuid=True), ForeignKey("guideline_versions.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(100), nullable=False)  # 'RULE_HF_START_ACEI', 'RULE_SEPSIS_LACTATE'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    trigger_context = Column(String(100), nullable=False)  # 'OPD_VISIT', 'IPD_ADMISSION', 'LAB_RESULT', 'MED_ORDER'
    priority = Column(String(20), nullable=False, default='info')  # 'info', 'warning', 'critical'
    logic_expression = Column(JSONB, nullable=False)  # DSL referencing patient data
    action_suggestions = Column(JSONB)  # template suggestions
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    guideline_version = relationship("GuidelineVersion", back_populates="cds_rules")
    triggers = relationship("CDSRuleTrigger", back_populates="cds_rule", cascade="all, delete-orphan")
    evaluations = relationship("CDSEvaluation", back_populates="cds_rule")

    # Indexes
    __table_args__ = (
        Index("idx_cds_rules_guideline", "guideline_version_id", "trigger_context"),
    )


class CDSRuleTrigger(Base):
    """
    Event triggers for CDS rules
    """
    __tablename__ = "cds_rule_triggers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    cds_rule_id = Column(UUID(as_uuid=True), ForeignKey("cds_rules.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)  # 'Encounter.OPD.Created', 'Order.Created', 'Observation.New'
    filter = Column(JSONB)  # optional filter on event payload
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    cds_rule = relationship("CDSRule", back_populates="triggers")


class CDSEvaluation(Base):
    """
    Log of CDS rule evaluations
    """
    __tablename__ = "cds_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    cds_rule_id = Column(UUID(as_uuid=True), ForeignKey("cds_rules.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id"))
    evaluation_time = Column(DateTime(timezone=True), nullable=False)
    trigger_event_type = Column(String(100))
    trigger_event_id = Column(String(255))
    result = Column(String(50), nullable=False)  # 'fired', 'not_fired', 'error'
    card_payload = Column(JSONB)  # CDS card content if fired
    accepted = Column(Boolean)  # whether clinician accepted suggestion
    accepted_at = Column(DateTime(timezone=True))
    acted_on_resource_ids = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    cds_rule = relationship("CDSRule", back_populates="evaluations")
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    admission = relationship("Admission")

    # Indexes
    __table_args__ = (
        Index("idx_cds_evaluations_patient", "patient_id", "evaluation_time"),
    )


# --- Synthetic Data Models ---

class SyntheticDataProfile(Base):
    """
    Profiles for synthetic data generation
    """
    __tablename__ = "synthetic_data_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'HF_SANDBOX', 'ICU_SIM_2025'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_population = Column(JSONB, nullable=False)  # { "registry_code": "HF_REGISTRY", "period": {...} }
    variables = Column(JSONB, nullable=False)  # list of variables to model
    method = Column(String(50), nullable=False)  # 'GAN', 'VAEs', 'copula', 'rules_based'
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    synthetic_data_jobs = relationship("SyntheticDataJob", back_populates="synthetic_data_profile")

    # Indexes
    __table_args__ = (
        Index("uniq_synth_profile_code_tenant", "tenant_id", "code", unique=True),
    )


class SyntheticDataJob(Base):
    """
    Batch jobs for generating synthetic datasets
    """
    __tablename__ = "synthetic_data_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    synthetic_data_profile_id = Column(UUID(as_uuid=True), ForeignKey("synthetic_data_profiles.id"), nullable=False)
    requested_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), nullable=False, default='queued')  # 'queued', 'running', 'completed', 'failed'
    requested_samples = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    synthetic_data_profile = relationship("SyntheticDataProfile", back_populates="synthetic_data_jobs")
    requested_by = relationship("User")
    outputs = relationship("SyntheticDataOutput", back_populates="synthetic_data_job", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_synth_job_status", "status", "created_at"),
    )


class SyntheticDataOutput(Base):
    """
    Outputs from synthetic data generation jobs
    """
    __tablename__ = "synthetic_data_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    synthetic_data_job_id = Column(UUID(as_uuid=True), ForeignKey("synthetic_data_jobs.id", ondelete="CASCADE"), nullable=False)
    output_type = Column(String(50), nullable=False)  # 'parquet', 'csv', 'fhir_bundle'
    location = Column(Text, nullable=False)
    sample_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    synthetic_data_job = relationship("SyntheticDataJob", back_populates="outputs")


# --- Knowledge Graph Models ---

class KGNode(Base):
    """
    Global medical knowledge graph nodes (concepts)
    """
    __tablename__ = "kg_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    code_system = Column(String(50))  # 'SNOMED', 'ICD10', 'LOINC', 'RXNORM', 'INTERNAL'
    code = Column(String(100))
    label = Column(String(255), nullable=False)
    node_type = Column(String(50), nullable=False)  # 'condition', 'lab', 'medication', 'procedure', 'guideline', 'risk_factor'
    meta_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    outgoing_edges = relationship("KGEdge", foreign_keys="KGEdge.source_node_id", back_populates="source_node")
    incoming_edges = relationship("KGEdge", foreign_keys="KGEdge.target_node_id", back_populates="target_node")
    patient_instances = relationship("PatientKGNode", back_populates="kg_node")

    # Indexes
    __table_args__ = (
        Index("idx_kg_nodes_code", "code_system", "code"),
    )


class KGEdge(Base):
    """
    Relationships between knowledge graph concepts
    """
    __tablename__ = "kg_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("kg_nodes.id"), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("kg_nodes.id"), nullable=False)
    relationship_type = Column(String(100), nullable=False)  # 'associated_with', 'contraindicates', 'treats', 'is_risk_factor_for', 'measures'
    weight = Column(Numeric)  # strength of relationship
    evidence_level = Column(String(50))  # 'RCT', 'observational', 'guideline', 'expert_opinion'
    evidence_source = Column(Text)  # citation string or reference ID
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    source_node = relationship("KGNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("KGNode", foreign_keys=[target_node_id], back_populates="incoming_edges")

    # Indexes
    __table_args__ = (
        Index("idx_kg_edges_source", "source_node_id", "relationship_type"),
        Index("idx_kg_edges_target", "target_node_id", "relationship_type"),
    )


class PatientKGNode(Base):
    """
    Patient-specific instances of knowledge graph concepts
    """
    __tablename__ = "patient_kg_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    kg_node_id = Column(UUID(as_uuid=True), ForeignKey("kg_nodes.id"))
    instance_type = Column(String(50), nullable=False)  # 'diagnosis', 'lab_result', 'med_order', 'visit', 'event'
    fhir_resource_type = Column(String(100))
    fhir_resource_id = Column(String(255))
    occurred_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    patient = relationship("Patient")
    kg_node = relationship("KGNode", back_populates="patient_instances")
    outgoing_edges = relationship("PatientKGEdge", foreign_keys="PatientKGEdge.source_instance_id", back_populates="source_instance")
    incoming_edges = relationship("PatientKGEdge", foreign_keys="PatientKGEdge.target_instance_id", back_populates="target_instance")

    # Indexes
    __table_args__ = (
        Index("idx_patient_kg_nodes_patient", "patient_id", "occurred_at"),
    )


class PatientKGEdge(Base):
    """
    Relationships between patient-specific knowledge graph instances
    """
    __tablename__ = "patient_kg_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    source_instance_id = Column(UUID(as_uuid=True), ForeignKey("patient_kg_nodes.id"), nullable=False)
    target_instance_id = Column(UUID(as_uuid=True), ForeignKey("patient_kg_nodes.id"), nullable=False)
    relationship_type = Column(String(100), nullable=False)  # 'temporal_before', 'causal_suspected', 'co_occurs', 'same_episode'
    created_by = Column(String(50), nullable=False)  # 'rules', 'llm_agent', 'user'
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    patient = relationship("Patient")
    source_instance = relationship("PatientKGNode", foreign_keys=[source_instance_id], back_populates="outgoing_edges")
    target_instance = relationship("PatientKGNode", foreign_keys=[target_instance_id], back_populates="incoming_edges")

    # Indexes
    __table_args__ = (
        Index("idx_patient_kg_edges_patient", "patient_id"),
    )


# ============================================================================
# PHASE 7 - IMAGING, PACS & DIAGNOSTICS PLATFORM (15 Models)
# ============================================================================

# Imaging Order Service Models (3 models)

class ImagingModality(Base):
    """
    Imaging modalities (CT, MR, US, XR, etc.)
    """
    __tablename__ = "imaging_modalities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(50), nullable=False)  # 'CR', 'CT', 'MR', 'US', 'DX', 'MG', 'XA', 'NM', 'PT'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    imaging_procedures = relationship("ImagingProcedure", back_populates="modality")

    # Indexes
    __table_args__ = (
        Index("uniq_imaging_modality_code_tenant", "tenant_id", "code", unique=True),
    )


class ImagingProcedure(Base):
    """
    Imaging procedure catalog (CT Brain w/ contrast, US Abdomen Complete, etc.)
    """
    __tablename__ = "imaging_procedures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'CT_BRAIN_WO_CONTRAST', 'US_ABD_COMPLETE'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    modality_id = Column(UUID(as_uuid=True), ForeignKey("imaging_modalities.id"), nullable=False)
    body_part = Column(String(100))  # 'BRAIN', 'CHEST', 'ABDOMEN'
    snomed_code = Column(String(50))
    loinc_code = Column(String(50))
    default_duration_minutes = Column(Integer)
    preparation_instructions = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    modality = relationship("ImagingModality", back_populates="imaging_procedures")
    imaging_orders = relationship("ImagingOrder", back_populates="imaging_procedure")

    # Indexes
    __table_args__ = (
        Index("uniq_imaging_procedure_code_tenant", "tenant_id", "code", unique=True),
    )


class ImagingOrder(Base):
    """
    Imaging orders (ServiceRequest in FHIR)
    """
    __tablename__ = "imaging_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"))
    ordering_practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    ordering_department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    imaging_procedure_id = Column(UUID(as_uuid=True), ForeignKey("imaging_procedures.id"), nullable=False)
    indication = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default='routine')  # 'routine', 'urgent', 'stat'
    status = Column(String(50), nullable=False, default='requested')  # 'requested', 'scheduled', 'in_progress', 'completed', 'cancelled'
    requested_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    scheduled_slot_id = Column(UUID(as_uuid=True))
    performed_start_at = Column(DateTime(timezone=True))
    performed_end_at = Column(DateTime(timezone=True))
    fhir_service_request_id = Column(String(255))
    meta_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    episode = relationship("Episode")
    ordering_practitioner = relationship("Practitioner", foreign_keys=[ordering_practitioner_id])
    imaging_procedure = relationship("ImagingProcedure", back_populates="imaging_orders")
    imaging_studies = relationship("ImagingStudy", back_populates="imaging_order")

    # Indexes
    __table_args__ = (
        Index("idx_imaging_orders_patient", "patient_id", "requested_at"),
        Index("idx_imaging_orders_status", "status", "priority", "requested_at"),
    )


# PACS Connector Service Models (4 models)

class PACSEndpoint(Base):
    """
    PACS/VNA endpoints for DICOM integration
    """
    __tablename__ = "pacs_endpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'MAIN_PACS', 'CLOUD_PACS'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    ae_title = Column(String(50))  # DICOM AE title
    host = Column(String(255))
    port = Column(Integer)
    protocol = Column(String(50), nullable=False)  # 'DICOM', 'DICOMWeb', 'WADO_RS'
    auth_config = Column(JSONB)  # tokens, basic auth, etc.
    viewer_launch_url = Column(Text)  # template URL for embedding viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    imaging_studies = relationship("ImagingStudy", back_populates="pacs_endpoint")

    # Indexes
    __table_args__ = (
        Index("uniq_pacs_endpoint_code_tenant", "tenant_id", "code", unique=True),
    )


class ImagingStudy(Base):
    """
    Imaging studies (FHIR ImagingStudy)
    """
    __tablename__ = "imaging_studies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    imaging_order_id = Column(UUID(as_uuid=True), ForeignKey("imaging_orders.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    pacs_endpoint_id = Column(UUID(as_uuid=True), ForeignKey("pacs_endpoints.id"), nullable=False)
    study_instance_uid = Column(String(255), nullable=False)
    accession_number = Column(String(100))
    modality_code = Column(String(50), nullable=False)  # 'CT', 'MR', 'US', etc.
    description = Column(Text)
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    number_of_series = Column(Integer)
    number_of_instances = Column(Integer)
    fhir_imaging_study_id = Column(String(255))
    viewer_url = Column(Text)  # pre-built URL with token
    status = Column(String(50), nullable=False, default='available')  # 'available', 'archived', 'unavailable'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    imaging_order = relationship("ImagingOrder", back_populates="imaging_studies")
    patient = relationship("Patient")
    pacs_endpoint = relationship("PACSEndpoint", back_populates="imaging_studies")
    imaging_series = relationship("ImagingSeries", back_populates="imaging_study", cascade="all, delete-orphan")
    radiology_worklist_items = relationship("RadiologyWorklistItem", back_populates="imaging_study")
    radiology_reports = relationship("RadiologyReport", back_populates="imaging_study")
    imaging_ai_tasks = relationship("ImagingAITask", back_populates="imaging_study")

    # Indexes
    __table_args__ = (
        Index("uniq_imaging_study_uid_tenant", "tenant_id", "study_instance_uid", unique=True),
        Index("idx_imaging_studies_patient", "patient_id", "started_at"),
    )


class ImagingSeries(Base):
    """
    DICOM series within an imaging study
    """
    __tablename__ = "imaging_series"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    imaging_study_id = Column(UUID(as_uuid=True), ForeignKey("imaging_studies.id", ondelete="CASCADE"), nullable=False)
    series_instance_uid = Column(String(255), nullable=False)
    series_number = Column(Integer)
    body_part = Column(String(100))
    modality_code = Column(String(50))
    number_of_instances = Column(Integer)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    imaging_study = relationship("ImagingStudy", back_populates="imaging_series")
    imaging_instances = relationship("ImagingInstance", back_populates="imaging_series", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("uniq_imaging_series_uid", "imaging_study_id", "series_instance_uid", unique=True),
    )


class ImagingInstance(Base):
    """
    DICOM instances (individual images)
    """
    __tablename__ = "imaging_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    imaging_series_id = Column(UUID(as_uuid=True), ForeignKey("imaging_series.id", ondelete="CASCADE"), nullable=False)
    sop_instance_uid = Column(String(255), nullable=False)
    instance_number = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    imaging_series = relationship("ImagingSeries", back_populates="imaging_instances")

    # Indexes
    __table_args__ = (
        Index("uniq_imaging_instance_uid", "imaging_series_id", "sop_instance_uid", unique=True),
    )


# Radiology Worklist Service Models (2 models)

class RadiologyReadingProfile(Base):
    """
    Radiologist capabilities and preferences
    """
    __tablename__ = "radiology_reading_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"), nullable=False)
    allowed_modalities = Column(ARRAY(String))  # ['CT', 'MR', 'US']
    allowed_body_parts = Column(ARRAY(String))  # ['BRAIN', 'CHEST']
    max_concurrent_cases = Column(Integer, default=5)
    reading_locations = Column(ARRAY(String))  # ['MAIN_RAD_DEPT', 'REMOTE']
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    practitioner = relationship("Practitioner")

    # Indexes
    __table_args__ = (
        Index("uniq_radiology_reading_profile", "tenant_id", "practitioner_id", unique=True),
    )


class RadiologyWorklistItem(Base):
    """
    Radiology worklist items for assignment and tracking
    """
    __tablename__ = "radiology_worklist_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    imaging_study_id = Column(UUID(as_uuid=True), ForeignKey("imaging_studies.id"), nullable=False)
    imaging_order_id = Column(UUID(as_uuid=True), ForeignKey("imaging_orders.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    modality_code = Column(String(50), nullable=False)
    body_part = Column(String(100))
    priority = Column(String(20), nullable=False)  # 'routine', 'urgent', 'stat'
    status = Column(String(50), nullable=False, default='pending')  # 'pending', 'claimed', 'in_progress', 'reported'
    assigned_radiologist_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    claimed_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True))
    ai_triage_score = Column(Numeric)  # Probability of critical finding
    ai_triage_flags = Column(JSONB)  # ['ICH_suspected', 'PE_suspected']
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    imaging_study = relationship("ImagingStudy", back_populates="radiology_worklist_items")
    patient = relationship("Patient")
    assigned_radiologist = relationship("Practitioner", foreign_keys=[assigned_radiologist_id])

    # Indexes
    __table_args__ = (
        Index("idx_radiology_worklist_status_priority", "status", "priority", "created_at"),
        Index("idx_radiology_worklist_assigned", "assigned_radiologist_id", "status"),
    )


# Radiology Reporting Service Models (4 models)

class RadiologyReportTemplate(Base):
    """
    Radiology report templates for structured reporting
    """
    __tablename__ = "radiology_report_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'CT_HEAD_STROKE', 'US_ABD_GENERAL'
    name = Column(String(255), nullable=False)
    modality_code = Column(String(50))
    body_part = Column(String(100))
    description = Column(Text)
    template_type = Column(String(50), nullable=False)  # 'free_text', 'structured', 'hybrid'
    schema = Column(JSONB)  # for structured fields
    default_text = Column(Text)  # base narrative template
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    radiology_reports = relationship("RadiologyReport", back_populates="template")

    # Indexes
    __table_args__ = (
        Index("uniq_radiology_report_template_code", "tenant_id", "code", unique=True),
    )


class RadiologyReport(Base):
    """
    Radiology diagnostic reports (FHIR DiagnosticReport)
    """
    __tablename__ = "radiology_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    imaging_study_id = Column(UUID(as_uuid=True), ForeignKey("imaging_studies.id"), nullable=False)
    imaging_order_id = Column(UUID(as_uuid=True), ForeignKey("imaging_orders.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    radiologist_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    template_id = Column(UUID(as_uuid=True), ForeignKey("radiology_report_templates.id"))
    status = Column(String(50), nullable=False, default='draft')  # 'draft', 'preliminary', 'final', 'corrected', 'cancelled'
    clinical_history = Column(Text)
    technique = Column(Text)
    findings = Column(Text)
    impression = Column(Text)
    structured_data = Column(JSONB)  # for structured findings (e.g., BI-RADS)
    ai_assist_summary = Column(JSONB)  # AI suggestions used in draft
    critical_result = Column(Boolean, default=False)
    critical_communication_logged = Column(Boolean, default=False)
    critical_communication_details = Column(Text)
    signed_at = Column(DateTime(timezone=True))
    signed_by_radiologist_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    fhir_diagnostic_report_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    imaging_study = relationship("ImagingStudy", back_populates="radiology_reports")
    patient = relationship("Patient")
    radiologist = relationship("Practitioner", foreign_keys=[radiologist_id])
    signed_by_radiologist = relationship("Practitioner", foreign_keys=[signed_by_radiologist_id])
    template = relationship("RadiologyReportTemplate", back_populates="radiology_reports")
    sections = relationship("RadiologyReportSection", back_populates="radiology_report", cascade="all, delete-orphan")
    addenda = relationship("RadiologyReportAddendum", back_populates="radiology_report", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_radiology_reports_patient", "patient_id", "created_at"),
        Index("idx_radiology_reports_study", "imaging_study_id"),
    )


class RadiologyReportSection(Base):
    """
    Granular sections within radiology reports
    """
    __tablename__ = "radiology_report_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    radiology_report_id = Column(UUID(as_uuid=True), ForeignKey("radiology_reports.id", ondelete="CASCADE"), nullable=False)
    section_code = Column(String(50), nullable=False)  # 'FINDINGS', 'IMPRESSION', 'TECHNIQUE'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    radiology_report = relationship("RadiologyReport", back_populates="sections")


class RadiologyReportAddendum(Base):
    """
    Addenda to radiology reports for corrections or additional information
    """
    __tablename__ = "radiology_report_addenda"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    radiology_report_id = Column(UUID(as_uuid=True), ForeignKey("radiology_reports.id", ondelete="CASCADE"), nullable=False)
    added_by_radiologist_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    radiology_report = relationship("RadiologyReport", back_populates="addenda")
    added_by_radiologist = relationship("Practitioner")


# Imaging AI Orchestrator Service Models (3 models)

class ImagingAIModel(Base):
    """
    AI models for imaging analysis (triage, quality, detection, etc.)
    """
    __tablename__ = "imaging_ai_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    code = Column(String(100), nullable=False)  # 'CT_HEAD_ICH_TRIAGE', 'CXR_PNEUMONIA_DET'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    modality_code = Column(String(50))
    body_part = Column(String(100))
    capabilities = Column(JSONB)  # {"triage": true, "segmentation": false}
    vendor = Column(String(255))
    version = Column(String(50))
    endpoint_config = Column(JSONB)  # inference endpoint details
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    imaging_ai_tasks = relationship("ImagingAITask", back_populates="ai_model")

    # Indexes
    __table_args__ = (
        Index("uniq_imaging_ai_model_code", "code", unique=True),
    )


class ImagingAITask(Base):
    """
    AI processing tasks for imaging studies
    """
    __tablename__ = "imaging_ai_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    imaging_study_id = Column(UUID(as_uuid=True), ForeignKey("imaging_studies.id"), nullable=False)
    ai_model_id = Column(UUID(as_uuid=True), ForeignKey("imaging_ai_models.id"), nullable=False)
    task_type = Column(String(50), nullable=False)  # 'triage', 'quality', 'pre_report', 'comparison'
    status = Column(String(50), nullable=False, default='queued')  # 'queued', 'running', 'completed', 'failed'
    requested_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    imaging_study = relationship("ImagingStudy", back_populates="imaging_ai_tasks")
    ai_model = relationship("ImagingAIModel", back_populates="imaging_ai_tasks")
    outputs = relationship("ImagingAIOutput", back_populates="imaging_ai_task", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_imaging_ai_tasks_study", "imaging_study_id", "task_type"),
    )


class ImagingAIOutput(Base):
    """
    AI analysis outputs for imaging tasks
    """
    __tablename__ = "imaging_ai_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    imaging_ai_task_id = Column(UUID(as_uuid=True), ForeignKey("imaging_ai_tasks.id", ondelete="CASCADE"), nullable=False)
    output_type = Column(String(50), nullable=False)  # 'triage', 'finding_list', 'bbox', 'suggested_report'
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    imaging_ai_task = relationship("ImagingAITask", back_populates="outputs")


# ============================================================================
# Phase 8: Laboratory & Pathology Platform Models
# ============================================================================

# ===== Lab Catalog Service Models =====

class LabSpecimenType(Base):
    """
    Laboratory specimen types (blood, urine, tissue, etc.)
    """
    __tablename__ = "lab_specimen_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'VEN_BLOOD', 'URINE', 'CSF', 'TISSUE'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    container_type = Column(String(100))  # 'EDTA_TUBE', 'SST_TUBE', etc.
    handling_instructions = Column(Text)
    storage_temperature_range = Column(String(50))  # '2-8C'
    stability_hours = Column(Integer)  # how long before result invalid
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lab_tests = relationship("LabTest", back_populates="default_specimen_type")
    lab_specimens = relationship("LabSpecimen", back_populates="specimen_type")

    __table_args__ = (
        Index('idx_lab_specimen_type_tenant_code', 'tenant_id', 'code', unique=True),
    )


class LabTest(Base):
    """
    Laboratory test catalog (individual tests and panels)
    """
    __tablename__ = "lab_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'CBC', 'HB', 'FBS', 'CRP', 'CREAT'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    loinc_code = Column(String(100))
    category = Column(String(100))  # 'hematology', 'chemistry', 'immunology', 'micro', 'pathology'
    default_specimen_type_id = Column(UUID(as_uuid=True), ForeignKey("lab_specimen_types.id"))
    unit = Column(String(50))
    reference_range = Column(JSONB)  # {"adult_male": "13-17 g/dL", ...}
    critical_range = Column(JSONB)  # {"low": "< 6", "high": "> 20"}
    is_panel = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    result_type = Column(String(50), nullable=False, default='numeric')  # 'numeric', 'text', 'categorical', 'qualitative'
    result_value_set = Column(JSONB)  # for categorical (e.g., ['Positive','Negative'])
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    default_specimen_type = relationship("LabSpecimenType", back_populates="lab_tests")
    lab_order_items = relationship("LabOrderItem", back_populates="lab_test")
    lab_results = relationship("LabResult", back_populates="lab_test")
    lab_result_values = relationship("LabResultValue", back_populates="component_lab_test")
    lab_test_panel = relationship("LabTestPanel", back_populates="lab_test", uselist=False)
    panel_items = relationship("LabTestPanelItem", back_populates="child_lab_test")

    __table_args__ = (
        Index('idx_lab_test_tenant_code', 'tenant_id', 'code', unique=True),
    )


class LabTestPanel(Base):
    """
    Lab test panels (profiles like LFT, RFT, Lipid Profile)
    """
    __tablename__ = "lab_test_panels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    lab_test_id = Column(UUID(as_uuid=True), ForeignKey("lab_tests.id", ondelete="CASCADE"), nullable=False)
    panel_code = Column(String(100), nullable=False, unique=True)  # 'LFT', 'RFT', 'LIPID_PROFILE'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    lab_test = relationship("LabTest", back_populates="lab_test_panel")
    panel_items = relationship("LabTestPanelItem", back_populates="panel", cascade="all, delete-orphan")


class LabTestPanelItem(Base):
    """
    Individual tests within a panel
    """
    __tablename__ = "lab_test_panel_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    lab_test_panel_id = Column(UUID(as_uuid=True), ForeignKey("lab_test_panels.id", ondelete="CASCADE"), nullable=False)
    child_lab_test_id = Column(UUID(as_uuid=True), ForeignKey("lab_tests.id"), nullable=False)
    sort_order = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    panel = relationship("LabTestPanel", back_populates="panel_items")
    child_lab_test = relationship("LabTest", back_populates="panel_items")


# ===== Lab Order Service Models =====

class LabOrder(Base):
    """
    Lab orders (requests) from OPD/IPD/ED
    """
    __tablename__ = "lab_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"))
    ordering_practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    ordering_department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    priority = Column(String(20), nullable=False, default='routine')  # 'routine', 'urgent', 'stat'
    status = Column(String(50), nullable=False, default='requested')  # 'requested', 'collected', 'in_progress', 'completed', 'cancelled', 'rejected'
    clinical_indication = Column(Text)
    requested_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    collected_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    fhir_service_request_bundle_id = Column(String(255))  # group of ServiceRequests
    meta_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    episode = relationship("Episode")
    ordering_practitioner = relationship("Practitioner", foreign_keys=[ordering_practitioner_id])
    ordering_department = relationship("Department")
    order_items = relationship("LabOrderItem", back_populates="lab_order", cascade="all, delete-orphan")
    lab_specimens = relationship("LabSpecimen", back_populates="lab_order")
    lab_results = relationship("LabResult", back_populates="lab_order")

    __table_args__ = (
        Index('idx_lab_orders_patient', 'patient_id', 'requested_at'),
        Index('idx_lab_orders_status', 'status', 'requested_at'),
    )


class LabOrderItem(Base):
    """
    Individual tests or panels within a lab order
    """
    __tablename__ = "lab_order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    lab_order_id = Column(UUID(as_uuid=True), ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False)
    lab_test_id = Column(UUID(as_uuid=True), ForeignKey("lab_tests.id"), nullable=False)
    is_panel = Column(Boolean, default=False)
    status = Column(String(50), nullable=False, default='ordered')  # 'ordered', 'cancelled'
    requested_specimen_type_id = Column(UUID(as_uuid=True), ForeignKey("lab_specimen_types.id"))
    result_group_id = Column(UUID(as_uuid=True))  # for linking to results
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lab_order = relationship("LabOrder", back_populates="order_items")
    lab_test = relationship("LabTest", back_populates="lab_order_items")
    requested_specimen_type = relationship("LabSpecimenType")
    lab_results = relationship("LabResult", back_populates="lab_order_item")

    __table_args__ = (
        Index('idx_lab_order_items_order', 'lab_order_id'),
    )


# ===== Lab Specimen Tracking Service Models =====

class LabSpecimen(Base):
    """
    Specimen lifecycle tracking
    """
    __tablename__ = "lab_specimens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    lab_order_id = Column(UUID(as_uuid=True), ForeignKey("lab_orders.id"), nullable=False)
    specimen_identifier = Column(String(255), nullable=False)  # barcode / label ID
    specimen_type_id = Column(UUID(as_uuid=True), ForeignKey("lab_specimen_types.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    collection_time = Column(DateTime(timezone=True))
    collection_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"))
    collected_by_user_id = Column(UUID(as_uuid=True))
    status = Column(String(50), nullable=False, default='pending_collection')  # 'pending_collection', 'collected', 'in_transit', 'received', 'processing', 'stored', 'discarded'
    received_time = Column(DateTime(timezone=True))
    received_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"))
    volume_ml = Column(Numeric(10, 2))
    comments = Column(Text)
    fhir_specimen_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lab_order = relationship("LabOrder", back_populates="lab_specimens")
    specimen_type = relationship("LabSpecimenType", back_populates="lab_specimens")
    patient = relationship("Patient")
    collection_location = relationship("Location", foreign_keys=[collection_location_id])
    received_location = relationship("Location", foreign_keys=[received_location_id])
    specimen_events = relationship("LabSpecimenEvent", back_populates="lab_specimen", cascade="all, delete-orphan")
    lab_results = relationship("LabResult", back_populates="specimen")

    __table_args__ = (
        Index('idx_lab_specimen_tenant_identifier', 'tenant_id', 'specimen_identifier', unique=True),
        Index('idx_lab_specimens_order', 'lab_order_id'),
    )


class LabSpecimenEvent(Base):
    """
    Specimen lifecycle events (collection, transport, receipt, etc.)
    """
    __tablename__ = "lab_specimen_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    lab_specimen_id = Column(UUID(as_uuid=True), ForeignKey("lab_specimens.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)  # 'label_printed', 'collected', 'sent_to_lab', 'received', 'aliquoted', 'stored', 'discarded'
    event_time = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"))
    performed_by_user_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    lab_specimen = relationship("LabSpecimen", back_populates="specimen_events")
    location = relationship("Location")

    __table_args__ = (
        Index('idx_lab_specimen_events_specimen', 'lab_specimen_id', 'event_time'),
    )


# ===== Lab Result Service Models =====

class LabResult(Base):
    """
    Lab results from analyzers / LIS
    """
    __tablename__ = "lab_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    lab_order_id = Column(UUID(as_uuid=True), ForeignKey("lab_orders.id"), nullable=False)
    lab_order_item_id = Column(UUID(as_uuid=True), ForeignKey("lab_order_items.id"))
    lab_test_id = Column(UUID(as_uuid=True), ForeignKey("lab_tests.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    specimen_id = Column(UUID(as_uuid=True), ForeignKey("lab_specimens.id"))
    analyzer_run_id = Column(String(255))  # optional from instrument
    status = Column(String(50), nullable=False, default='preliminary')  # 'preliminary', 'final', 'corrected', 'cancelled'
    result_time = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    validated_by_user_id = Column(UUID(as_uuid=True))
    validated_at = Column(DateTime(timezone=True))
    entered_by_user_id = Column(UUID(as_uuid=True))
    entry_source = Column(String(50))  # 'manual', 'analyzer_import'
    comments = Column(Text)
    is_critical = Column(Boolean, default=False)
    critical_notified = Column(Boolean, default=False)
    critical_notification_details = Column(Text)
    fhir_observation_id = Column(String(255))
    fhir_diagnostic_report_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lab_order = relationship("LabOrder", back_populates="lab_results")
    lab_order_item = relationship("LabOrderItem", back_populates="lab_results")
    lab_test = relationship("LabTest", back_populates="lab_results")
    patient = relationship("Patient")
    specimen = relationship("LabSpecimen", back_populates="lab_results")
    result_values = relationship("LabResultValue", back_populates="lab_result", cascade="all, delete-orphan")
    micro_organisms = relationship("LabMicroOrganism", back_populates="lab_result", cascade="all, delete-orphan")
    lab_ai_tasks = relationship("LabAITask", back_populates="lab_result")

    __table_args__ = (
        Index('idx_lab_results_patient', 'patient_id', 'result_time'),
        Index('idx_lab_results_order_item', 'lab_order_item_id'),
    )


class LabResultValue(Base):
    """
    Multi-component test values (for panels)
    """
    __tablename__ = "lab_result_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    lab_result_id = Column(UUID(as_uuid=True), ForeignKey("lab_results.id", ondelete="CASCADE"), nullable=False)
    component_lab_test_id = Column(UUID(as_uuid=True), ForeignKey("lab_tests.id"))
    component_code = Column(String(100))  # fallback if no lab_test row
    value_numeric = Column(Numeric(15, 4))
    value_text = Column(Text)
    value_code = Column(String(100))
    unit = Column(String(50))
    reference_range = Column(String(255))
    flag = Column(String(10))  # 'L', 'H', 'LL', 'HH', 'N', 'A' etc.
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    lab_result = relationship("LabResult", back_populates="result_values")
    component_lab_test = relationship("LabTest", back_populates="lab_result_values")

    __table_args__ = (
        Index('idx_lab_result_values_result', 'lab_result_id'),
    )


class LabMicroOrganism(Base):
    """
    Microbiology organisms (from cultures)
    """
    __tablename__ = "lab_micro_organisms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    lab_result_id = Column(UUID(as_uuid=True), ForeignKey("lab_results.id", ondelete="CASCADE"), nullable=False)
    organism_code = Column(String(100))  # SNOMED or internal
    organism_name = Column(String(255))
    quantity = Column(String(50))  # 'heavy growth', 'scanty'
    comments = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    lab_result = relationship("LabResult", back_populates="micro_organisms")
    susceptibilities = relationship("LabMicroSusceptibility", back_populates="organism", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_lab_micro_organisms_result', 'lab_result_id'),
    )


class LabMicroSusceptibility(Base):
    """
    Antibiotic susceptibility test results
    """
    __tablename__ = "lab_micro_susceptibilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    lab_micro_organism_id = Column(UUID(as_uuid=True), ForeignKey("lab_micro_organisms.id", ondelete="CASCADE"), nullable=False)
    antibiotic_code = Column(String(100))  # ATC or internal
    antibiotic_name = Column(String(255))
    mic_value = Column(Numeric(10, 4))
    mic_unit = Column(String(50))
    interpretation = Column(String(10))  # 'S', 'I', 'R'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    organism = relationship("LabMicroOrganism", back_populates="susceptibilities")

    __table_args__ = (
        Index('idx_lab_micro_susc_organism', 'lab_micro_organism_id'),
    )


# ===== Anatomic Pathology Service Models =====

class APCase(Base):
    """
    Anatomic pathology cases
    """
    __tablename__ = "ap_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    case_number = Column(String(100), nullable=False)  # 'AP-2025-000123'
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    referring_practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    referring_department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    received_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default='accessioned')  # 'accessioned', 'in_progress', 'reported', 'amended', 'cancelled'
    clinical_history = Column(Text)
    diagnosis_summary = Column(Text)
    pathologist_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    fhir_diagnostic_report_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    referring_practitioner = relationship("Practitioner", foreign_keys=[referring_practitioner_id])
    referring_department = relationship("Department")
    pathologist = relationship("Practitioner", foreign_keys=[pathologist_id])
    specimens = relationship("APSpecimen", back_populates="ap_case", cascade="all, delete-orphan")
    reports = relationship("APReport", back_populates="ap_case", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_ap_case_tenant_number', 'tenant_id', 'case_number', unique=True),
        Index('idx_ap_cases_patient', 'patient_id', 'received_date'),
    )


class APSpecimen(Base):
    """
    Tissue specimens within AP cases
    """
    __tablename__ = "ap_specimens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    ap_case_id = Column(UUID(as_uuid=True), ForeignKey("ap_cases.id", ondelete="CASCADE"), nullable=False)
    specimen_identifier = Column(String(255), nullable=False)  # container label
    site = Column(String(255))  # 'colon', 'breast'
    description = Column(Text)  # "Segment of colon, 5cm…"
    procedure = Column(String(255))  # 'polypectomy', 'excision'
    collection_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    ap_case = relationship("APCase", back_populates="specimens")
    blocks = relationship("APBlock", back_populates="ap_specimen", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_ap_specimens_case', 'ap_case_id'),
    )


class APBlock(Base):
    """
    Tissue blocks from specimens
    """
    __tablename__ = "ap_blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    ap_specimen_id = Column(UUID(as_uuid=True), ForeignKey("ap_specimens.id", ondelete="CASCADE"), nullable=False)
    block_identifier = Column(String(100), nullable=False)  # 'A1', 'A2', 'B1'
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    ap_specimen = relationship("APSpecimen", back_populates="blocks")
    slides = relationship("APSlide", back_populates="ap_block", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_ap_blocks_specimen', 'ap_specimen_id'),
    )


class APSlide(Base):
    """
    Microscope slides from blocks
    """
    __tablename__ = "ap_slides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    ap_block_id = Column(UUID(as_uuid=True), ForeignKey("ap_blocks.id", ondelete="CASCADE"), nullable=False)
    slide_identifier = Column(String(100), nullable=False)  # 'A1-1', 'A1-2'
    stain = Column(String(100))  # 'H&E', 'IHC ER', 'PAS'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    ap_block = relationship("APBlock", back_populates="slides")

    __table_args__ = (
        Index('idx_ap_slides_block', 'ap_block_id'),
    )


class APReportTemplate(Base):
    """
    Structured pathology report templates (synoptic reporting)
    """
    __tablename__ = "ap_report_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'BREAST_CA_RESECTION', 'COLON_POLYP'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    site = Column(String(255))
    schema = Column(JSONB, nullable=False)  # synoptic fields (JSON schema-like)
    default_narrative = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ap_reports = relationship("APReport", back_populates="template")

    __table_args__ = (
        Index('idx_ap_report_template_tenant_code', 'tenant_id', 'code', unique=True),
    )


class APReport(Base):
    """
    Pathology diagnostic reports
    """
    __tablename__ = "ap_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    ap_case_id = Column(UUID(as_uuid=True), ForeignKey("ap_cases.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("ap_report_templates.id"))
    status = Column(String(50), nullable=False, default='draft')  # 'draft', 'final', 'amended', 'cancelled'
    gross_description = Column(Text)
    microscopic_description = Column(Text)
    diagnosis_text = Column(Text)
    comments = Column(Text)
    signed_at = Column(DateTime(timezone=True))
    signed_by_pathologist_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ap_case = relationship("APCase", back_populates="reports")
    template = relationship("APReportTemplate", back_populates="ap_reports")
    signed_by_pathologist = relationship("Practitioner", foreign_keys=[signed_by_pathologist_id])
    synoptic_values = relationship("APReportSynopticValue", back_populates="ap_report", cascade="all, delete-orphan")
    lab_ai_tasks = relationship("LabAITask", back_populates="ap_report")

    __table_args__ = (
        Index('idx_ap_reports_case', 'ap_case_id'),
    )


class APReportSynopticValue(Base):
    """
    Structured data fields in pathology reports (TNM staging, margins, etc.)
    """
    __tablename__ = "ap_report_synoptic_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    ap_report_id = Column(UUID(as_uuid=True), ForeignKey("ap_reports.id", ondelete="CASCADE"), nullable=False)
    field_code = Column(String(100), nullable=False)  # 'T_STAGE', 'N_STAGE', 'M_STAGE', 'MARGIN_STATUS'
    value_text = Column(Text)
    value_code = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    ap_report = relationship("APReport", back_populates="synoptic_values")

    __table_args__ = (
        Index('idx_ap_report_synoptic_values_report', 'ap_report_id'),
    )


# ===== Lab AI Orchestrator Service Models =====

class LabAIModel(Base):
    """
    AI model registry for lab interpretation and pathology assistance
    """
    __tablename__ = "lab_ai_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    code = Column(String(100), nullable=False)  # 'LFT_INTERPRETER', 'CBC_TREND', 'MICRO_ABX_ANALYTICS'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    domain = Column(String(50), nullable=False)  # 'core_lab', 'micro', 'ap'
    capabilities = Column(JSONB)
    endpoint_config = Column(JSONB)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lab_ai_tasks = relationship("LabAITask", back_populates="ai_model")


class LabAITask(Base):
    """
    AI processing tasks for lab interpretation and pathology
    """
    __tablename__ = "lab_ai_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    domain = Column(String(50), nullable=False)  # 'core_lab', 'micro', 'ap'
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    lab_result_id = Column(UUID(as_uuid=True), ForeignKey("lab_results.id"))
    ap_report_id = Column(UUID(as_uuid=True), ForeignKey("ap_reports.id"))
    ai_model_id = Column(UUID(as_uuid=True), ForeignKey("lab_ai_models.id"))
    task_type = Column(String(50), nullable=False)  # 'interpretation', 'trend_summary', 'reflex_suggestion', 'synoptic_suggestion'
    status = Column(String(50), nullable=False, default='queued')
    requested_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    lab_result = relationship("LabResult", back_populates="lab_ai_tasks")
    ap_report = relationship("APReport", back_populates="lab_ai_tasks")
    ai_model = relationship("LabAIModel", back_populates="lab_ai_tasks")
    outputs = relationship("LabAIOutput", back_populates="lab_ai_task", cascade="all, delete-orphan")


class LabAIOutput(Base):
    """
    AI analysis outputs for lab and pathology tasks
    """
    __tablename__ = "lab_ai_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    lab_ai_task_id = Column(UUID(as_uuid=True), ForeignKey("lab_ai_tasks.id", ondelete="CASCADE"), nullable=False)
    output_type = Column(String(50), nullable=False)  # 'patient_summary', 'clinician_comment', 'ap_synoptic'
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    lab_ai_task = relationship("LabAITask", back_populates="outputs")


# ============================================================================
# Phase 9: Pharmacy, Medication Management & Supply Chain Models
# ============================================================================

# ===== Medication Catalog Service Models =====

class MedicationMolecule(Base):
    """
    Core drug molecules (generic names)
    """
    __tablename__ = "medication_molecules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    global_code = Column(String(100))  # RxNorm / ATC code
    name = Column(String(255), nullable=False)  # 'Paracetamol'
    synonyms = Column(ARRAY(String))
    atc_code = Column(String(50))
    drug_class = Column(String(255))  # 'Analgesic', 'ACE inhibitor'
    is_controlled_substance = Column(Boolean, default=False)
    is_high_alert = Column(Boolean, default=False)  # narrow therapeutic index
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    medication_products = relationship("MedicationProduct", back_populates="molecule")
    formulary_substitution_from = relationship("FormularySubstitutionRule", foreign_keys="FormularySubstitutionRule.from_molecule_id", back_populates="from_molecule")
    formulary_substitution_to = relationship("FormularySubstitutionRule", foreign_keys="FormularySubstitutionRule.to_molecule_id", back_populates="to_molecule")
    medication_orders = relationship("MedicationOrder", back_populates="molecule")


class MedicationRoute(Base):
    """
    Medication routes (PO, IV, IM, etc.)
    """
    __tablename__ = "medication_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    code = Column(String(50), nullable=False, unique=True)  # 'PO', 'IV', 'IM', 'SC', 'TOP', 'SL'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    medication_products = relationship("MedicationProduct", back_populates="route")
    medication_orders = relationship("MedicationOrder", back_populates="route")
    medication_administrations = relationship("MedicationAdministration", back_populates="route")


class MedicationDoseForm(Base):
    """
    Medication dose forms (tablet, capsule, injection, etc.)
    """
    __tablename__ = "medication_dose_forms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    code = Column(String(50), nullable=False, unique=True)  # 'TAB', 'CAP', 'SUSP', 'INJ', 'SR_TAB'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    medication_products = relationship("MedicationProduct", back_populates="dose_form")
    medication_orders = relationship("MedicationOrder", back_populates="dose_form")


class MedicationProduct(Base):
    """
    Medication products (branded/generic formulations)
    """
    __tablename__ = "medication_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    molecule_id = Column(UUID(as_uuid=True), ForeignKey("medication_molecules.id"), nullable=False)
    brand_name = Column(String(255))  # 'Crocin 500'
    strength = Column(String(100))  # '500 mg'
    strength_numeric = Column(Numeric(15, 4))  # 500
    strength_unit = Column(String(50))  # 'mg'
    dose_form_id = Column(UUID(as_uuid=True), ForeignKey("medication_dose_forms.id"))
    route_id = Column(UUID(as_uuid=True), ForeignKey("medication_routes.id"))
    pack_size = Column(Integer)  # 10 tablets, etc.
    pack_unit = Column(String(50))  # 'TAB', 'VIAL'
    is_generic = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    molecule = relationship("MedicationMolecule", back_populates="medication_products")
    dose_form = relationship("MedicationDoseForm", back_populates="medication_products")
    route = relationship("MedicationRoute", back_populates="medication_products")
    formulary_entries = relationship("FormularyEntry", back_populates="medication_product")
    medication_orders = relationship("MedicationOrder", back_populates="medication_product")
    medication_dispensation_items = relationship("MedicationDispensationItem", back_populates="medication_product")
    medication_administrations = relationship("MedicationAdministration", back_populates="medication_product")
    medication_reconciliation_lines = relationship("MedicationReconciliationLine", back_populates="medication_product")
    inventory_batches = relationship("InventoryBatch", back_populates="medication_product")
    purchase_order_lines = relationship("PurchaseOrderLine", back_populates="medication_product")

    __table_args__ = (
        Index('idx_medication_products_molecule', 'molecule_id'),
    )


# ===== Formulary Service Models =====

class FormularyEntry(Base):
    """
    Hospital/tenant-specific formulary entries
    """
    __tablename__ = "formulary_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    medication_product_id = Column(UUID(as_uuid=True), ForeignKey("medication_products.id"), nullable=False)
    is_formulary = Column(Boolean, nullable=False, default=True)
    restriction_level = Column(String(50), default='none')  # 'none', 'restricted', 'non_formulary'
    default_route_id = Column(UUID(as_uuid=True), ForeignKey("medication_routes.id"))
    default_frequency = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    medication_product = relationship("MedicationProduct", back_populates="formulary_entries")
    default_route = relationship("MedicationRoute")
    restrictions = relationship("FormularyRestriction", back_populates="formulary_entry", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_formulary_entry_tenant_product', 'tenant_id', 'medication_product_id', unique=True),
    )


class FormularyRestriction(Base):
    """
    Formulary restriction rules (specialist-only, indication-based, etc.)
    """
    __tablename__ = "formulary_restrictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    formulary_entry_id = Column(UUID(as_uuid=True), ForeignKey("formulary_entries.id", ondelete="CASCADE"), nullable=False)
    restriction_type = Column(String(100), nullable=False)  # 'specialist_only', 'indication_based'
    allowed_specialties = Column(ARRAY(String))  # ['Oncology', 'Cardiology']
    indication_regex = Column(Text)  # optional; matches indication text
    approval_required = Column(Boolean, default=False)
    approval_role = Column(String(100))  # 'pharmacy_director', 'ID_specialist'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    formulary_entry = relationship("FormularyEntry", back_populates="restrictions")


class FormularySubstitutionRule(Base):
    """
    Formulary substitution rules (generic substitution, therapeutic alternatives)
    """
    __tablename__ = "formulary_substitution_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    from_molecule_id = Column(UUID(as_uuid=True), ForeignKey("medication_molecules.id"), nullable=False)
    to_molecule_id = Column(UUID(as_uuid=True), ForeignKey("medication_molecules.id"), nullable=False)
    rule_type = Column(String(50), nullable=False)  # 'automatic_generic', 'therapeutic'
    conditions = Column(JSONB)  # {"route": "PO", "indication_contains": "hypertension"}
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    from_molecule = relationship("MedicationMolecule", foreign_keys=[from_molecule_id], back_populates="formulary_substitution_from")
    to_molecule = relationship("MedicationMolecule", foreign_keys=[to_molecule_id], back_populates="formulary_substitution_to")


# ===== Medication Order Service Models =====

class MedicationOrder(Base):
    """
    Medication orders (FHIR MedicationRequest)
    """
    __tablename__ = "medication_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"))
    prescriber_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    medication_product_id = Column(UUID(as_uuid=True), ForeignKey("medication_products.id"))
    molecule_id = Column(UUID(as_uuid=True), ForeignKey("medication_molecules.id"))
    order_type = Column(String(50), nullable=False)  # 'inpatient', 'outpatient', 'discharge'
    status = Column(String(50), nullable=False, default='active')  # 'active', 'on_hold', 'cancelled', 'completed'
    intent = Column(String(50), nullable=False, default='order')  # 'order', 'plan', 'proposal'
    dose_amount_numeric = Column(Numeric(15, 4))
    dose_amount_unit = Column(String(50))  # 'mg'
    dose_form_id = Column(UUID(as_uuid=True), ForeignKey("medication_dose_forms.id"))
    route_id = Column(UUID(as_uuid=True), ForeignKey("medication_routes.id"))
    frequency = Column(String(50))  # 'BID', 'TID', 'Q6H'
    as_needed = Column(Boolean, default=False)
    as_needed_reason = Column(Text)
    start_datetime = Column(DateTime(timezone=True))
    end_datetime = Column(DateTime(timezone=True))
    indication = Column(Text)
    instructions_for_patient = Column(Text)
    instructions_for_pharmacist = Column(Text)
    is_prn = Column(Boolean, default=False)
    linked_discharge_order_id = Column(UUID(as_uuid=True))
    fhir_medication_request_id = Column(String(255))
    formulary_status = Column(String(50))  # 'formulary', 'non_formulary', 'substituted'
    substitution_details = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    episode = relationship("Episode")
    prescriber = relationship("Practitioner", foreign_keys=[prescriber_id])
    department = relationship("Department")
    medication_product = relationship("MedicationProduct", back_populates="medication_orders")
    molecule = relationship("MedicationMolecule", back_populates="medication_orders")
    dose_form = relationship("MedicationDoseForm", back_populates="medication_orders")
    route = relationship("MedicationRoute", back_populates="medication_orders")
    pharmacy_verification_queue = relationship("PharmacyVerificationQueue", back_populates="medication_order", uselist=False)
    medication_dispensations = relationship("MedicationDispensation", back_populates="medication_order")
    medication_administrations = relationship("MedicationAdministration", back_populates="medication_order")
    medication_reconciliation_lines = relationship("MedicationReconciliationLine", back_populates="linked_medication_order")
    pharmacy_ai_tasks = relationship("PharmacyAITask", back_populates="medication_order")

    __table_args__ = (
        Index('idx_medication_orders_patient', 'patient_id', 'created_at'),
        Index('idx_medication_orders_status', 'status', 'start_datetime'),
    )


# ===== Pharmacy Verification & Dispense Service Models =====

class PharmacyVerificationQueue(Base):
    """
    Pharmacy verification queue for medication orders
    """
    __tablename__ = "pharmacy_verification_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    medication_order_id = Column(UUID(as_uuid=True), ForeignKey("medication_orders.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    status = Column(String(50), nullable=False, default='pending')  # 'pending', 'under_review', 'approved', 'rejected'
    pharmacist_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    review_notes = Column(Text)
    rejection_reason = Column(Text)
    clinical_checks = Column(JSONB)  # [{"type":"interaction","severity":"major","details":"..."}]

    # Relationships
    medication_order = relationship("MedicationOrder", back_populates="pharmacy_verification_queue")
    patient = relationship("Patient")
    pharmacist = relationship("Practitioner")

    __table_args__ = (
        Index('idx_pharmacy_verification_queue_status', 'status', 'created_at'),
    )


class MedicationDispensation(Base):
    """
    Medication dispensations (FHIR MedicationDispense)
    """
    __tablename__ = "medication_dispensations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    medication_order_id = Column(UUID(as_uuid=True), ForeignKey("medication_orders.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    dispensed_by_user_id = Column(UUID(as_uuid=True))
    dispensed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    destination_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"))  # ward/OPD/patient home
    status = Column(String(50), nullable=False, default='completed')  # 'preparation', 'completed', 'returned', 'cancelled'
    comments = Column(Text)
    fhir_medication_dispense_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    medication_order = relationship("MedicationOrder", back_populates="medication_dispensations")
    patient = relationship("Patient")
    destination_location = relationship("Location")
    dispensation_items = relationship("MedicationDispensationItem", back_populates="medication_dispensation", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_medication_dispensations_patient', 'patient_id', 'dispensed_at'),
    )


class MedicationDispensationItem(Base):
    """
    Individual items within a medication dispensation
    """
    __tablename__ = "medication_dispensation_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    medication_dispensation_id = Column(UUID(as_uuid=True), ForeignKey("medication_dispensations.id", ondelete="CASCADE"), nullable=False)
    medication_product_id = Column(UUID(as_uuid=True), ForeignKey("medication_products.id"), nullable=False)
    quantity_dispensed = Column(Numeric(15, 4), nullable=False)
    quantity_unit = Column(String(50))  # 'TAB', 'ML'
    inventory_batch_id = Column(UUID(as_uuid=True), ForeignKey("inventory_batches.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    medication_dispensation = relationship("MedicationDispensation", back_populates="dispensation_items")
    medication_product = relationship("MedicationProduct", back_populates="medication_dispensation_items")
    inventory_batch = relationship("InventoryBatch")


# ===== MAR Service Models =====

class MedicationAdministration(Base):
    """
    Medication administration records (FHIR MedicationAdministration)
    """
    __tablename__ = "medication_administrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    medication_order_id = Column(UUID(as_uuid=True), ForeignKey("medication_orders.id"))
    medication_product_id = Column(UUID(as_uuid=True), ForeignKey("medication_products.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    scheduled_time = Column(DateTime(timezone=True))
    administration_time = Column(DateTime(timezone=True))
    administered_by_user_id = Column(UUID(as_uuid=True))
    dose_given_numeric = Column(Numeric(15, 4))
    dose_given_unit = Column(String(50))
    route_id = Column(UUID(as_uuid=True), ForeignKey("medication_routes.id"))
    status = Column(String(50), nullable=False, default='scheduled')  # 'scheduled', 'completed', 'skipped', 'refused', 'partial'
    reason_skipped = Column(Text)
    comments = Column(Text)
    fhir_medication_administration_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    medication_order = relationship("MedicationOrder", back_populates="medication_administrations")
    medication_product = relationship("MedicationProduct", back_populates="medication_administrations")
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    route = relationship("MedicationRoute", back_populates="medication_administrations")

    __table_args__ = (
        Index('idx_medication_admin_patient', 'patient_id', 'scheduled_time'),
        Index('idx_medication_admin_order', 'medication_order_id', 'scheduled_time'),
    )


# ===== Medication Reconciliation Service Models =====

class MedicationHistorySource(Base):
    """
    Medication history sources (patient interview, external records, etc.)
    """
    __tablename__ = "medication_history_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    source_type = Column(String(100), nullable=False)  # 'patient', 'caregiver', 'external_record', 'pharmacy'
    description = Column(Text)
    recorded_by_user_id = Column(UUID(as_uuid=True))
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")


class MedicationReconciliationSession(Base):
    """
    Medication reconciliation sessions (admission, transfer, discharge)
    """
    __tablename__ = "medication_reconciliation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    reconciliation_type = Column(String(50), nullable=False)  # 'admission', 'transfer', 'discharge'
    status = Column(String(50), nullable=False, default='in_progress')  # 'in_progress', 'completed'
    performed_by_user_id = Column(UUID(as_uuid=True))
    performed_at = Column(DateTime(timezone=True))
    comments = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    reconciliation_lines = relationship("MedicationReconciliationLine", back_populates="reconciliation_session", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_medication_recon_sessions_patient', 'patient_id', 'created_at'),
    )


class MedicationReconciliationLine(Base):
    """
    Individual medication decisions within reconciliation session
    """
    __tablename__ = "medication_reconciliation_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    reconciliation_session_id = Column(UUID(as_uuid=True), ForeignKey("medication_reconciliation_sessions.id", ondelete="CASCADE"), nullable=False)
    source_medication_statement_id = Column(String(255))  # pointer to FHIR MedicationStatement / external
    medication_product_id = Column(UUID(as_uuid=True), ForeignKey("medication_products.id"))
    molecule_id = Column(UUID(as_uuid=True), ForeignKey("medication_molecules.id"))
    home_regimen = Column(Text)  # 'Paracetamol 500mg TID'
    decision = Column(String(50), nullable=False)  # 'continue', 'modify', 'stop', 'new'
    decision_reason = Column(Text)
    linked_medication_order_id = Column(UUID(as_uuid=True), ForeignKey("medication_orders.id"))
    comments = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reconciliation_session = relationship("MedicationReconciliationSession", back_populates="reconciliation_lines")
    medication_product = relationship("MedicationProduct", back_populates="medication_reconciliation_lines")
    molecule = relationship("MedicationMolecule")
    linked_medication_order = relationship("MedicationOrder", back_populates="medication_reconciliation_lines")


# ===== Pharmacy Inventory Service Models =====

class InventoryLocation(Base):
    """
    Inventory storage locations (pharmacy stores, ward cupboards, etc.)
    """
    __tablename__ = "inventory_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'MAIN_PHARM', 'WARD_3_STOCK'
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'pharmacy_store', 'ward_cupboard'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    inventory_batches = relationship("InventoryBatch", back_populates="location")

    __table_args__ = (
        Index('idx_inventory_locations_tenant_code', 'tenant_id', 'code', unique=True),
    )


class InventoryBatch(Base):
    """
    Inventory batches with expiry tracking
    """
    __tablename__ = "inventory_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    medication_product_id = Column(UUID(as_uuid=True), ForeignKey("medication_products.id"), nullable=False)
    batch_number = Column(String(255))
    expiry_date = Column(Date)
    current_quantity = Column(Numeric(15, 4), nullable=False)
    quantity_unit = Column(String(50))  # 'TAB', 'VIAL'
    location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    medication_product = relationship("MedicationProduct", back_populates="inventory_batches")
    location = relationship("InventoryLocation", back_populates="inventory_batches")
    inventory_transactions = relationship("InventoryTransaction", back_populates="inventory_batch")

    __table_args__ = (
        Index('idx_inventory_batches_product_location', 'medication_product_id', 'location_id'),
        Index('idx_inventory_batches_expiry', 'expiry_date'),
    )


class InventoryTransaction(Base):
    """
    Inventory transactions (receive, dispense, adjust, etc.)
    """
    __tablename__ = "inventory_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    inventory_batch_id = Column(UUID(as_uuid=True), ForeignKey("inventory_batches.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # 'receive', 'dispense', 'transfer_out', 'transfer_in', 'adjustment', 'return'
    quantity_delta = Column(Numeric(15, 4), nullable=False)  # positive or negative
    reason = Column(Text)
    related_dispensation_id = Column(UUID(as_uuid=True), ForeignKey("medication_dispensations.id"))
    related_purchase_order_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by_user_id = Column(UUID(as_uuid=True))

    # Relationships
    inventory_batch = relationship("InventoryBatch", back_populates="inventory_transactions")
    related_dispensation = relationship("MedicationDispensation")
    related_purchase_order_line = relationship("PurchaseOrderLine")

    __table_args__ = (
        Index('idx_inventory_transactions_batch', 'inventory_batch_id', 'created_at'),
    )


class Vendor(Base):
    """
    Medication vendors/suppliers
    """
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(100))
    contact_details = Column(JSONB)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")


class PurchaseOrder(Base):
    """
    Purchase orders for medication procurement
    """
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    po_number = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default='draft')  # 'draft', 'sent', 'partially_received', 'completed', 'cancelled'
    ordered_at = Column(DateTime(timezone=True))
    expected_delivery_date = Column(Date)
    created_by_user_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vendor = relationship("Vendor", back_populates="purchase_orders")
    purchase_order_lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_purchase_orders_tenant_po_number', 'tenant_id', 'po_number', unique=True),
    )


class PurchaseOrderLine(Base):
    """
    Individual line items within purchase orders
    """
    __tablename__ = "purchase_order_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    medication_product_id = Column(UUID(as_uuid=True), ForeignKey("medication_products.id"), nullable=False)
    quantity_ordered = Column(Numeric(15, 4), nullable=False)
    quantity_received = Column(Numeric(15, 4), default=0)
    quantity_unit = Column(String(50))
    unit_price = Column(Numeric(15, 2))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="purchase_order_lines")
    medication_product = relationship("MedicationProduct", back_populates="purchase_order_lines")


# ===== Pharmacy AI Orchestrator Service Models =====

class PharmacyAITask(Base):
    """
    AI processing tasks for pharmacy (interactions, dose suggestions, etc.)
    """
    __tablename__ = "pharmacy_ai_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    medication_order_id = Column(UUID(as_uuid=True), ForeignKey("medication_orders.id"))
    task_type = Column(String(50), nullable=False)  # 'interaction_check', 'dose_suggestion', 'reconciliation_assist', 'inventory_forecast'
    status = Column(String(50), nullable=False, default='queued')  # 'queued', 'running', 'completed', 'failed'
    requested_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    medication_order = relationship("MedicationOrder", back_populates="pharmacy_ai_tasks")
    outputs = relationship("PharmacyAIOutput", back_populates="pharmacy_ai_task", cascade="all, delete-orphan")


class PharmacyAIOutput(Base):
    """
    AI analysis outputs for pharmacy tasks
    """
    __tablename__ = "pharmacy_ai_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    pharmacy_ai_task_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_ai_tasks.id", ondelete="CASCADE"), nullable=False)
    output_type = Column(String(50), nullable=False)  # 'interaction_summary', 'dose_recommendation', 'reconciliation_proposal', 'forecast'
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    pharmacy_ai_task = relationship("PharmacyAITask", back_populates="outputs")


# ============================================================================
# PHASE 10: OR / Procedure / Perioperative Management Models
# ============================================================================

class SurgeryProcedureCatalog(Base):
    """
    Catalog of surgical procedures with default parameters
    """
    __tablename__ = "surgery_procedure_catalog"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(100), nullable=False)  # 'APPENDECTOMY_LAP', 'CABG_3V'
    name = Column(String(255), nullable=False)
    specialty = Column(String(100), nullable=False)  # 'General Surgery', 'Cardiac Surgery'
    body_site = Column(String(100))  # 'abdomen', 'heart', 'uterus'
    description = Column(Text)
    typical_duration_minutes = Column(Integer)  # expected OR time
    fhir_code = Column(String(100))  # SNOMED/ICD-10-PCS/OPCS
    default_priority = Column(String(50), default='elective')  # 'elective', 'urgent', 'emergency'
    default_anaesthesia_type = Column(String(50))  # 'general', 'regional', 'local'
    preop_required_labs = Column(ARRAY(String))  # ['CBC', 'RFT', 'LFT']
    preop_required_imaging = Column(ARRAY(String))  # ['CXR', 'ECG']
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    surgery_requests = relationship("SurgeryRequest", back_populates="procedure_catalog")

    __table_args__ = (
        Index('uniq_surgery_procedure_catalog_code_tenant', 'tenant_id', 'code', unique=True),
    )


class SurgeryRequest(Base):
    """
    Surgical/procedure requests from clinics/wards/ED
    Maps to FHIR ServiceRequest
    """
    __tablename__ = "surgery_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"))
    requesting_practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    requesting_department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    procedure_catalog_id = Column(UUID(as_uuid=True), ForeignKey("surgery_procedure_catalog.id"), nullable=False)
    additional_procedure_text = Column(Text)
    indication = Column(Text, nullable=False)
    urgency = Column(String(50), nullable=False, default='elective')  # 'elective', 'urgent', 'emergency'
    status = Column(String(50), nullable=False, default='requested')  # 'requested', 'accepted', 'rejected', 'scheduled', 'cancelled', 'completed'
    requested_date = Column(DateTime(timezone=True), nullable=False)
    comments = Column(Text)
    fhir_service_request_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    procedure_catalog = relationship("SurgeryProcedureCatalog", back_populates="surgery_requests")
    or_case_schedules = relationship("ORCaseSchedule", back_populates="surgery_request")
    preop_assessments = relationship("PreopAssessment", back_populates="surgery_request")
    surgical_cases = relationship("SurgicalCase", back_populates="surgery_request")
    periop_ai_tasks = relationship("PeriopAITask", back_populates="surgery_request")

    __table_args__ = (
        Index('idx_surgery_requests_patient', 'patient_id', 'requested_date'),
        Index('idx_surgery_requests_status', 'status', 'urgency', 'requested_date'),
    )


class ORRoom(Base):
    """
    Operating room/theatre
    """
    __tablename__ = "or_rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(50), nullable=False)  # 'OR1', 'OR2', 'CATH1'
    name = Column(String(255), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"))
    specialties_supported = Column(ARRAY(String))  # ['General Surgery', 'Ortho']
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    or_blocks = relationship("ORBlock", back_populates="or_room")
    or_case_schedules = relationship("ORCaseSchedule", back_populates="or_room")

    __table_args__ = (
        Index('uniq_or_rooms_code_tenant', 'tenant_id', 'code', unique=True),
    )


class ORBlock(Base):
    """
    Scheduled block time for a service/surgeon
    """
    __tablename__ = "or_blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    or_room_id = Column(UUID(as_uuid=True), ForeignKey("or_rooms.id"), nullable=False)
    service_or_department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    surgeon_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    day_of_week = Column(Integer, nullable=False)  # 1-7
    start_time_local = Column(Time, nullable=False)
    end_time_local = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    or_room = relationship("ORRoom", back_populates="or_blocks")
    or_case_schedules = relationship("ORCaseSchedule", back_populates="block")

    __table_args__ = (
        Index('idx_or_blocks_room_day', 'or_room_id', 'day_of_week'),
    )


class ORCaseSchedule(Base):
    """
    Scheduled surgical cases in OR
    """
    __tablename__ = "or_case_schedule"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    surgery_request_id = Column(UUID(as_uuid=True), ForeignKey("surgery_requests.id"), nullable=False)
    or_room_id = Column(UUID(as_uuid=True), ForeignKey("or_rooms.id"), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    scheduled_start_time_local = Column(Time, nullable=False)
    scheduled_end_time_local = Column(Time)
    status = Column(String(50), nullable=False, default='scheduled')  # 'scheduled', 'in_progress', 'completed', 'cancelled', 'no_show'
    block_id = Column(UUID(as_uuid=True), ForeignKey("or_blocks.id"))
    priority = Column(String(50), nullable=False)  # 'elective', 'urgent', 'emergency'
    case_number = Column(String(100))  # 'CASE-2025-000123'
    reason_for_cancellation = Column(Text)
    actual_start_time = Column(DateTime(timezone=True))
    actual_end_time = Column(DateTime(timezone=True))
    turnover_start_time = Column(DateTime(timezone=True))
    turnover_end_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    surgery_request = relationship("SurgeryRequest", back_populates="or_case_schedules")
    or_room = relationship("ORRoom", back_populates="or_case_schedules")
    block = relationship("ORBlock", back_populates="or_case_schedules")
    surgical_cases = relationship("SurgicalCase", back_populates="or_case_schedule")

    __table_args__ = (
        Index('uniq_or_case_schedule_case_number_tenant', 'tenant_id', 'case_number', unique=True),
        Index('idx_or_case_schedule_or_date', 'or_room_id', 'scheduled_date', 'scheduled_start_time_local'),
    )


class PreopAssessment(Base):
    """
    Pre-anesthesia evaluation and clearance
    """
    __tablename__ = "preop_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    surgery_request_id = Column(UUID(as_uuid=True), ForeignKey("surgery_requests.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    assessor_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))  # usually anesthetist
    assessment_datetime = Column(DateTime(timezone=True))
    asa_class = Column(String(10))  # 'I', 'II', 'III', 'IV', 'V', 'VI'
    airway_assessment = Column(Text)  # Mallampati, neck mobility
    comorbidities = Column(Text)
    functional_status = Column(Text)  # METs
    planned_anaesthesia_type = Column(String(50))  # 'general', 'regional', 'spinal', 'local'
    npo_status = Column(String(255))
    investigations_reviewed = Column(JSONB)  # labs, imaging summary
    recommendation = Column(Text)  # 'fit for surgery', 'optimise'
    status = Column(String(50), nullable=False, default='in_progress')  # 'in_progress', 'cleared', 'deferred'
    fhir_encounter_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    surgery_request = relationship("SurgeryRequest", back_populates="preop_assessments")
    risk_scores = relationship("PreopRiskScore", back_populates="preop_assessment", cascade="all, delete-orphan")
    optimization_tasks = relationship("PreopOptimizationTask", back_populates="preop_assessment", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_preop_assessments_surgery_request', 'surgery_request_id'),
    )


class PreopRiskScore(Base):
    """
    Perioperative risk scores (RCRI, NSQIP, etc.)
    """
    __tablename__ = "preop_risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    preop_assessment_id = Column(UUID(as_uuid=True), ForeignKey("preop_assessments.id", ondelete="CASCADE"), nullable=False)
    score_type = Column(String(50), nullable=False)  # 'RCRI', 'NSQIP', 'Custom'
    score_value = Column(Numeric(15, 4))
    risk_category = Column(String(50))  # 'low', 'intermediate', 'high'
    details = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    preop_assessment = relationship("PreopAssessment", back_populates="risk_scores")


class PreopOptimizationTask(Base):
    """
    Tasks to optimize patient before surgery
    """
    __tablename__ = "preop_optimization_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    preop_assessment_id = Column(UUID(as_uuid=True), ForeignKey("preop_assessments.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)  # 'Optimise BP', 'Stop warfarin 5 days prior'
    assigned_to_role = Column(String(100))  # 'cardiologist', 'primary_team'
    due_date = Column(Date)
    status = Column(String(50), nullable=False, default='pending')  # 'pending', 'in_progress', 'completed', 'cancelled'
    completed_at = Column(DateTime(timezone=True))
    comments = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    preop_assessment = relationship("PreopAssessment", back_populates="optimization_tasks")


class SurgicalCase(Base):
    """
    Intra-operative surgical case record
    Maps to FHIR Procedure
    """
    __tablename__ = "surgical_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    or_case_schedule_id = Column(UUID(as_uuid=True), ForeignKey("or_case_schedule.id"), nullable=False)
    surgery_request_id = Column(UUID(as_uuid=True), ForeignKey("surgery_requests.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    primary_surgeon_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    assistant_surgeon_ids = Column(ARRAY(UUID(as_uuid=True)))
    anesthetist_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    anesthesia_type = Column(String(50))  # 'general', 'regional', 'spinal', 'local'
    procedure_performed_code = Column(String(100))
    procedure_performed_text = Column(Text)
    wound_class = Column(String(50))  # 'clean', 'clean-contaminated', etc.
    asa_class_intraop = Column(String(10))
    incision_time = Column(DateTime(timezone=True))
    closure_time = Column(DateTime(timezone=True))
    estimated_blood_loss_ml = Column(Numeric(15, 2))
    intraop_complications = Column(Text)
    disposition = Column(String(50))  # 'PACU', 'ICU', 'ward'
    status = Column(String(50), nullable=False, default='in_progress')  # 'in_progress', 'completed', 'abandoned'
    fhir_procedure_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    or_case_schedule = relationship("ORCaseSchedule", back_populates="surgical_cases")
    surgery_request = relationship("SurgeryRequest", back_populates="surgical_cases")
    team_members = relationship("SurgicalCaseTeamMember", back_populates="surgical_case", cascade="all, delete-orphan")
    implants = relationship("SurgicalCaseImplant", back_populates="surgical_case", cascade="all, delete-orphan")
    specimens = relationship("SurgicalCaseSpecimen", back_populates="surgical_case", cascade="all, delete-orphan")
    anesthesia_records = relationship("AnesthesiaRecord", back_populates="surgical_case")
    pacu_stays = relationship("PACUStay", back_populates="surgical_case")
    periop_ai_tasks = relationship("PeriopAITask", back_populates="surgical_case")

    __table_args__ = (
        Index('idx_surgical_cases_patient', 'patient_id', 'created_at'),
        Index('idx_surgical_cases_schedule', 'or_case_schedule_id'),
    )


class SurgicalCaseTeamMember(Base):
    """
    OR team members for a surgical case
    """
    __tablename__ = "surgical_case_team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    surgical_case_id = Column(UUID(as_uuid=True), ForeignKey("surgical_cases.id", ondelete="CASCADE"), nullable=False)
    practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    role = Column(String(100), nullable=False)  # 'scrub_nurse', 'circulating_nurse', 'perfursionist'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    surgical_case = relationship("SurgicalCase", back_populates="team_members")


class SurgicalCaseImplant(Base):
    """
    Implants used in surgical case
    Maps to FHIR Device
    """
    __tablename__ = "surgical_case_implants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    surgical_case_id = Column(UUID(as_uuid=True), ForeignKey("surgical_cases.id", ondelete="CASCADE"), nullable=False)
    implant_code = Column(String(255))  # internal or UDI
    description = Column(Text)
    manufacturer = Column(String(255))
    lot_number = Column(String(255))
    expiry_date = Column(Date)
    quantity = Column(Integer)
    body_site = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    surgical_case = relationship("SurgicalCase", back_populates="implants")


class SurgicalCaseSpecimen(Base):
    """
    Specimens collected during surgical case
    Links to anatomic pathology
    """
    __tablename__ = "surgical_case_specimens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    surgical_case_id = Column(UUID(as_uuid=True), ForeignKey("surgical_cases.id", ondelete="CASCADE"), nullable=False)
    ap_case_id = Column(UUID(as_uuid=True), ForeignKey("ap_cases.id"))
    specimen_label = Column(String(100))  # 'Specimen A', 'B'
    description = Column(Text)
    site = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    surgical_case = relationship("SurgicalCase", back_populates="specimens")


class AnesthesiaRecord(Base):
    """
    Intra-operative anesthesia chart
    """
    __tablename__ = "anesthesia_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    surgical_case_id = Column(UUID(as_uuid=True), ForeignKey("surgical_cases.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    anesthetist_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    anesthesia_start_time = Column(DateTime(timezone=True))
    anesthesia_end_time = Column(DateTime(timezone=True))
    airway_type = Column(String(50))  # 'ETT', 'LMA', 'mask'
    airway_difficulty = Column(Text)
    induction_agents = Column(Text)
    maintenance_agents = Column(Text)
    reversal_agents = Column(Text)
    intraop_notes = Column(Text)
    status = Column(String(50), nullable=False, default='in_progress')  # 'in_progress', 'completed'
    fhir_encounter_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    surgical_case = relationship("SurgicalCase", back_populates="anesthesia_records")
    events = relationship("AnesthesiaEvent", back_populates="anesthesia_record", cascade="all, delete-orphan")
    vitals = relationship("AnesthesiaVitals", back_populates="anesthesia_record", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_anesthesia_records_surgical_case', 'surgical_case_id'),
    )


class AnesthesiaEvent(Base):
    """
    Events during anesthesia (drugs, fluids, airway, procedures)
    """
    __tablename__ = "anesthesia_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    anesthesia_record_id = Column(UUID(as_uuid=True), ForeignKey("anesthesia_records.id", ondelete="CASCADE"), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False)
    event_type = Column(String(50), nullable=False)  # 'drug', 'fluid', 'airway', 'procedure', 'complication'
    description = Column(Text)
    medication_product_id = Column(UUID(as_uuid=True), ForeignKey("medication_products.id"))
    dose_numeric = Column(Numeric(15, 4))
    dose_unit = Column(String(50))
    fluid_volume_ml = Column(Numeric(15, 2))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    anesthesia_record = relationship("AnesthesiaRecord", back_populates="events")

    __table_args__ = (
        Index('idx_anesthesia_events_record', 'anesthesia_record_id', 'event_time'),
    )


class AnesthesiaVitals(Base):
    """
    Vital signs during anesthesia
    """
    __tablename__ = "anesthesia_vitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    anesthesia_record_id = Column(UUID(as_uuid=True), ForeignKey("anesthesia_records.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    heart_rate = Column(Numeric(15, 2))
    systolic_bp = Column(Numeric(15, 2))
    diastolic_bp = Column(Numeric(15, 2))
    mean_arterial_pressure = Column(Numeric(15, 2))
    spo2 = Column(Numeric(15, 2))
    resp_rate = Column(Numeric(15, 2))
    etco2 = Column(Numeric(15, 2))
    temperature = Column(Numeric(15, 2))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    anesthesia_record = relationship("AnesthesiaRecord", back_populates="vitals")

    __table_args__ = (
        Index('idx_anesthesia_vitals_record', 'anesthesia_record_id', 'timestamp'),
    )


class PACUStay(Base):
    """
    Post-Anesthesia Care Unit stay
    """
    __tablename__ = "pacu_stays"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    surgical_case_id = Column(UUID(as_uuid=True), ForeignKey("surgical_cases.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    admission_time = Column(DateTime(timezone=True), nullable=False)
    discharge_time = Column(DateTime(timezone=True))
    initial_status = Column(String(100))  # 'stable', 'requires_observation', 'critical'
    disposition = Column(String(50))  # 'ward', 'ICU', 'home'
    complications = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    surgical_case = relationship("SurgicalCase", back_populates="pacu_stays")
    vitals = relationship("PACUVitals", back_populates="pacu_stay", cascade="all, delete-orphan")
    scores = relationship("PACUScore", back_populates="pacu_stay", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_pacu_stays_case', 'surgical_case_id'),
    )


class PACUVitals(Base):
    """
    Vital signs in PACU
    """
    __tablename__ = "pacu_vitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    pacu_stay_id = Column(UUID(as_uuid=True), ForeignKey("pacu_stays.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    heart_rate = Column(Numeric(15, 2))
    systolic_bp = Column(Numeric(15, 2))
    diastolic_bp = Column(Numeric(15, 2))
    spo2 = Column(Numeric(15, 2))
    resp_rate = Column(Numeric(15, 2))
    pain_score = Column(Numeric(15, 2))  # 0-10
    sedation_score = Column(String(50))  # RASS
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    pacu_stay = relationship("PACUStay", back_populates="vitals")

    __table_args__ = (
        Index('idx_pacu_vitals_stay', 'pacu_stay_id', 'timestamp'),
    )


class PACUScore(Base):
    """
    Recovery scores in PACU (Aldrete, Modified Aldrete, etc.)
    """
    __tablename__ = "pacu_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    pacu_stay_id = Column(UUID(as_uuid=True), ForeignKey("pacu_stays.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    score_type = Column(String(50), nullable=False)  # 'Aldrete', 'Modified_Aldrete'
    score_value = Column(Numeric(15, 2))
    components = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    pacu_stay = relationship("PACUStay", back_populates="scores")

    __table_args__ = (
        Index('idx_pacu_scores_stay', 'pacu_stay_id', 'timestamp'),
    )


class PeriopAITask(Base):
    """
    AI tasks for perioperative workflows
    """
    __tablename__ = "periop_ai_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    surgery_request_id = Column(UUID(as_uuid=True), ForeignKey("surgery_requests.id"))
    surgical_case_id = Column(UUID(as_uuid=True), ForeignKey("surgical_cases.id"))
    task_type = Column(String(100), nullable=False)  # 'case_duration_estimate', 'preop_risk_summary', 'handoff_note', 'or_list_optimisation'
    status = Column(String(50), nullable=False, default='queued')  # 'queued', 'running', 'completed', 'failed'
    requested_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    surgery_request = relationship("SurgeryRequest", back_populates="periop_ai_tasks")
    surgical_case = relationship("SurgicalCase", back_populates="periop_ai_tasks")
    outputs = relationship("PeriopAIOutput", back_populates="periop_ai_task", cascade="all, delete-orphan")


class PeriopAIOutput(Base):
    """
    AI outputs for perioperative tasks
    """
    __tablename__ = "periop_ai_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    periop_ai_task_id = Column(UUID(as_uuid=True), ForeignKey("periop_ai_tasks.id", ondelete="CASCADE"), nullable=False)
    output_type = Column(String(50), nullable=False)  # 'duration_estimate', 'risk_summary', 'handoff_text', 'optimised_list'
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    periop_ai_task = relationship("PeriopAITask", back_populates="outputs")


# ============================================================================
# PHASE 11: REVENUE CYCLE MANAGEMENT (RCM) & CASHLESS CONTROL TOWER
# ============================================================================


# ----------------------------------------------------------------------------
# Payer Master (4 models)
# ----------------------------------------------------------------------------


class Payer(Base):
    """
    Insurance companies, TPAs, self-pay, corporate payers
    Maps to FHIR Organization (insurer)
    """
    __tablename__ = "payers"
    __table_args__ = (
        Index('uniq_payers_code_tenant', 'tenant_id', 'code', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(Text, nullable=False)  # 'HDFC_ERGO', 'STAR_HEALTH', 'MEDI_ASSIST'
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=False)  # 'insurer', 'tpa', 'self_pay', 'corporate'
    contact_details = Column(JSONB)
    portal_url = Column(Text)  # for cashless login
    api_endpoint_config = Column(JSONB)  # if API-based
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payer_plans = relationship("PayerPlan", back_populates="payer")
    claims = relationship("Claim", back_populates="payer")
    remittances = relationship("Remittance", back_populates="payer")


class PayerPlan(Base):
    """
    Specific insurance plans offered by payers
    Maps to FHIR InsurancePlan
    """
    __tablename__ = "payer_plans"
    __table_args__ = (
        Index('uniq_payer_plans_payer_code', 'payer_id', 'code', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    payer_id = Column(UUID(as_uuid=True), ForeignKey("payers.id"), nullable=False)
    code = Column(Text, nullable=False)  # 'GOLD_FAMILY_FLOATER', 'CORP_ABC_TIER1'
    name = Column(Text, nullable=False)
    coverage_type = Column(Text)  # 'individual', 'floater', 'corporate'
    product_type = Column(Text)  # 'indemnity', 'fixed_benefit'
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payer = relationship("Payer", back_populates="payer_plans")
    network_contracts = relationship("PayerNetworkContract", back_populates="payer_plan")
    payer_rules = relationship("PayerRule", back_populates="payer_plan")
    coverages = relationship("Coverage", back_populates="payer_plan")
    tariff_groups = relationship("TariffGroup", back_populates="payer_plan")
    package_definitions = relationship("PackageDefinition", back_populates="payer_plan")
    claims = relationship("Claim", back_populates="payer_plan")


class PayerNetworkContract(Base):
    """
    Network agreements between hospital locations and payer plans
    Determines cashless eligibility and discount models
    """
    __tablename__ = "payer_network_contracts"
    __table_args__ = (
        Index('idx_payer_network_contracts_payer', 'payer_plan_id', 'hospital_location_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    payer_plan_id = Column(UUID(as_uuid=True), ForeignKey("payer_plans.id"), nullable=False)
    hospital_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"))
    network_type = Column(Text, nullable=False)  # 'network', 'non_network', 'PPN'
    effective_from = Column(Date)
    effective_to = Column(Date)
    discount_model = Column(Text)  # 'package', 'percent_off_tariff', 'negotiated_rate'
    discount_details = Column(JSONB)
    cashless_allowed = Column(Boolean, default=True)
    preauth_required = Column(Boolean, default=True)
    remarks = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payer_plan = relationship("PayerPlan", back_populates="network_contracts")
    coverages = relationship("Coverage", back_populates="network_contract")


class PayerRule(Base):
    """
    Payer-specific rules for document checklists, TAT SLAs, package mappings
    """
    __tablename__ = "payer_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    payer_plan_id = Column(UUID(as_uuid=True), ForeignKey("payer_plans.id"), nullable=False)
    rule_type = Column(Text, nullable=False)  # 'document_checklist', 'tat_sla', 'package_mapping'
    rule_name = Column(Text, nullable=False)
    rule_payload = Column(JSONB, nullable=False)  # e.g., doc checklist per indication
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payer_plan = relationship("PayerPlan", back_populates="payer_rules")


# ----------------------------------------------------------------------------
# Tariff / Pricebook (5 models)
# ----------------------------------------------------------------------------


class ServiceItem(Base):
    """
    Master catalog of billable services: procedures, beds, consultations, labs, imaging, consumables, packages
    Maps to FHIR ChargeItemDefinition
    """
    __tablename__ = "service_items"
    __table_args__ = (
        Index('uniq_service_items_code_tenant', 'tenant_id', 'code', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(Text, nullable=False)  # 'PROC_LAP_APPEND', 'BED_GEN', 'CONS_SYR_5ML'
    name = Column(Text, nullable=False)
    category = Column(Text, nullable=False)  # 'procedure', 'bed', 'consultation', 'lab', 'imaging', 'consumable', 'package'
    description = Column(Text)
    clinical_code = Column(Text)  # ICD10-PCS/CPT/SNOMED for procedures
    unit = Column(Text, nullable=False)  # 'DAY', 'SERVICE', 'UNIT', 'HOUR'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tariff_rates = relationship("TariffRate", back_populates="service_item")
    charges = relationship("Charge", back_populates="service_item")
    package_inclusions = relationship("PackageInclusion", back_populates="service_item")
    financial_estimate_lines = relationship("FinancialEstimateLine", back_populates="service_item")
    claim_lines = relationship("ClaimLine", back_populates="service_item")


class TariffGroup(Base):
    """
    Pricing groups (cash, corporate, payer-specific)
    """
    __tablename__ = "tariff_groups"
    __table_args__ = (
        Index('uniq_tariff_groups_code_tenant', 'tenant_id', 'code', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(Text, nullable=False)  # 'DEFAULT_CASH', 'CORP_ABC', 'STAR_HEALTH'
    name = Column(Text, nullable=False)
    payer_plan_id = Column(UUID(as_uuid=True), ForeignKey("payer_plans.id"))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payer_plan = relationship("PayerPlan", back_populates="tariff_groups")
    tariff_rates = relationship("TariffRate", back_populates="tariff_group")
    package_definitions = relationship("PackageDefinition", back_populates="tariff_group")
    financial_estimates = relationship("FinancialEstimate", back_populates="tariff_group")


class TariffRate(Base):
    """
    Pricing for service items within tariff groups
    """
    __tablename__ = "tariff_rates"
    __table_args__ = (
        Index('uniq_tariff_rates_combo', 'tariff_group_id', 'service_item_id', 'effective_from', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tariff_group_id = Column(UUID(as_uuid=True), ForeignKey("tariff_groups.id"), nullable=False)
    service_item_id = Column(UUID(as_uuid=True), ForeignKey("service_items.id"), nullable=False)
    base_rate = Column(Numeric, nullable=False)
    currency = Column(Text, nullable=False, default='INR')
    effective_from = Column(Date)
    effective_to = Column(Date)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tariff_group = relationship("TariffGroup", back_populates="tariff_rates")
    service_item = relationship("ServiceItem", back_populates="tariff_rates")


class PackageDefinition(Base):
    """
    Pre-defined packages for procedures (e.g., Appendectomy Package - Star Health Gold)
    Maps to FHIR PlanDefinition or InsurancePlan benefit
    """
    __tablename__ = "package_definitions"
    __table_args__ = (
        Index('uniq_package_definitions_code_tenant', 'tenant_id', 'code', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(Text, nullable=False)  # 'PKG_LAP_APPEND_STAR', 'PKG_CSECTION_GOLD'
    name = Column(Text, nullable=False)
    procedure_catalog_id = Column(UUID(as_uuid=True), ForeignKey("surgery_procedure_catalog.id"))
    payer_plan_id = Column(UUID(as_uuid=True), ForeignKey("payer_plans.id"))
    tariff_group_id = Column(UUID(as_uuid=True), ForeignKey("tariff_groups.id"))
    package_rate = Column(Numeric, nullable=False)
    currency = Column(Text, nullable=False, default='INR')
    length_of_stay_days = Column(Integer)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payer_plan = relationship("PayerPlan", back_populates="package_definitions")
    tariff_group = relationship("TariffGroup", back_populates="package_definitions")
    package_inclusions = relationship("PackageInclusion", back_populates="package_definition", cascade="all, delete-orphan")
    charges = relationship("Charge", back_populates="package_definition")
    charge_packages = relationship("ChargePackage", back_populates="package_definition")


class PackageInclusion(Base):
    """
    What's included in a package (service items or generic rules)
    """
    __tablename__ = "package_inclusions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    package_definition_id = Column(UUID(as_uuid=True), ForeignKey("package_definitions.id", ondelete="CASCADE"), nullable=False)
    inclusion_type = Column(Text, nullable=False)  # 'service_item', 'generic_rule'
    service_item_id = Column(UUID(as_uuid=True), ForeignKey("service_items.id"))
    rule_payload = Column(JSONB)  # e.g., 'all lab tests except...', 'max X days ICU'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    package_definition = relationship("PackageDefinition", back_populates="package_inclusions")
    service_item = relationship("ServiceItem", back_populates="package_inclusions")


# ----------------------------------------------------------------------------
# Coverage / Insurance Policy (2 models)
# ----------------------------------------------------------------------------


class Coverage(Base):
    """
    Patient-level insurance coverage
    Maps to FHIR Coverage
    """
    __tablename__ = "coverages"
    __table_args__ = (
        Index('idx_coverages_patient', 'patient_id', 'is_primary'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    payer_plan_id = Column(UUID(as_uuid=True), ForeignKey("payer_plans.id"), nullable=False)
    policy_number = Column(Text, nullable=False)
    insured_person_name = Column(Text)
    relationship_to_insured = Column(Text)  # 'self', 'spouse', 'child'
    sum_insured = Column(Numeric)
    remaining_eligible_amount = Column(Numeric)  # optional; may be approximate
    valid_from = Column(Date)
    valid_to = Column(Date)
    network_contract_id = Column(UUID(as_uuid=True), ForeignKey("payer_network_contracts.id"))
    is_primary = Column(Boolean, default=True)
    verification_status = Column(Text, default='unverified')  # 'unverified', 'verified', 'invalid'
    verification_details = Column(JSONB)
    fhir_coverage_id = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payer_plan = relationship("PayerPlan", back_populates="coverages")
    network_contract = relationship("PayerNetworkContract", back_populates="coverages")
    benefit_limits = relationship("CoverageBenefitLimit", back_populates="coverage", cascade="all, delete-orphan")
    financial_estimates = relationship("FinancialEstimate", back_populates="coverage")
    preauth_cases = relationship("PreauthCase", back_populates="coverage")
    accounts = relationship("Account", back_populates="coverage")
    claims = relationship("Claim", back_populates="coverage")


class CoverageBenefitLimit(Base):
    """
    Benefit limits within a coverage (room rent, procedure caps, etc.)
    """
    __tablename__ = "coverage_benefit_limits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    coverage_id = Column(UUID(as_uuid=True), ForeignKey("coverages.id", ondelete="CASCADE"), nullable=False)
    benefit_type = Column(Text, nullable=False)  # 'room_rent', 'icd_block', 'procedure_category'
    benefit_code = Column(Text)  # e.g., 'single_ac_room', 'cardiac'
    limit_type = Column(Text, nullable=False)  # 'per_day', 'per_event', 'overall'
    limit_amount = Column(Numeric)
    currency = Column(Text, default='INR')
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    coverage = relationship("Coverage", back_populates="benefit_limits")


# ----------------------------------------------------------------------------
# Financial Estimates (2 models)
# ----------------------------------------------------------------------------


class FinancialEstimate(Base):
    """
    Pre-admission / pre-surgery financial estimates
    Package vs itemized, patient share vs payer share
    """
    __tablename__ = "financial_estimates"
    __table_args__ = (
        Index('idx_financial_estimates_patient', 'patient_id', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"))
    coverage_id = Column(UUID(as_uuid=True), ForeignKey("coverages.id"))
    procedure_catalog_id = Column(UUID(as_uuid=True), ForeignKey("surgery_procedure_catalog.id"))
    tariff_group_id = Column(UUID(as_uuid=True), ForeignKey("tariff_groups.id"))
    estimate_type = Column(Text, nullable=False)  # 'opd_procedure', 'ipd_package', 'ipd_itemised'
    estimated_total = Column(Numeric, nullable=False)
    estimated_payer_amount = Column(Numeric)
    estimated_patient_amount = Column(Numeric)
    currency = Column(Text, default='INR')
    assumptions = Column(JSONB)  # e.g., LOS=3d, ward type
    status = Column(Text, nullable=False, default='draft')  # 'draft', 'final', 'expired'
    valid_until = Column(DateTime(timezone=True))
    created_by_user_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    coverage = relationship("Coverage", back_populates="financial_estimates")
    tariff_group = relationship("TariffGroup", back_populates="financial_estimates")
    estimate_lines = relationship("FinancialEstimateLine", back_populates="financial_estimate", cascade="all, delete-orphan")


class FinancialEstimateLine(Base):
    """
    Line items in a financial estimate
    """
    __tablename__ = "financial_estimate_lines"
    __table_args__ = (
        Index('idx_financial_estimate_lines_estimate', 'financial_estimate_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    financial_estimate_id = Column(UUID(as_uuid=True), ForeignKey("financial_estimates.id", ondelete="CASCADE"), nullable=False)
    service_item_id = Column(UUID(as_uuid=True), ForeignKey("service_items.id"))
    description = Column(Text)
    quantity = Column(Numeric)
    unit_rate = Column(Numeric)
    total_amount = Column(Numeric)
    coverage_category = Column(Text)  # 'payer', 'patient', 'non_medical', 'exclusion'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    financial_estimate = relationship("FinancialEstimate", back_populates="estimate_lines")
    service_item = relationship("ServiceItem", back_populates="financial_estimate_lines")


# ----------------------------------------------------------------------------
# Pre-Authorization / Cashless (3 models)
# ----------------------------------------------------------------------------


class PreauthCase(Base):
    """
    Cashless pre-authorization cases
    Heart of cashless control flow
    Maps to FHIR Claim with use = preauthorization
    """
    __tablename__ = "preauth_cases"
    __table_args__ = (
        Index('idx_preauth_cases_patient', 'patient_id', 'created_at'),
        Index('idx_preauth_cases_status', 'status', 'sla_due_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    coverage_id = Column(UUID(as_uuid=True), ForeignKey("coverages.id"), nullable=False)
    surgery_request_id = Column(UUID(as_uuid=True), ForeignKey("surgery_requests.id"))
    admission_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))  # IP encounter
    preauth_type = Column(Text, nullable=False)  # 'initial', 'enhancement', 'final'
    indication = Column(Text, nullable=False)
    estimated_cost = Column(Numeric)
    requested_amount = Column(Numeric)
    approved_amount = Column(Numeric)
    status = Column(Text, nullable=False, default='draft')  # 'draft', 'submitted', 'queried', 'approved', 'partially_approved', 'rejected', 'closed'
    payer_reference_number = Column(Text)  # TPA ref no.
    payer_plan_id = Column(UUID(as_uuid=True), ForeignKey("payer_plans.id"))
    sla_due_at = Column(DateTime(timezone=True))  # from payer_rules TAT
    assigned_queue_id = Column(UUID(as_uuid=True))
    assigned_user_id = Column(UUID(as_uuid=True))
    priority = Column(Text, default='normal')  # 'normal', 'high', 'critical'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    coverage = relationship("Coverage", back_populates="preauth_cases")
    documents = relationship("PreauthDocument", back_populates="preauth_case", cascade="all, delete-orphan")
    events = relationship("PreauthEvent", back_populates="preauth_case", cascade="all, delete-orphan")
    rcm_ai_tasks = relationship("RCMAITask", back_populates="preauth_case")


class PreauthDocument(Base):
    """
    Documents uploaded for pre-authorization (ID, policy, labs, imaging, estimates)
    """
    __tablename__ = "preauth_documents"
    __table_args__ = (
        Index('idx_preauth_documents_case', 'preauth_case_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    preauth_case_id = Column(UUID(as_uuid=True), ForeignKey("preauth_cases.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(Text, nullable=False)  # 'id_proof', 'policy_copy', 'consultation_note', 'lab_report', 'imaging_report', 'estimate'
    file_storage_uri = Column(Text, nullable=False)  # S3 or blob URI
    uploaded_by_user_id = Column(UUID(as_uuid=True))
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ocr_status = Column(Text, default='pending')  # 'pending', 'processed', 'failed'
    ocr_extracted_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    preauth_case = relationship("PreauthCase", back_populates="documents")
    rcm_ai_tasks = relationship("RCMAITask", back_populates="document")


class PreauthEvent(Base):
    """
    Event timeline for pre-authorization case
    """
    __tablename__ = "preauth_events"
    __table_args__ = (
        Index('idx_preauth_events_case', 'preauth_case_id', 'event_time'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    preauth_case_id = Column(UUID(as_uuid=True), ForeignKey("preauth_cases.id", ondelete="CASCADE"), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False)
    event_type = Column(Text, nullable=False)  # 'created', 'submitted', 'queried', 'approved', 'rejected', 'enhancement_requested', 'call_log'
    actor_type = Column(Text)  # 'system', 'payer', 'tpa', 'user'
    actor_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    preauth_case = relationship("PreauthCase", back_populates="events")


# ----------------------------------------------------------------------------
# Charge Capture / Patient Accounts (3 models)
# ----------------------------------------------------------------------------


class Account(Base):
    """
    Patient financial accounts (per episode/encounter)
    Maps to FHIR Account
    """
    __tablename__ = "accounts"
    __table_args__ = (
        Index('idx_accounts_patient', 'patient_id', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"))
    coverage_id = Column(UUID(as_uuid=True), ForeignKey("coverages.id"))
    account_type = Column(Text, nullable=False)  # 'ip', 'op', 'daycare'
    status = Column(Text, nullable=False, default='open')  # 'open', 'finalising', 'closed'
    total_charges = Column(Numeric, default=0)
    total_adjustments = Column(Numeric, default=0)
    total_payer_responsibility = Column(Numeric, default=0)
    total_patient_responsibility = Column(Numeric, default=0)
    currency = Column(Text, default='INR')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    coverage = relationship("Coverage", back_populates="accounts")
    charges = relationship("Charge", back_populates="account", cascade="all, delete-orphan")
    charge_packages = relationship("ChargePackage", back_populates="account", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="account")


class Charge(Base):
    """
    Individual itemized charges
    Maps to FHIR ChargeItem
    """
    __tablename__ = "charges"
    __table_args__ = (
        Index('idx_charges_account', 'account_id', 'charge_date'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    service_item_id = Column(UUID(as_uuid=True), ForeignKey("service_items.id"), nullable=False)
    charge_date = Column(DateTime(timezone=True), nullable=False)
    quantity = Column(Numeric, nullable=False)
    unit_rate = Column(Numeric, nullable=False)
    gross_amount = Column(Numeric, nullable=False)
    coverage_category = Column(Text)  # 'payer', 'patient', 'non_medical'
    is_package_component = Column(Boolean, default=False)
    package_definition_id = Column(UUID(as_uuid=True), ForeignKey("package_definitions.id"))
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    ordering_practitioner_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    charge_source = Column(Text)  # 'manual', 'order_auto', 'import'
    meta_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="charges")
    service_item = relationship("ServiceItem", back_populates="charges")
    package_definition = relationship("PackageDefinition", back_populates="charges")
    claim_lines = relationship("ClaimLine", back_populates="charge")


class ChargePackage(Base):
    """
    Package-based charges (alternative to itemized)
    """
    __tablename__ = "charge_packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    package_definition_id = Column(UUID(as_uuid=True), ForeignKey("package_definitions.id"), nullable=False)
    package_rate = Column(Numeric, nullable=False)
    coverage_category = Column(Text)  # typically 'payer'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="charge_packages")
    package_definition = relationship("PackageDefinition", back_populates="charge_packages")


# ----------------------------------------------------------------------------
# Claims (2 models)
# ----------------------------------------------------------------------------


class Claim(Base):
    """
    Insurance claims
    Maps to FHIR Claim
    """
    __tablename__ = "claims"
    __table_args__ = (
        Index('idx_claims_payer_status', 'payer_id', 'status', 'submission_date'),
        Index('idx_claims_account', 'account_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    coverage_id = Column(UUID(as_uuid=True), ForeignKey("coverages.id"), nullable=False)
    payer_id = Column(UUID(as_uuid=True), ForeignKey("payers.id"), nullable=False)
    payer_plan_id = Column(UUID(as_uuid=True), ForeignKey("payer_plans.id"))
    claim_number = Column(Text)
    claim_type = Column(Text, nullable=False)  # 'institutional', 'professional'
    use = Column(Text, nullable=False)  # 'preauthorization', 'claim'
    status = Column(Text, nullable=False, default='draft')  # 'draft', 'submitted', 'in_review', 'paid', 'partially_paid', 'denied', 'cancelled'
    total_claimed_amount = Column(Numeric)
    total_approved_amount = Column(Numeric)
    total_patient_responsibility = Column(Numeric)
    currency = Column(Text, default='INR')
    submission_channel = Column(Text)  # 'portal', 'EDI', 'email'
    submission_reference = Column(Text)
    submission_date = Column(DateTime(timezone=True))
    fhir_claim_id = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="claims")
    coverage = relationship("Coverage", back_populates="claims")
    payer = relationship("Payer", back_populates="claims")
    payer_plan = relationship("PayerPlan", back_populates="claims")
    claim_lines = relationship("ClaimLine", back_populates="claim", cascade="all, delete-orphan")
    remittance_lines = relationship("RemittanceLine", back_populates="claim")
    denials = relationship("Denial", back_populates="claim")
    rcm_ai_tasks = relationship("RCMAITask", back_populates="claim")


class ClaimLine(Base):
    """
    Line items in a claim
    """
    __tablename__ = "claim_lines"
    __table_args__ = (
        Index('idx_claim_lines_claim', 'claim_id', 'line_number'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    charge_id = Column(UUID(as_uuid=True), ForeignKey("charges.id"))
    line_number = Column(Integer)
    service_item_id = Column(UUID(as_uuid=True), ForeignKey("service_items.id"))
    service_date_from = Column(Date)
    service_date_to = Column(Date)
    quantity = Column(Numeric)
    unit_price = Column(Numeric)
    line_amount = Column(Numeric)
    diagnosis_codes = Column(ARRAY(Text))  # ICD-10 codes
    procedure_codes = Column(ARRAY(Text))  # if line-specific
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    claim = relationship("Claim", back_populates="claim_lines")
    charge = relationship("Charge", back_populates="claim_lines")
    service_item = relationship("ServiceItem", back_populates="claim_lines")


# ----------------------------------------------------------------------------
# Payment / Remittance (2 models)
# ----------------------------------------------------------------------------


class Remittance(Base):
    """
    Payment remittances from payers (EOB/ERA)
    """
    __tablename__ = "remittances"
    __table_args__ = (
        Index('idx_remittances_payer_date', 'payer_id', 'payment_date'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    payer_id = Column(UUID(as_uuid=True), ForeignKey("payers.id"))
    payment_reference = Column(Text, nullable=False)  # NEFT/RTGS/cheque no.
    payment_date = Column(DateTime(timezone=True), nullable=False)
    total_payment_amount = Column(Numeric, nullable=False)
    currency = Column(Text, default='INR')
    remittance_source = Column(Text)  # 'manual', 'ERA', 'upload'
    raw_data_uri = Column(Text)  # original file/object
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payer = relationship("Payer", back_populates="remittances")
    remittance_lines = relationship("RemittanceLine", back_populates="remittance", cascade="all, delete-orphan")


class RemittanceLine(Base):
    """
    Line items in remittance (claim-level payments/denials)
    """
    __tablename__ = "remittance_lines"
    __table_args__ = (
        Index('idx_remittance_lines_claim', 'claim_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    remittance_id = Column(UUID(as_uuid=True), ForeignKey("remittances.id", ondelete="CASCADE"), nullable=False)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"))
    claim_number = Column(Text)
    paid_amount = Column(Numeric)
    patient_responsibility_amount = Column(Numeric)
    denial_code = Column(Text)
    denial_reason = Column(Text)
    adjustment_codes = Column(ARRAY(Text))  # e.g., CO45 etc.
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    remittance = relationship("Remittance", back_populates="remittance_lines")
    claim = relationship("Claim", back_populates="remittance_lines")
    denials = relationship("Denial", back_populates="remittance_line")


# ----------------------------------------------------------------------------
# Denials Management (2 models)
# ----------------------------------------------------------------------------


class Denial(Base):
    """
    Claim denials requiring follow-up and appeals
    """
    __tablename__ = "denials"
    __table_args__ = (
        Index('idx_denials_status', 'status', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    remittance_line_id = Column(UUID(as_uuid=True), ForeignKey("remittance_lines.id"))
    denial_code = Column(Text)
    denial_category = Column(Text)  # 'authorization', 'medical_necessity', 'coding', 'timely_filing', 'documentation'
    denial_reason = Column(Text)
    amount_denied = Column(Numeric)
    status = Column(Text, nullable=False, default='open')  # 'open', 'in_appeal', 'resolved', 'written_off'
    root_cause = Column(Text)  # 'missing_document', 'wrong_code', 'payer_error'
    assigned_user_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    claim = relationship("Claim", back_populates="denials")
    remittance_line = relationship("RemittanceLine", back_populates="denials")
    denial_actions = relationship("DenialAction", back_populates="denial", cascade="all, delete-orphan")
    rcm_ai_tasks = relationship("RCMAITask", back_populates="denial")


class DenialAction(Base):
    """
    Actions taken on denials (appeals, calls, write-offs)
    """
    __tablename__ = "denial_actions"
    __table_args__ = (
        Index('idx_denial_actions_denial', 'denial_id', 'action_time'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    denial_id = Column(UUID(as_uuid=True), ForeignKey("denials.id", ondelete="CASCADE"), nullable=False)
    action_time = Column(DateTime(timezone=True), nullable=False)
    action_type = Column(Text, nullable=False)  # 'appeal_filed', 'info_submitted', 'call_log', 'writeoff'
    actor_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    denial = relationship("Denial", back_populates="denial_actions")


# ----------------------------------------------------------------------------
# Cashless Control Tower (3 models)
# ----------------------------------------------------------------------------


class WorkQueue(Base):
    """
    Work queues for RCM workflows (pre-auth, claims, denials, AR)
    """
    __tablename__ = "work_queues"
    __table_args__ = (
        Index('uniq_work_queues_code_tenant', 'tenant_id', 'code', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(Text, nullable=False)  # 'PREAUTH_NEW', 'PREAUTH_QUERY', 'CLAIMS_TO_SUBMIT', 'DENIALS_HIGH_VALUE'
    name = Column(Text, nullable=False)
    description = Column(Text)
    domain = Column(Text, nullable=False)  # 'preauth', 'claims', 'denials', 'ar'
    filter_config = Column(JSONB)  # definition of items included
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    work_items = relationship("WorkItem", back_populates="work_queue")


class WorkItem(Base):
    """
    Individual work items in queues
    """
    __tablename__ = "work_items"
    __table_args__ = (
        Index('idx_work_items_queue_status', 'work_queue_id', 'status', 'due_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    work_queue_id = Column(UUID(as_uuid=True), ForeignKey("work_queues.id"), nullable=False)
    domain = Column(Text, nullable=False)  # 'preauth', 'claim', 'denial'
    entity_id = Column(UUID(as_uuid=True), nullable=False)  # preauth_case_id / claim_id / denial_id
    priority = Column(Text, default='normal')  # 'low', 'normal', 'high', 'critical'
    status = Column(Text, nullable=False, default='open')  # 'open', 'in_progress', 'completed', 'snoozed'
    assigned_user_id = Column(UUID(as_uuid=True))
    due_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    work_queue = relationship("WorkQueue", back_populates="work_items")


class SLARule(Base):
    """
    SLA rules for RCM workflows (TAT tracking)
    """
    __tablename__ = "sla_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    domain = Column(Text, nullable=False)  # 'preauth', 'claims', 'denials'
    name = Column(Text, nullable=False)
    condition_config = Column(JSONB)  # e.g. { "preauth_type":"initial","payer_id":... }
    tat_hours = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# ----------------------------------------------------------------------------
# RCM AI Orchestrator (2 models)
# ----------------------------------------------------------------------------


class RCMAITask(Base):
    """
    AI tasks for RCM workflows (OCR, coding, denial classification, appeals)
    """
    __tablename__ = "rcm_ai_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    domain = Column(Text, nullable=False)  # 'preauth', 'claim_coding', 'denial', 'analytics'
    preauth_case_id = Column(UUID(as_uuid=True), ForeignKey("preauth_cases.id"))
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"))
    denial_id = Column(UUID(as_uuid=True), ForeignKey("denials.id"))
    document_id = Column(UUID(as_uuid=True), ForeignKey("preauth_documents.id"))
    task_type = Column(Text, nullable=False)  # 'doc_ocr', 'clinical_summary', 'coding_suggestion', 'denial_classification', 'appeal_draft'
    status = Column(Text, nullable=False, default='queued')  # 'queued', 'running', 'completed', 'failed'
    requested_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    preauth_case = relationship("PreauthCase", back_populates="rcm_ai_tasks")
    claim = relationship("Claim", back_populates="rcm_ai_tasks")
    denial = relationship("Denial", back_populates="rcm_ai_tasks")
    document = relationship("PreauthDocument", back_populates="rcm_ai_tasks")
    outputs = relationship("RCMAIOutput", back_populates="rcm_ai_task", cascade="all, delete-orphan")


class RCMAIOutput(Base):
    """
    AI outputs for RCM tasks
    """
    __tablename__ = "rcm_ai_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    rcm_ai_task_id = Column(UUID(as_uuid=True), ForeignKey("rcm_ai_tasks.id", ondelete="CASCADE"), nullable=False)
    output_type = Column(Text, nullable=False)  # 'structured_ocr', 'summary', 'code_suggestions', 'denial_category', 'appeal_text'
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    rcm_ai_task = relationship("RCMAITask", back_populates="outputs")


# ============================================================================
# PHASE 12: OPERATIONS COMMAND CENTER (INTEGRATED CLINICAL + FINANCIAL COMMAND)
# ============================================================================


# ----------------------------------------------------------------------------
# Event Ingestion (2 models)
# ----------------------------------------------------------------------------


class OpsEventSource(Base):
    """
    Event source systems for operational command center
    """
    __tablename__ = "ops_event_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    source_system = Column(Text, nullable=False)  # 'ehr', 'or', 'lis', 'rcm', 'ed', 'icu'
    source_stream = Column(Text, nullable=False)  # 'admission_events', 'or_case_events', etc.
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class OpsEvent(Base):
    """
    Operational event log (optional persistent log beyond Kafka)
    """
    __tablename__ = "ops_events"
    __table_args__ = (
        Index('idx_ops_events_processed', 'processed', 'event_time'),
        Index('idx_ops_events_entity', 'entity_type', 'entity_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    source_system = Column(Text, nullable=False)  # 'or', 'lis', 'rcm'
    event_type = Column(Text, nullable=False)  # 'admission_created', 'bed_transfer', 'or_case_status_changed', etc.
    entity_type = Column(Text, nullable=False)  # 'admission', 'bed', 'or_case', 'lab_order', 'claim', 'preauth_case'
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False)
    payload = Column(JSONB, nullable=False)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# ----------------------------------------------------------------------------
# Hospital Units & State Projections (9 models)
# ----------------------------------------------------------------------------


class HospitalUnit(Base):
    """
    Hospital operational units (wards, ICUs, ED, OT, lab, imaging)
    """
    __tablename__ = "hospital_units"
    __table_args__ = (
        Index('uniq_hospital_units_code_tenant', 'tenant_id', 'code', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(Text, nullable=False)  # 'WARD_3', 'ICU_1', 'ED_MAIN'
    name = Column(Text, nullable=False)
    unit_type = Column(Text, nullable=False)  # 'ward', 'icu', 'ed', 'ot', 'lab', 'imaging'
    parent_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    unit_snapshots = relationship("UnitSnapshot", back_populates="unit")
    bed_snapshots = relationship("BedSnapshot", back_populates="unit")
    or_status_snapshots = relationship("ORStatusSnapshot", back_populates="or_room")
    ed_status_snapshots = relationship("EDStatusSnapshot", back_populates="ed_unit")
    lab_workload_snapshots = relationship("LabWorkloadSnapshot", back_populates="lab_unit")
    imaging_workload_snapshots = relationship("ImagingWorkloadSnapshot", back_populates="imaging_unit")


class UnitSnapshot(Base):
    """
    High-level snapshot per clinical unit (ward/ICU/ED)
    """
    __tablename__ = "unit_snapshots"
    __table_args__ = (
        Index('idx_unit_snapshots_unit_time', 'unit_id', 'snapshot_time'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("hospital_units.id"), nullable=False)
    snapshot_time = Column(DateTime(timezone=True), nullable=False)
    total_beds = Column(Integer)
    occupied_beds = Column(Integer)
    reserved_beds = Column(Integer)
    blocked_beds = Column(Integer)
    admissions_last_4h = Column(Integer)
    discharges_last_4h = Column(Integer)
    transfer_in_last_4h = Column(Integer)
    transfer_out_last_4h = Column(Integer)
    occupancy_rate = Column(Numeric)  # computed
    acuity_index = Column(Numeric)  # weighted severity (optional)
    ed_waiting_count = Column(Integer)  # if ED
    ed_waiting_longer_than_30m = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    unit = relationship("HospitalUnit", back_populates="unit_snapshots")


class BedSnapshot(Base):
    """
    Fine-grained per-bed state snapshot
    """
    __tablename__ = "bed_snapshots"
    __table_args__ = (
        Index('idx_bed_snapshots_bed_time', 'bed_id', 'snapshot_time'),
        Index('idx_bed_snapshots_unit_status', 'unit_id', 'status', 'snapshot_time'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("hospital_units.id"), nullable=False)
    snapshot_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(Text, nullable=False)  # 'available', 'occupied', 'reserved', 'cleaning', 'blocked'
    current_patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    current_encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    last_status_change = Column(DateTime(timezone=True))
    isolation_flag = Column(Boolean, default=False)
    acuity_level = Column(Text)  # 'low', 'medium', 'high', if available
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    unit = relationship("HospitalUnit", back_populates="bed_snapshots")


class ORStatusSnapshot(Base):
    """
    Per OR room snapshot for near real-time OR command
    """
    __tablename__ = "or_status_snapshots"
    __table_args__ = (
        Index('idx_or_status_snapshots_room_time', 'or_room_id', 'snapshot_time'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    or_room_id = Column(UUID(as_uuid=True), ForeignKey("hospital_units.id"), nullable=False)
    snapshot_time = Column(DateTime(timezone=True), nullable=False)
    current_case_id = Column(UUID(as_uuid=True), ForeignKey("surgical_cases.id"))
    current_case_status = Column(Text)  # 'scheduled', 'in_progress', 'closing', 'cleanup'
    scheduled_case_count_today = Column(Integer)
    completed_case_count_today = Column(Integer)
    delayed_case_count_today = Column(Integer)
    avg_delay_minutes_today = Column(Numeric)
    utilization_rate_today = Column(Numeric)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    or_room = relationship("HospitalUnit", back_populates="or_status_snapshots")


class EDStatusSnapshot(Base):
    """
    ED crowding view snapshot
    """
    __tablename__ = "ed_status_snapshots"
    __table_args__ = (
        Index('idx_ed_status_snapshots_unit_time', 'ed_unit_id', 'snapshot_time'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    ed_unit_id = Column(UUID(as_uuid=True), ForeignKey("hospital_units.id"), nullable=False)
    snapshot_time = Column(DateTime(timezone=True), nullable=False)
    total_in_ed = Column(Integer)
    waiting_for_triage = Column(Integer)
    waiting_for_provider = Column(Integer)
    waiting_for_bed = Column(Integer)
    avg_wait_time_triage_minutes = Column(Numeric)
    avg_wait_time_provider_minutes = Column(Numeric)
    lwbs_last_4h = Column(Integer)  # left without being seen
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    ed_unit = relationship("HospitalUnit", back_populates="ed_status_snapshots")


class LabWorkloadSnapshot(Base):
    """
    Lab workload snapshot
    """
    __tablename__ = "lab_workload_snapshots"
    __table_args__ = (
        Index('idx_lab_workload_snapshots_unit_time', 'lab_unit_id', 'snapshot_time'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    lab_unit_id = Column(UUID(as_uuid=True), ForeignKey("hospital_units.id"), nullable=False)
    snapshot_time = Column(DateTime(timezone=True), nullable=False)
    total_pending = Column(Integer)
    critical_pending = Column(Integer)
    median_turnaround_minutes = Column(Numeric)
    percentile90_turnaround_minutes = Column(Numeric)
    pending_by_priority = Column(JSONB)  # e.g. { "stat": 5, "routine": 42 }
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    lab_unit = relationship("HospitalUnit", back_populates="lab_workload_snapshots")


class ImagingWorkloadSnapshot(Base):
    """
    Imaging workload snapshot
    """
    __tablename__ = "imaging_workload_snapshots"
    __table_args__ = (
        Index('idx_imaging_workload_snapshots_unit_time', 'imaging_unit_id', 'snapshot_time'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    imaging_unit_id = Column(UUID(as_uuid=True), ForeignKey("hospital_units.id"), nullable=False)
    snapshot_time = Column(DateTime(timezone=True), nullable=False)
    total_pending = Column(Integer)
    pending_urgent = Column(Integer)
    median_report_turnaround_minutes = Column(Numeric)
    pending_by_modality = Column(JSONB)  # { "CT": 3, "MRI": 2, "XRay": 15 }
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    imaging_unit = relationship("HospitalUnit", back_populates="imaging_workload_snapshots")


class RCMWorkloadSnapshot(Base):
    """
    RCM workload snapshot
    """
    __tablename__ = "rcm_workload_snapshots"
    __table_args__ = (
        Index('idx_rcm_workload_snapshots_time', 'snapshot_time'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    snapshot_time = Column(DateTime(timezone=True), nullable=False)
    preauth_pending = Column(Integer)
    preauth_sla_breach_risk = Column(Integer)
    claims_to_submit = Column(Integer)
    claims_in_review = Column(Integer)
    denials_open = Column(Integer)
    denials_high_value = Column(Integer)
    ar_total = Column(Numeric)
    ar_aging_buckets = Column(JSONB)  # { "0-30": x, "31-60": y, ... }
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class OpsKPI(Base):
    """
    Daily/hourly operational KPI aggregates
    """
    __tablename__ = "ops_kpis"
    __table_args__ = (
        Index('idx_ops_kpis_metric_period', 'metric_name', 'period_start'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(Text, nullable=False)  # 'hour', 'day'
    metric_name = Column(Text, nullable=False)  # 'hospital_occupancy', 'ed_lwbs_rate', 'or_utilization', 'lab_tat'
    metric_value = Column(Numeric)
    metric_dimensions = Column(JSONB)  # e.g. { "unit": "ICU_1" }
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# ----------------------------------------------------------------------------
# Alerts & Playbooks (5 models)
# ----------------------------------------------------------------------------


class OpsAlertRule(Base):
    """
    Alert rules for operational command center
    """
    __tablename__ = "ops_alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(Text, nullable=False)  # 'ICU occupancy > 90%', 'ED crowding'
    description = Column(Text)
    domain = Column(Text, nullable=False)  # 'bed_management', 'or', 'ed', 'lab', 'imaging', 'rcm'
    rule_type = Column(Text, nullable=False)  # 'threshold', 'trend', 'composite'
    condition_config = Column(JSONB, nullable=False)  # JSON describing thresholds, metrics, units
    severity = Column(Text, nullable=False)  # 'info', 'warning', 'critical'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ops_alerts = relationship("OpsAlert", back_populates="alert_rule")
    playbooks = relationship("OpsPlaybook", back_populates="trigger_alert_rule")


class OpsAlert(Base):
    """
    Operational alerts
    """
    __tablename__ = "ops_alerts"
    __table_args__ = (
        Index('idx_ops_alerts_status_severity', 'status', 'severity', 'triggered_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    alert_rule_id = Column(UUID(as_uuid=True), ForeignKey("ops_alert_rules.id"))
    domain = Column(Text, nullable=False)
    metric_name = Column(Text)
    metric_value = Column(Numeric)
    metric_context = Column(JSONB)  # unit_id, or_room_id, payer, etc.
    severity = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default='open')  # 'open', 'acked', 'in_progress', 'resolved', 'dismissed'
    triggered_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    assigned_user_id = Column(UUID(as_uuid=True))
    assigned_team = Column(Text)  # 'bed_management', 'or', 'rcm'
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    alert_rule = relationship("OpsAlertRule", back_populates="ops_alerts")
    alert_actions = relationship("OpsAlertAction", back_populates="alert", cascade="all, delete-orphan")


class OpsAlertAction(Base):
    """
    Actions taken on alerts
    """
    __tablename__ = "ops_alert_actions"
    __table_args__ = (
        Index('idx_ops_alert_actions_alert', 'alert_id', 'action_time'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("ops_alerts.id", ondelete="CASCADE"), nullable=False)
    action_time = Column(DateTime(timezone=True), nullable=False)
    actor_id = Column(UUID(as_uuid=True))
    action_type = Column(Text, nullable=False)  # 'ack', 'assign', 'comment', 'resolve'
    details = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    alert = relationship("OpsAlert", back_populates="alert_actions")


class OpsPlaybook(Base):
    """
    Standard response playbooks per alert type
    """
    __tablename__ = "ops_playbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(Text, nullable=False)  # 'ED crowding > 120%', 'ICU full'
    domain = Column(Text, nullable=False)  # 'ed', 'icu', 'or', 'rcm'
    trigger_alert_rule_id = Column(UUID(as_uuid=True), ForeignKey("ops_alert_rules.id"))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trigger_alert_rule = relationship("OpsAlertRule", back_populates="playbooks")
    playbook_steps = relationship("OpsPlaybookStep", back_populates="playbook", cascade="all, delete-orphan")


class OpsPlaybookStep(Base):
    """
    Steps in a playbook
    """
    __tablename__ = "ops_playbook_steps"
    __table_args__ = (
        Index('idx_ops_playbook_steps_playbook_order', 'playbook_id', 'step_order'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    playbook_id = Column(UUID(as_uuid=True), ForeignKey("ops_playbooks.id", ondelete="CASCADE"), nullable=False)
    step_order = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)  # 'Call ICU consultant', 'Open surge ward'
    instructions = Column(Text, nullable=False)
    responsible_role = Column(Text)  # 'bed_manager', 'ed_head', 'rcm_manager'
    expected_completion_minutes = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    playbook = relationship("OpsPlaybook", back_populates="playbook_steps")


# ----------------------------------------------------------------------------
# Ops AI Orchestrator (2 models)
# ----------------------------------------------------------------------------


class OpsAITask(Base):
    """
    AI tasks for operational command center
    """
    __tablename__ = "ops_ai_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    task_type = Column(Text, nullable=False)  # 'situation_summary', 'bottleneck_analysis', 'what_if_scenario', 'incident_timeline'
    snapshot_time = Column(DateTime(timezone=True))
    input_context = Column(JSONB)  # e.g. specific unit, date range
    status = Column(Text, nullable=False, default='queued')  # 'queued', 'running', 'completed', 'failed'
    requested_by_user_id = Column(UUID(as_uuid=True))
    requested_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    outputs = relationship("OpsAIOutput", back_populates="ops_ai_task", cascade="all, delete-orphan")


class OpsAIOutput(Base):
    """
    AI outputs for operational tasks
    """
    __tablename__ = "ops_ai_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    ops_ai_task_id = Column(UUID(as_uuid=True), ForeignKey("ops_ai_tasks.id", ondelete="CASCADE"), nullable=False)
    output_type = Column(Text, nullable=False)  # 'summary', 'root_cause', 'recommendations', 'timeline'
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    ops_ai_task = relationship("OpsAITask", back_populates="outputs")


# ============================================================================
# PHASE 4: PRM ADVANCED MODULES
# ============================================================================
# Vector Search, AI Agents, Clinical Intake
# Added: November 2024
# ============================================================================


# ----------------------------------------------------------------------------
# Vector Search Module (1 model)
# ----------------------------------------------------------------------------


class TextChunk(Base):
    """
    Indexable chunk of text with vector embeddings for semantic search

    Sources:
      - transcript: Message/conversation transcripts
      - ticket_note: Support ticket notes
      - knowledge: Free-text documents and knowledge base

    For semantic search, text is:
      1. Chunked into manageable sizes (800-1000 chars)
      2. Embedded into vectors (384 dimensions)
      3. Searchable via hybrid search (vector similarity + full-text)

    Production Note:
      - Currently stores embeddings as JSON array
      - For better performance, migrate to pgvector extension
      - pgvector provides optimized vector operations and indexing
    """
    __tablename__ = "text_chunk"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Source identification
    source_type = Column(String(32), nullable=False, index=True)  # transcript | ticket_note | knowledge
    source_id = Column(String(64), nullable=False, index=True)

    # Optional patient link
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True, index=True)

    # Optional cross-references for provenance
    locator = Column(JSONB, comment="Cross-references: {'conversation_id': '...', 'message_id': '...'}")

    # Content
    text = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0, nullable=False)

    # Vector embedding (JSON for now - migrate to pgvector.Vector(384) for production)
    embedding = Column(JSONB, nullable=False, comment="384-dimensional embedding vector (stored as JSON array)")

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<TextChunk {self.id} source={self.source_type}:{self.source_id} chunk={self.chunk_index}>"


# ----------------------------------------------------------------------------
# AI Agents Module (1 model)
# ----------------------------------------------------------------------------


class ToolRun(Base):
    """
    AI agent tool execution log

    Tracks all tools executed by AI agents for:
      - Audit trail
      - Debugging failed executions
      - Analytics on tool usage
      - Replay capability for testing

    Examples of tools:
      - create_ticket
      - confirm_appointment
      - send_notification
      - update_patient
      - book_appointment
    """
    __tablename__ = "tool_run"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Tool information
    tool = Column(String(64), nullable=False, index=True)
    inputs = Column(JSONB, nullable=False)
    outputs = Column(JSONB)

    # Execution result
    success = Column(Boolean, default=True, nullable=False, index=True)
    error = Column(String(400))

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        status = "success" if self.success else "failed"
        return f"<ToolRun {self.id} tool={self.tool} status={status}>"


# ----------------------------------------------------------------------------
# Clinical Intake Module (10 models)
# ----------------------------------------------------------------------------


class IntakeSession(Base):
    """
    Intake session - groups all intake data for a patient/lead

    Workflow:
      1. Create session (can be anonymous)
      2. Collect data via upsert_records
      3. Link patient (with consent)
      4. Submit session
      5. Create appointment

    Status:
      - open: Actively collecting data
      - submitted: Complete, ready for review
      - closed: Processed and archived
    """
    __tablename__ = "intake_session"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Optional references
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True, comment="Linked patient (requires consent)")
    conversation_id = Column(UUID(as_uuid=True), index=True, comment="WhatsApp conversation ID")

    # Status
    status = Column(String(16), default="open", nullable=False, index=True, comment="open | submitted | closed")

    # Context metadata
    context = Column(JSONB, comment="Channel, locale, source, etc.")

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<IntakeSession {self.id} status={self.status}>"


class IntakeSummary(Base):
    """AI-generated summary of intake session"""
    __tablename__ = "intake_summary"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("intake_session.id"), nullable=False, index=True)

    text = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<IntakeSummary {self.id} session={self.session_id}>"


class IntakeChiefComplaint(Base):
    """Primary reason for visit"""
    __tablename__ = "intake_chief_complaint"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("intake_session.id"), nullable=False, index=True)

    text = Column(Text, nullable=False)
    codes = Column(JSONB, comment="Coded complaint")

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class IntakeSymptom(Base):
    """Individual symptom with clinical details"""
    __tablename__ = "intake_symptom"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("intake_session.id"), nullable=False, index=True)

    client_item_id = Column(String(64), index=True, comment="Client-side ID for idempotency")

    code = Column(JSONB)
    onset = Column(String(32))
    duration = Column(String(32))
    severity = Column(String(32))
    frequency = Column(String(32))
    laterality = Column(String(32))
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class IntakeAllergy(Base):
    """Allergy information"""
    __tablename__ = "intake_allergy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("intake_session.id"), nullable=False, index=True)

    client_item_id = Column(String(64), index=True)

    substance = Column(String(120), nullable=False)
    reaction = Column(String(120))
    severity = Column(String(32))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class IntakeMedication(Base):
    """Current medication"""
    __tablename__ = "intake_medication"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("intake_session.id"), nullable=False, index=True)

    client_item_id = Column(String(64), index=True)

    name = Column(String(120), nullable=False)
    dose = Column(String(120))
    schedule = Column(String(120))
    adherence = Column(String(64))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class IntakeConditionHistory(Base):
    """Past medical history"""
    __tablename__ = "intake_condition_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("intake_session.id"), nullable=False, index=True)

    client_item_id = Column(String(64), index=True)

    condition = Column(String(160), nullable=False)
    status = Column(String(32))
    year_or_age = Column(String(32))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class IntakeFamilyHistory(Base):
    """Family medical history"""
    __tablename__ = "intake_family_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("intake_session.id"), nullable=False, index=True)

    client_item_id = Column(String(64), index=True)

    relative = Column(String(64), nullable=False)
    condition = Column(String(160), nullable=False)
    age_of_onset = Column(String(32))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class IntakeSocialHistory(Base):
    """Social history data"""
    __tablename__ = "intake_social_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("intake_session.id"), nullable=False, index=True)

    data = Column(JSONB, nullable=False, comment="Social history fields")

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class IntakeNote(Base):
    """Free-text notes"""
    __tablename__ = "intake_note"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("intake_session.id"), nullable=False, index=True)

    text = Column(Text, nullable=False)
    visibility = Column(String(16), default="internal", nullable=False, comment="internal | external")

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
