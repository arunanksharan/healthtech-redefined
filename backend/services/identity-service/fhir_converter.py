"""
FHIR R4 Conversion Utilities
Convert database models to FHIR resources and vice versa
"""
from datetime import date, datetime
from typing import Dict, Any, Optional


def to_fhir_patient(patient) -> Dict[str, Any]:
    """
    Convert Patient database model to FHIR R4 Patient resource

    Args:
        patient: Patient SQLAlchemy model instance

    Returns:
        dict: FHIR R4 Patient resource
    """
    fhir_patient = {
        "resourceType": "Patient",
        "id": str(patient.id),
        "meta": {
            "versionId": "1",
            "lastUpdated": patient.updated_at.isoformat() if patient.updated_at else datetime.utcnow().isoformat(),
        },
        "active": not patient.is_deceased,
    }

    # Name
    if patient.first_name or patient.last_name:
        name_parts = []
        if patient.first_name:
            name_parts.append(patient.first_name)
        if patient.middle_name:
            name_parts.append(patient.middle_name)

        fhir_patient["name"] = [{
            "use": "official",
            "family": patient.last_name,
            "given": name_parts,
            "text": f"{patient.first_name} {patient.middle_name or ''} {patient.last_name}".strip()
        }]

    # Telecom (phone and email)
    telecom = []
    if patient.phone_primary:
        telecom.append({
            "system": "phone",
            "value": patient.phone_primary,
            "use": "mobile",
            "rank": 1
        })
    if patient.phone_secondary:
        telecom.append({
            "system": "phone",
            "value": patient.phone_secondary,
            "use": "mobile",
            "rank": 2
        })
    if patient.email_primary:
        telecom.append({
            "system": "email",
            "value": patient.email_primary,
            "use": "home",
            "rank": 1
        })
    if patient.email_secondary:
        telecom.append({
            "system": "email",
            "value": patient.email_secondary,
            "use": "work",
            "rank": 2
        })
    if telecom:
        fhir_patient["telecom"] = telecom

    # Gender
    if patient.gender:
        # Map our gender values to FHIR codes
        gender_map = {
            "male": "male",
            "female": "female",
            "other": "other",
            "unknown": "unknown"
        }
        fhir_patient["gender"] = gender_map.get(patient.gender, "unknown")

    # Birth date
    if patient.date_of_birth:
        fhir_patient["birthDate"] = patient.date_of_birth.isoformat()

    # Deceased
    if patient.is_deceased:
        if patient.deceased_date:
            fhir_patient["deceasedDateTime"] = patient.deceased_date.isoformat()
        else:
            fhir_patient["deceasedBoolean"] = True

    # Address
    if patient.address_line1 or patient.city:
        address_lines = []
        if patient.address_line1:
            address_lines.append(patient.address_line1)
        if patient.address_line2:
            address_lines.append(patient.address_line2)

        fhir_patient["address"] = [{
            "use": "home",
            "type": "physical",
            "line": address_lines,
            "city": patient.city,
            "state": patient.state,
            "postalCode": patient.postal_code,
            "country": patient.country or "India"
        }]

    # Marital status
    if patient.marital_status:
        marital_status_map = {
            "single": "S",
            "married": "M",
            "divorced": "D",
            "widowed": "W",
            "unknown": "UNK"
        }
        code = marital_status_map.get(patient.marital_status.lower(), "UNK")
        fhir_patient["maritalStatus"] = {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                "code": code,
                "display": patient.marital_status
            }]
        }

    # Extensions for additional fields
    extensions = []

    if patient.blood_group:
        extensions.append({
            "url": "http://healthtech.com/fhir/StructureDefinition/blood-group",
            "valueString": patient.blood_group
        })

    if patient.language_preferred:
        extensions.append({
            "url": "http://healthtech.com/fhir/StructureDefinition/preferred-language",
            "valueCode": patient.language_preferred
        })

    if extensions:
        fhir_patient["extension"] = extensions

    # Communication (preferred language)
    if patient.language_preferred:
        fhir_patient["communication"] = [{
            "language": {
                "coding": [{
                    "system": "urn:ietf:bcp:47",
                    "code": patient.language_preferred
                }]
            },
            "preferred": True
        }]

    return fhir_patient


def to_fhir_practitioner(practitioner) -> Dict[str, Any]:
    """
    Convert Practitioner database model to FHIR R4 Practitioner resource

    Args:
        practitioner: Practitioner SQLAlchemy model instance

    Returns:
        dict: FHIR R4 Practitioner resource
    """
    fhir_practitioner = {
        "resourceType": "Practitioner",
        "id": str(practitioner.id),
        "meta": {
            "versionId": "1",
            "lastUpdated": practitioner.updated_at.isoformat() if practitioner.updated_at else datetime.utcnow().isoformat(),
        },
        "active": practitioner.is_active,
    }

    # Name
    name_parts = []
    if practitioner.first_name:
        name_parts.append(practitioner.first_name)
    if practitioner.middle_name:
        name_parts.append(practitioner.middle_name)

    fhir_practitioner["name"] = [{
        "use": "official",
        "family": practitioner.last_name,
        "given": name_parts,
        "prefix": ["Dr."] if practitioner.qualification else [],
        "text": f"Dr. {practitioner.first_name} {practitioner.last_name}"
    }]

    # Telecom
    telecom = []
    if practitioner.phone_primary:
        telecom.append({
            "system": "phone",
            "value": practitioner.phone_primary,
            "use": "work"
        })
    if practitioner.email_primary:
        telecom.append({
            "system": "email",
            "value": practitioner.email_primary,
            "use": "work"
        })
    if telecom:
        fhir_practitioner["telecom"] = telecom

    # Gender
    if practitioner.gender:
        gender_map = {
            "male": "male",
            "female": "female",
            "other": "other",
            "unknown": "unknown"
        }
        fhir_practitioner["gender"] = gender_map.get(practitioner.gender, "unknown")

    # Qualifications
    qualifications = []

    if practitioner.qualification:
        qualifications.append({
            "code": {
                "coding": [{
                    "system": "http://healthtech.com/fhir/CodeSystem/qualifications",
                    "code": "MD",
                    "display": practitioner.qualification
                }]
            }
        })

    if practitioner.license_number:
        qualifications.append({
            "identifier": [{
                "system": "http://healthtech.com/fhir/license-number",
                "value": practitioner.license_number
            }],
            "code": {
                "text": "Medical License"
            }
        })

    if qualifications:
        fhir_practitioner["qualification"] = qualifications

    # Specialties (using extensions)
    if practitioner.speciality or practitioner.sub_speciality:
        extensions = []

        if practitioner.speciality:
            extensions.append({
                "url": "http://healthtech.com/fhir/StructureDefinition/specialty",
                "valueString": practitioner.speciality
            })

        if practitioner.sub_speciality:
            extensions.append({
                "url": "http://healthtech.com/fhir/StructureDefinition/sub-specialty",
                "valueString": practitioner.sub_speciality
            })

        fhir_practitioner["extension"] = extensions

    return fhir_practitioner


def from_fhir_patient(fhir_patient: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert FHIR R4 Patient resource to database model fields

    Args:
        fhir_patient: FHIR R4 Patient resource dict

    Returns:
        dict: Fields for Patient model
    """
    patient_data = {}

    # Name
    if "name" in fhir_patient and fhir_patient["name"]:
        name = fhir_patient["name"][0]
        patient_data["last_name"] = name.get("family", "")
        if "given" in name and name["given"]:
            patient_data["first_name"] = name["given"][0]
            if len(name["given"]) > 1:
                patient_data["middle_name"] = " ".join(name["given"][1:])

    # Gender
    if "gender" in fhir_patient:
        patient_data["gender"] = fhir_patient["gender"]

    # Birth date
    if "birthDate" in fhir_patient:
        patient_data["date_of_birth"] = fhir_patient["birthDate"]

    # Telecom
    if "telecom" in fhir_patient:
        phones = [t for t in fhir_patient["telecom"] if t.get("system") == "phone"]
        emails = [t for t in fhir_patient["telecom"] if t.get("system") == "email"]

        if phones:
            patient_data["phone_primary"] = phones[0].get("value")
            if len(phones) > 1:
                patient_data["phone_secondary"] = phones[1].get("value")

        if emails:
            patient_data["email_primary"] = emails[0].get("value")
            if len(emails) > 1:
                patient_data["email_secondary"] = emails[1].get("value")

    # Address
    if "address" in fhir_patient and fhir_patient["address"]:
        address = fhir_patient["address"][0]
        if "line" in address and address["line"]:
            patient_data["address_line1"] = address["line"][0]
            if len(address["line"]) > 1:
                patient_data["address_line2"] = address["line"][1]
        patient_data["city"] = address.get("city")
        patient_data["state"] = address.get("state")
        patient_data["postal_code"] = address.get("postalCode")
        patient_data["country"] = address.get("country", "India")

    # Deceased
    if "deceasedBoolean" in fhir_patient:
        patient_data["is_deceased"] = fhir_patient["deceasedBoolean"]
    if "deceasedDateTime" in fhir_patient:
        patient_data["is_deceased"] = True
        patient_data["deceased_date"] = fhir_patient["deceasedDateTime"]

    return patient_data


def to_fhir_organization(organization) -> Dict[str, Any]:
    """Convert Organization model to FHIR R4 Organization resource"""
    return {
        "resourceType": "Organization",
        "id": str(organization.id),
        "active": organization.is_active,
        "name": organization.name,
        "type": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                "code": organization.type or "prov",
                "display": organization.type or "Healthcare Provider"
            }]
        }] if organization.type else None,
    }


def to_fhir_location(location) -> Dict[str, Any]:
    """Convert Location model to FHIR R4 Location resource"""
    return {
        "resourceType": "Location",
        "id": str(location.id),
        "status": location.operational_status or "active",
        "name": location.name,
        "mode": "instance",
        "type": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                "code": location.type or "HOSP",
                "display": location.type or "Hospital"
            }]
        }] if location.type else None,
    }
