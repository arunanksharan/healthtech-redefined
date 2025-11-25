"""
Integration Service for RPM

Handles third-party device platform integrations (Withings, Apple Health, etc.)

EPIC-019: Remote Patient Monitoring
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
import httpx

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    RPMDevice, DeviceAssignment, DeviceReading, DeviceVendor,
    DeviceType, DeviceStatus, ReadingType
)
from ..schemas import (
    ReadingCreate, WithingsWebhookPayload,
    AppleHealthExportPayload, GoogleFitDataPayload
)

logger = logging.getLogger(__name__)


# Withings API mapping
WITHINGS_MEASURE_TYPES = {
    1: (ReadingType.BODY_WEIGHT, "kg"),
    4: (ReadingType.BODY_WEIGHT, "kg"),  # Height, we'll skip
    5: (ReadingType.BODY_WEIGHT, "kg"),  # Fat Free Mass
    6: (ReadingType.BODY_WEIGHT, "%"),   # Fat Ratio
    8: (ReadingType.BODY_WEIGHT, "kg"),  # Fat Mass Weight
    9: (ReadingType.BLOOD_PRESSURE_DIASTOLIC, "mmHg"),
    10: (ReadingType.BLOOD_PRESSURE_SYSTOLIC, "mmHg"),
    11: (ReadingType.HEART_RATE, "bpm"),
    54: (ReadingType.OXYGEN_SATURATION, "%"),
    71: (ReadingType.BODY_TEMPERATURE, "°C"),
}

# Apple Health type mapping
APPLE_HEALTH_TYPES = {
    "HKQuantityTypeIdentifierBloodPressureSystolic": (ReadingType.BLOOD_PRESSURE_SYSTOLIC, "mmHg"),
    "HKQuantityTypeIdentifierBloodPressureDiastolic": (ReadingType.BLOOD_PRESSURE_DIASTOLIC, "mmHg"),
    "HKQuantityTypeIdentifierHeartRate": (ReadingType.HEART_RATE, "bpm"),
    "HKQuantityTypeIdentifierBloodGlucose": (ReadingType.BLOOD_GLUCOSE, "mg/dL"),
    "HKQuantityTypeIdentifierOxygenSaturation": (ReadingType.OXYGEN_SATURATION, "%"),
    "HKQuantityTypeIdentifierBodyMass": (ReadingType.BODY_WEIGHT, "kg"),
    "HKQuantityTypeIdentifierBodyTemperature": (ReadingType.BODY_TEMPERATURE, "°C"),
    "HKQuantityTypeIdentifierRespiratoryRate": (ReadingType.RESPIRATORY_RATE, "breaths/min"),
    "HKQuantityTypeIdentifierStepCount": (ReadingType.STEPS, "count"),
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": (ReadingType.HRV, "ms"),
}

# Google Fit data source mapping
GOOGLE_FIT_TYPES = {
    "com.google.blood_pressure": {
        "systolic": (ReadingType.BLOOD_PRESSURE_SYSTOLIC, "mmHg"),
        "diastolic": (ReadingType.BLOOD_PRESSURE_DIASTOLIC, "mmHg"),
    },
    "com.google.heart_rate.bpm": (ReadingType.HEART_RATE, "bpm"),
    "com.google.blood_glucose": (ReadingType.BLOOD_GLUCOSE, "mmol/L"),
    "com.google.oxygen_saturation": (ReadingType.OXYGEN_SATURATION, "%"),
    "com.google.weight": (ReadingType.BODY_WEIGHT, "kg"),
    "com.google.body.temperature": (ReadingType.BODY_TEMPERATURE, "°C"),
    "com.google.step_count.delta": (ReadingType.STEPS, "count"),
}


class IntegrationService:
    """Service for third-party device integrations."""

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

    # =========================================================================
    # Withings Integration
    # =========================================================================

    async def handle_withings_webhook(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: WithingsWebhookPayload
    ) -> List[DeviceReading]:
        """Handle Withings webhook notification."""
        # Find device by Withings user ID
        device_result = await db.execute(
            select(RPMDevice).where(
                and_(
                    RPMDevice.tenant_id == tenant_id,
                    RPMDevice.vendor == DeviceVendor.WITHINGS,
                    RPMDevice.device_identifier == payload.userid
                )
            )
        )
        device = device_result.scalar_one_or_none()

        if not device:
            logger.warning(f"No device found for Withings user {payload.userid}")
            return []

        # Get patient from assignment
        assignment_result = await db.execute(
            select(DeviceAssignment).where(
                and_(
                    DeviceAssignment.device_id == device.id,
                    DeviceAssignment.is_active == True
                )
            )
        )
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            logger.warning(f"No active assignment for device {device.id}")
            return []

        # Fetch measurements from Withings API
        measurements = await self._fetch_withings_measurements(
            device, payload.startdate, payload.enddate
        )

        # Create readings
        readings = []
        for measure in measurements:
            reading_data = self._map_withings_measure(
                measure,
                assignment.patient_id,
                device.id,
                assignment.enrollment_id
            )
            if reading_data:
                reading = DeviceReading(
                    tenant_id=tenant_id,
                    **reading_data
                )
                db.add(reading)
                readings.append(reading)

        # Update device status
        device.last_sync_at = datetime.utcnow()
        device.status = DeviceStatus.ACTIVE

        await db.commit()
        logger.info(f"Processed {len(readings)} Withings readings for device {device.id}")
        return readings

    async def _fetch_withings_measurements(
        self,
        device: RPMDevice,
        startdate: int,
        enddate: int
    ) -> List[Dict[str, Any]]:
        """Fetch measurements from Withings API."""
        if not device.oauth_access_token:
            logger.error(f"No access token for device {device.id}")
            return []

        # Check token expiration
        if device.oauth_token_expires_at and device.oauth_token_expires_at < datetime.utcnow():
            # Would need to refresh token here
            logger.error(f"Token expired for device {device.id}")
            return []

        try:
            response = await self.http_client.post(
                "https://wbsapi.withings.net/measure",
                data={
                    "action": "getmeas",
                    "startdate": startdate,
                    "enddate": enddate,
                },
                headers={"Authorization": f"Bearer {device.oauth_access_token}"}
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != 0:
                logger.error(f"Withings API error: {data}")
                return []

            return data.get("body", {}).get("measuregrps", [])

        except Exception as e:
            logger.error(f"Failed to fetch Withings data: {e}")
            return []

    def _map_withings_measure(
        self,
        measure_group: Dict[str, Any],
        patient_id: UUID,
        device_id: UUID,
        enrollment_id: Optional[UUID]
    ) -> Optional[Dict[str, Any]]:
        """Map Withings measure to reading data."""
        measures = measure_group.get("measures", [])
        if not measures:
            return None

        measure = measures[0]
        measure_type = measure.get("type")

        if measure_type not in WITHINGS_MEASURE_TYPES:
            return None

        reading_type, unit = WITHINGS_MEASURE_TYPES[measure_type]
        value = measure.get("value", 0) * (10 ** measure.get("unit", 0))

        return {
            "patient_id": patient_id,
            "device_id": device_id,
            "enrollment_id": enrollment_id,
            "reading_type": reading_type,
            "value": value,
            "unit": unit,
            "measured_at": datetime.fromtimestamp(measure_group.get("date", 0)),
            "source": "withings",
            "raw_data": measure_group
        }

    # =========================================================================
    # Apple Health Integration
    # =========================================================================

    async def process_apple_health_export(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: AppleHealthExportPayload
    ) -> List[DeviceReading]:
        """Process Apple Health data export from mobile app."""
        # Find or create Apple Health "device" for this patient
        device_result = await db.execute(
            select(RPMDevice).where(
                and_(
                    RPMDevice.tenant_id == tenant_id,
                    RPMDevice.vendor == DeviceVendor.APPLE_HEALTH,
                    RPMDevice.device_identifier == str(payload.patient_id)
                )
            )
        )
        device = device_result.scalar_one_or_none()

        if not device:
            device = RPMDevice(
                tenant_id=tenant_id,
                device_identifier=str(payload.patient_id),
                vendor=DeviceVendor.APPLE_HEALTH,
                device_type=DeviceType.SMART_WATCH,
                status=DeviceStatus.ACTIVE
            )
            db.add(device)
            await db.flush()

        # Get active enrollment
        assignment_result = await db.execute(
            select(DeviceAssignment).where(
                and_(
                    DeviceAssignment.device_id == device.id,
                    DeviceAssignment.patient_id == payload.patient_id,
                    DeviceAssignment.is_active == True
                )
            )
        )
        assignment = assignment_result.scalar_one_or_none()
        enrollment_id = assignment.enrollment_id if assignment else None

        # Process records
        readings = []
        for record in payload.records:
            reading_data = self._map_apple_health_record(
                record,
                payload.patient_id,
                device.id,
                enrollment_id
            )
            if reading_data:
                reading = DeviceReading(
                    tenant_id=tenant_id,
                    **reading_data
                )
                db.add(reading)
                readings.append(reading)

        # Update device
        device.last_sync_at = datetime.utcnow()
        device.last_reading_at = datetime.utcnow()

        await db.commit()
        logger.info(f"Processed {len(readings)} Apple Health readings")
        return readings

    def _map_apple_health_record(
        self,
        record: Dict[str, Any],
        patient_id: UUID,
        device_id: UUID,
        enrollment_id: Optional[UUID]
    ) -> Optional[Dict[str, Any]]:
        """Map Apple Health record to reading data."""
        record_type = record.get("type")

        if record_type not in APPLE_HEALTH_TYPES:
            return None

        reading_type, unit = APPLE_HEALTH_TYPES[record_type]
        value = record.get("value", 0)

        # Handle unit conversions
        source_unit = record.get("unit", "")
        if reading_type == ReadingType.BLOOD_GLUCOSE and "mmol" in source_unit.lower():
            value = value * 18.0  # Convert mmol/L to mg/dL

        return {
            "patient_id": patient_id,
            "device_id": device_id,
            "enrollment_id": enrollment_id,
            "reading_type": reading_type,
            "value": value,
            "unit": unit,
            "measured_at": datetime.fromisoformat(record.get("startDate", "")),
            "source": "apple_health",
            "raw_data": record
        }

    # =========================================================================
    # Google Fit Integration
    # =========================================================================

    async def process_google_fit_data(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: GoogleFitDataPayload
    ) -> List[DeviceReading]:
        """Process Google Fit data."""
        # Find or create Google Fit "device"
        device_result = await db.execute(
            select(RPMDevice).where(
                and_(
                    RPMDevice.tenant_id == tenant_id,
                    RPMDevice.vendor == DeviceVendor.GOOGLE_FIT,
                    RPMDevice.device_identifier == str(payload.patient_id)
                )
            )
        )
        device = device_result.scalar_one_or_none()

        if not device:
            device = RPMDevice(
                tenant_id=tenant_id,
                device_identifier=str(payload.patient_id),
                vendor=DeviceVendor.GOOGLE_FIT,
                device_type=DeviceType.SMART_WATCH,
                status=DeviceStatus.ACTIVE
            )
            db.add(device)
            await db.flush()

        # Get enrollment
        assignment_result = await db.execute(
            select(DeviceAssignment).where(
                and_(
                    DeviceAssignment.device_id == device.id,
                    DeviceAssignment.patient_id == payload.patient_id,
                    DeviceAssignment.is_active == True
                )
            )
        )
        assignment = assignment_result.scalar_one_or_none()
        enrollment_id = assignment.enrollment_id if assignment else None

        # Process data points
        readings = []
        for point in payload.data_points:
            reading_data = self._map_google_fit_point(
                payload.data_source_id,
                point,
                payload.patient_id,
                device.id,
                enrollment_id
            )
            if reading_data:
                reading = DeviceReading(
                    tenant_id=tenant_id,
                    **reading_data
                )
                db.add(reading)
                readings.append(reading)

        device.last_sync_at = datetime.utcnow()
        device.last_reading_at = datetime.utcnow()

        await db.commit()
        logger.info(f"Processed {len(readings)} Google Fit readings")
        return readings

    def _map_google_fit_point(
        self,
        data_source_id: str,
        point: Dict[str, Any],
        patient_id: UUID,
        device_id: UUID,
        enrollment_id: Optional[UUID]
    ) -> Optional[Dict[str, Any]]:
        """Map Google Fit data point to reading."""
        # Extract data type from source ID
        data_type = None
        for known_type in GOOGLE_FIT_TYPES:
            if known_type in data_source_id:
                data_type = known_type
                break

        if not data_type:
            return None

        type_mapping = GOOGLE_FIT_TYPES[data_type]

        # Handle nested types (like blood pressure)
        if isinstance(type_mapping, dict):
            # Would need to extract multiple values
            return None

        reading_type, unit = type_mapping
        value = point.get("value", [{}])[0].get("fpVal", 0)

        # Parse timestamp
        start_time = point.get("startTimeNanos", 0)
        measured_at = datetime.fromtimestamp(start_time / 1e9)

        return {
            "patient_id": patient_id,
            "device_id": device_id,
            "enrollment_id": enrollment_id,
            "reading_type": reading_type,
            "value": value,
            "unit": unit,
            "measured_at": measured_at,
            "source": "google_fit",
            "raw_data": point
        }

    # =========================================================================
    # OAuth Flows
    # =========================================================================

    async def initiate_withings_oauth(
        self,
        tenant_id: UUID,
        redirect_uri: str,
        state: str
    ) -> str:
        """Generate Withings OAuth authorization URL."""
        # Would need Withings client ID from config
        client_id = "YOUR_WITHINGS_CLIENT_ID"
        scope = "user.metrics,user.activity"

        return (
            f"https://account.withings.com/oauth2_user/authorize2"
            f"?response_type=code"
            f"&client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scope}"
            f"&state={state}"
        )

    async def complete_withings_oauth(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        device_id: UUID,
        authorization_code: str,
        redirect_uri: str
    ) -> Optional[RPMDevice]:
        """Complete Withings OAuth flow."""
        # Exchange code for tokens
        client_id = "YOUR_WITHINGS_CLIENT_ID"
        client_secret = "YOUR_WITHINGS_CLIENT_SECRET"

        try:
            response = await self.http_client.post(
                "https://wbsapi.withings.net/v2/oauth2",
                data={
                    "action": "requesttoken",
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": authorization_code,
                    "redirect_uri": redirect_uri
                }
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != 0:
                logger.error(f"Withings OAuth error: {data}")
                return None

            body = data.get("body", {})
            access_token = body.get("access_token")
            refresh_token = body.get("refresh_token")
            expires_in = body.get("expires_in", 3600)
            user_id = body.get("userid")

            # Update device
            device_result = await db.execute(
                select(RPMDevice).where(
                    and_(
                        RPMDevice.id == device_id,
                        RPMDevice.tenant_id == tenant_id
                    )
                )
            )
            device = device_result.scalar_one_or_none()

            if device:
                device.oauth_access_token = access_token
                device.oauth_refresh_token = refresh_token
                device.oauth_token_expires_at = (
                    datetime.utcnow() + timedelta(seconds=expires_in)
                )
                device.device_identifier = str(user_id)
                device.status = DeviceStatus.ACTIVE
                await db.commit()
                await db.refresh(device)
                return device

        except Exception as e:
            logger.error(f"Failed to complete Withings OAuth: {e}")

        return None

    # =========================================================================
    # Sync Operations
    # =========================================================================

    async def sync_device(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        device_id: UUID
    ) -> Dict[str, Any]:
        """Trigger data sync for a device."""
        device_result = await db.execute(
            select(RPMDevice).where(
                and_(
                    RPMDevice.id == device_id,
                    RPMDevice.tenant_id == tenant_id
                )
            )
        )
        device = device_result.scalar_one_or_none()

        if not device:
            return {"success": False, "error": "Device not found"}

        if device.vendor == DeviceVendor.WITHINGS:
            # For Withings, we rely on webhooks
            # Could trigger a manual pull if needed
            return {"success": True, "message": "Withings uses webhooks"}

        elif device.vendor in [DeviceVendor.APPLE_HEALTH, DeviceVendor.GOOGLE_FIT]:
            # These require mobile app to push data
            return {"success": True, "message": "Requires mobile app sync"}

        return {"success": False, "error": f"Sync not supported for {device.vendor.value}"}

    async def get_integration_status(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID
    ) -> Dict[str, Any]:
        """Get integration status for all connected services."""
        # Get all devices for patient
        assignments_result = await db.execute(
            select(DeviceAssignment).where(
                and_(
                    DeviceAssignment.tenant_id == tenant_id,
                    DeviceAssignment.patient_id == patient_id,
                    DeviceAssignment.is_active == True
                )
            )
        )
        assignments = assignments_result.scalars().all()

        integrations = {}
        for assignment in assignments:
            device_result = await db.execute(
                select(RPMDevice).where(RPMDevice.id == assignment.device_id)
            )
            device = device_result.scalar_one_or_none()

            if device:
                integrations[device.vendor.value] = {
                    "device_id": str(device.id),
                    "status": device.status.value,
                    "last_sync": device.last_sync_at.isoformat() if device.last_sync_at else None,
                    "last_reading": device.last_reading_at.isoformat() if device.last_reading_at else None,
                    "connected": device.status == DeviceStatus.ACTIVE
                }

        return integrations
