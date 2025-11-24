# Healthcare Platform Event Catalog

## Overview

This document catalogs all domain events published by the healthcare platform. Events follow a hierarchical naming convention: `{Domain}.{Action}`.

**Last Updated**: 2024-11-24
**Total Events**: 470+

## Event Categories

- [Patient Events](#patient-events)
- [Practitioner Events](#practitioner-events)
- [Consent Events](#consent-events)
- [Appointment Events](#appointment-events)
- [Encounter Events](#encounter-events)
- [Journey Events](#journey-events)
- [Communication Events](#communication-events)
- [Admission & Bed Management](#admission--bed-management)
- [Clinical Events](#clinical-events)
- [Orders & Medication](#orders--medication)
- [Laboratory Events](#laboratory-events)
- [Imaging & Radiology](#imaging--radiology)
- [Surgery & Perioperative](#surgery--perioperative)
- [Revenue Cycle Management](#revenue-cycle-management)
- [Operations Command Center](#operations-command-center)

---

## Patient Events

### Patient.Created
**Triggered When**: New patient record is created
**Topic**: `healthtech.patient.events`
**Payload**:
```json
{
  "patient_id": "uuid",
  "identifiers": [
    {"system": "MRN", "value": "MRN12345"},
    {"system": "NRIC", "value": "S1234567A"}
  ],
  "name": "John Doe",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "phone_primary": "+65-12345678",
  "email": "john.doe@example.com"
}
```

### Patient.Updated
**Triggered When**: Patient demographics are updated
**Topic**: `healthtech.patient.events`
**Payload**:
```json
{
  "patient_id": "uuid",
  "updated_fields": ["phone_primary", "email"],
  "previous_values": {},
  "new_values": {}
}
```

### Patient.Merged
**Triggered When**: Duplicate patient records are merged
**Topic**: `healthtech.patient.events`
**Payload**:
```json
{
  "surviving_patient_id": "uuid",
  "merged_patient_id": "uuid",
  "merge_reason": "Duplicate record",
  "merged_by_user_id": "uuid"
}
```

### Patient.Deceased
**Triggered When**: Patient is marked as deceased
**Topic**: `healthtech.patient.events`
**Payload**:
```json
{
  "patient_id": "uuid",
  "date_of_death": "2024-01-15",
  "cause_of_death": "Natural causes",
  "certified_by": "uuid"
}
```

---

## Appointment Events

### Appointment.Created
**Triggered When**: New appointment is scheduled
**Topic**: `healthtech.appointment.events`
**Payload**:
```json
{
  "appointment_id": "uuid",
  "patient_id": "uuid",
  "practitioner_id": "uuid",
  "location_id": "uuid",
  "specialty": "Cardiology",
  "appointment_type": "Follow-up",
  "start_time": "2024-11-25T10:00:00Z",
  "end_time": "2024-11-25T10:30:00Z",
  "status": "scheduled"
}
```

### Appointment.Confirmed
**Triggered When**: Patient confirms appointment
**Topic**: `healthtech.appointment.events`
**Payload**:
```json
{
  "appointment_id": "uuid",
  "confirmed_at": "2024-11-24T08:00:00Z",
  "confirmed_via": "SMS"
}
```

### Appointment.CheckedIn
**Triggered When**: Patient checks in for appointment
**Topic**: `healthtech.appointment.events`
**Payload**:
```json
{
  "appointment_id": "uuid",
  "checked_in_at": "2024-11-25T09:55:00Z",
  "check_in_method": "QR_Code",
  "location": "Reception A"
}
```

### Appointment.Cancelled
**Triggered When**: Appointment is cancelled
**Topic**: `healthtech.appointment.events`
**Payload**:
```json
{
  "appointment_id": "uuid",
  "cancelled_by": "patient|provider|system",
  "cancellation_reason": "Patient request",
  "cancelled_at": "2024-11-24T12:00:00Z"
}
```

---

## Journey Events (PRM)

### Journey.Created
**Triggered When**: New patient journey template is created
**Topic**: `healthtech.journeys.events`
**Payload**:
```json
{
  "journey_id": "uuid",
  "journey_name": "Cardiac Surgery Journey",
  "specialty": "Cardiology",
  "stages": [
    {"stage_id": "pre-op", "name": "Pre-operative Assessment"},
    {"stage_id": "surgery", "name": "Surgery"},
    {"stage_id": "post-op", "name": "Post-operative Care"}
  ],
  "created_by": "uuid"
}
```

### Journey.Instance.Created
**Triggered When**: Patient is enrolled in a journey
**Topic**: `healthtech.journeys.events`
**Payload**:
```json
{
  "instance_id": "uuid",
  "journey_id": "uuid",
  "patient_id": "uuid",
  "started_at": "2024-11-24T10:00:00Z",
  "expected_completion": "2024-12-24"
}
```

### Journey.StageEntered
**Triggered When**: Patient enters a journey stage
**Topic**: `healthtech.journeys.events`
**Payload**:
```json
{
  "instance_id": "uuid",
  "stage_id": "pre-op",
  "stage_name": "Pre-operative Assessment",
  "entered_at": "2024-11-24T10:00:00Z"
}
```

### Journey.StageCompleted
**Triggered When**: Patient completes a journey stage
**Topic**: `healthtech.journeys.events`
**Payload**:
```json
{
  "instance_id": "uuid",
  "stage_id": "pre-op",
  "completed_at": "2024-11-25T15:00:00Z",
  "completion_status": "success|partial|skipped"
}
```

---

## Clinical Events

### Vitals.Recorded
**Triggered When**: Vital signs are recorded
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "observation_id": "uuid",
  "patient_id": "uuid",
  "encounter_id": "uuid",
  "recorded_at": "2024-11-24T10:00:00Z",
  "vitals": {
    "blood_pressure_systolic": 120,
    "blood_pressure_diastolic": 80,
    "heart_rate": 72,
    "temperature": 36.8,
    "respiratory_rate": 16,
    "oxygen_saturation": 98
  },
  "recorded_by": "uuid"
}
```

### Order.Created
**Triggered When**: Clinical order is created
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "order_id": "uuid",
  "patient_id": "uuid",
  "encounter_id": "uuid",
  "order_type": "lab|imaging|medication|procedure",
  "description": "Complete Blood Count",
  "priority": "routine|urgent|stat",
  "ordered_by": "uuid",
  "ordered_at": "2024-11-24T10:00:00Z"
}
```

---

## Admission & Bed Management

### Admission.Created
**Triggered When**: Patient admission is initiated
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "admission_id": "uuid",
  "patient_id": "uuid",
  "admission_type": "elective|emergency",
  "admitting_diagnosis": "Chest pain",
  "ward_id": "uuid",
  "expected_length_of_stay": 3,
  "admitted_by": "uuid",
  "admission_time": "2024-11-24T10:00:00Z"
}
```

### Bed.Assigned
**Triggered When**: Bed is assigned to patient
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "assignment_id": "uuid",
  "bed_id": "uuid",
  "patient_id": "uuid",
  "admission_id": "uuid",
  "ward_id": "uuid",
  "bed_number": "A-101",
  "assigned_at": "2024-11-24T10:30:00Z"
}
```

### Bed.StatusChanged
**Triggered When**: Bed status changes
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "bed_id": "uuid",
  "previous_status": "occupied",
  "new_status": "cleaning",
  "changed_at": "2024-11-24T14:00:00Z",
  "changed_by": "uuid"
}
```

---

## Laboratory Events

### LabOrder.Created
**Triggered When**: Lab order is placed
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "order_id": "uuid",
  "patient_id": "uuid",
  "encounter_id": "uuid",
  "test_catalog_items": [
    {"test_code": "CBC", "test_name": "Complete Blood Count"},
    {"test_code": "BMP", "test_name": "Basic Metabolic Panel"}
  ],
  "priority": "routine",
  "ordered_by": "uuid"
}
```

### LabSpecimen.Collected
**Triggered When**: Lab specimen is collected
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "specimen_id": "uuid",
  "order_id": "uuid",
  "patient_id": "uuid",
  "specimen_type": "Blood",
  "collection_method": "Venipuncture",
  "collected_at": "2024-11-24T10:30:00Z",
  "collected_by": "uuid"
}
```

### LabResult.Finalized
**Triggered When**: Lab result is finalized
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "result_id": "uuid",
  "order_id": "uuid",
  "patient_id": "uuid",
  "test_code": "CBC",
  "results": {
    "WBC": {"value": 7.5, "unit": "10^9/L", "reference_range": "4-11"},
    "RBC": {"value": 4.8, "unit": "10^12/L", "reference_range": "4.5-5.9"}
  },
  "finalized_by": "uuid",
  "finalized_at": "2024-11-24T14:00:00Z"
}
```

### LabResult.CriticalResult
**Triggered When**: Critical lab result detected
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "result_id": "uuid",
  "patient_id": "uuid",
  "test_code": "Potassium",
  "critical_value": 6.2,
  "reference_range": "3.5-5.0",
  "alert_severity": "critical",
  "notified_providers": ["uuid1", "uuid2"],
  "detected_at": "2024-11-24T14:00:00Z"
}
```

---

## Medication Events

### MedicationOrder.Created
**Triggered When**: Medication order is created
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "order_id": "uuid",
  "patient_id": "uuid",
  "encounter_id": "uuid",
  "medication": {
    "drug_code": "RXNORM:123456",
    "drug_name": "Lisinopril 10mg Tablet",
    "dosage": "10mg",
    "route": "Oral",
    "frequency": "Once daily",
    "duration": "30 days"
  },
  "ordered_by": "uuid",
  "ordered_at": "2024-11-24T10:00:00Z"
}
```

### Medication.Administered
**Triggered When**: Medication is administered
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "administration_id": "uuid",
  "order_id": "uuid",
  "patient_id": "uuid",
  "administered_dose": "10mg",
  "route": "Oral",
  "administered_by": "uuid",
  "administered_at": "2024-11-24T08:00:00Z",
  "administration_status": "completed"
}
```

---

## Imaging Events

### ImagingOrder.Created
**Triggered When**: Imaging order is placed
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "order_id": "uuid",
  "patient_id": "uuid",
  "encounter_id": "uuid",
  "modality": "CT",
  "body_part": "Chest",
  "clinical_indication": "Suspected pneumonia",
  "priority": "routine",
  "ordered_by": "uuid"
}
```

### ImagingStudy.Available
**Triggered When**: Imaging study is available
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "study_id": "uuid",
  "order_id": "uuid",
  "patient_id": "uuid",
  "modality": "CT",
  "study_description": "CT Chest with Contrast",
  "performed_at": "2024-11-24T11:00:00Z",
  "image_count": 150,
  "pacs_url": "https://pacs.example.com/study/123"
}
```

### RadiologyReport.Signed
**Triggered When**: Radiology report is signed
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "report_id": "uuid",
  "study_id": "uuid",
  "patient_id": "uuid",
  "findings": "No acute abnormality identified.",
  "impression": "Normal chest CT",
  "signed_by": "uuid",
  "signed_at": "2024-11-24T13:00:00Z"
}
```

---

## Revenue Cycle Management Events

### Coverage.Verified
**Triggered When**: Insurance coverage is verified
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "verification_id": "uuid",
  "patient_id": "uuid",
  "payer_id": "uuid",
  "policy_number": "POL123456",
  "coverage_status": "active",
  "coverage_start_date": "2024-01-01",
  "coverage_end_date": "2024-12-31",
  "verified_at": "2024-11-24T09:00:00Z"
}
```

### Claim.Submitted
**Triggered When**: Insurance claim is submitted
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "claim_id": "uuid",
  "patient_id": "uuid",
  "encounter_id": "uuid",
  "payer_id": "uuid",
  "total_charges": 5000.00,
  "submission_date": "2024-11-24",
  "claim_number": "CLM202411240001"
}
```

### Remittance.Received
**Triggered When**: Payment remittance is received
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "remittance_id": "uuid",
  "claim_id": "uuid",
  "payer_id": "uuid",
  "paid_amount": 4500.00,
  "adjustment_amount": 500.00,
  "received_date": "2024-12-10",
  "payment_method": "EFT"
}
```

---

## Operations Events

### OpsAlert.Triggered
**Triggered When**: Operational alert is triggered
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "alert_id": "uuid",
  "alert_type": "bed_capacity|wait_time|resource_shortage",
  "severity": "warning|critical",
  "message": "ED wait time exceeds 4 hours",
  "affected_unit": "Emergency Department",
  "triggered_at": "2024-11-24T10:00:00Z"
}
```

### BedSnapshot.Updated
**Triggered When**: Bed occupancy snapshot is updated
**Topic**: `healthtech.clinical.events`
**Payload**:
```json
{
  "snapshot_id": "uuid",
  "unit_id": "uuid",
  "unit_name": "ICU",
  "total_beds": 20,
  "occupied_beds": 18,
  "available_beds": 2,
  "occupancy_rate": 0.90,
  "snapshot_time": "2024-11-24T10:00:00Z"
}
```

---

## Event Schema Standard

All events follow this base schema:

```json
{
  "event_id": "uuid",
  "event_type": "Domain.Action",
  "event_version": "1.0",
  "event_time": "2024-11-24T10:00:00Z",
  "tenant_id": "hospital-uuid",
  "correlation_id": "request-uuid",
  "causation_id": "parent-event-uuid",
  "metadata": {
    "user_id": "user-uuid",
    "source": "prm-service",
    "ip_address": "10.0.0.1"
  },
  "data": {
    // Event-specific payload
  }
}
```

## Event Versioning

Events support versioning for schema evolution:

- **v1.0**: Initial version
- **v1.1**: Backward-compatible changes (added fields)
- **v2.0**: Breaking changes (removed/renamed fields)

### Version Migration Example

```python
def migrate_patient_created_v1_to_v2(event_v1):
    """Migrate Patient.Created from v1.0 to v2.0"""
    event_v2 = event_v1.copy()
    event_v2["event_version"] = "2.0"

    # v2.0 uses nested 'name' object
    event_v2["data"]["name"] = {
        "first": event_v1["data"]["first_name"],
        "last": event_v1["data"]["last_name"],
    }

    del event_v2["data"]["first_name"]
    del event_v2["data"]["last_name"]

    return event_v2
```

## Event Naming Conventions

1. **Domain First**: Events are grouped by domain (Patient, Appointment, etc.)
2. **Past Tense**: Events represent facts that have already occurred
3. **Specific**: Event names should be unambiguous
4. **Hierarchical**: Use dot notation for hierarchy

### Good Examples:
- `Patient.Created`
- `Appointment.CheckedIn`
- `LabResult.Finalized`

### Bad Examples:
- `CreatePatient` (not past tense)
- `Patient` (not specific enough)
- `PatientCreatedEvent` (redundant "Event" suffix)

## Testing Events

### Unit Test Example

```python
async def test_patient_created_event():
    """Test Patient.Created event publishing"""

    # Publish event
    event_id = await publish_event(
        event_type=EventType.PATIENT_CREATED,
        tenant_id=str(tenant_id),
        payload={
            "patient_id": str(patient.id),
            "name": "John Doe",
        },
    )

    # Verify event was published
    assert event_id is not None

    # Verify event in event store
    events = event_store.query_events(
        tenant_id=str(tenant_id),
        event_types=[EventType.PATIENT_CREATED],
    )

    assert len(events) > 0
    assert events[0].payload["patient_id"] == str(patient.id)
```

## Resources

- [Event-Driven Architecture Guide](./EVENT_DRIVEN_ARCHITECTURE_GUIDE.md)
- [Kafka Topics Documentation](./KAFKA_TOPICS.md)
- [Event Sourcing Patterns](./EVENT_SOURCING_PATTERNS.md)

---

**Maintained by**: Platform Team
**Contact**: platform-team@healthtech.com
