"""
Laboratory Order Management

Comprehensive lab order system with:
- Lab compendium integration (LOINC)
- Order sets
- Specimen requirements
- Results management
- Critical value alerts
- Trending and visualization

EPIC-006: US-006.2 Laboratory Order Management
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class LabOrderStatus(str, Enum):
    """Lab order status."""
    DRAFT = "draft"
    PENDING = "pending"
    ORDERED = "ordered"
    SPECIMEN_COLLECTED = "specimen_collected"
    RECEIVED_BY_LAB = "received_by_lab"
    IN_PROGRESS = "in_progress"
    RESULTED = "resulted"
    FINAL = "final"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class ResultStatus(str, Enum):
    """Result status."""
    PRELIMINARY = "preliminary"
    FINAL = "final"
    CORRECTED = "corrected"
    AMENDED = "amended"
    CANCELLED = "cancelled"


class InterpretationFlag(str, Enum):
    """Result interpretation flags."""
    NORMAL = "N"
    LOW = "L"
    HIGH = "H"
    CRITICAL_LOW = "LL"
    CRITICAL_HIGH = "HH"
    ABNORMAL = "A"
    RESISTANT = "R"
    SUSCEPTIBLE = "S"
    INTERMEDIATE = "I"


class SpecimenType(str, Enum):
    """Specimen types."""
    BLOOD = "blood"
    SERUM = "serum"
    PLASMA = "plasma"
    URINE = "urine"
    STOOL = "stool"
    CSF = "csf"
    SWAB = "swab"
    TISSUE = "tissue"
    SPUTUM = "sputum"
    OTHER = "other"


class OrderPriority(str, Enum):
    """Order priority levels."""
    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"
    ASAP = "asap"
    TIMED = "timed"


@dataclass
class LabTest:
    """Lab test definition from compendium."""
    test_id: str
    loinc_code: str
    cpt_code: Optional[str] = None
    name: str = ""
    description: str = ""
    category: str = ""
    specimen_type: SpecimenType = SpecimenType.BLOOD
    specimen_volume_ml: Optional[float] = None
    specimen_container: str = ""
    fasting_required: bool = False
    special_instructions: str = ""
    turnaround_hours: int = 24
    reference_range: Optional[str] = None
    units: str = ""
    method: str = ""
    is_panel: bool = False
    panel_components: List[str] = field(default_factory=list)


@dataclass
class ReferenceRange:
    """Reference range for a lab test."""
    low: Optional[float] = None
    high: Optional[float] = None
    low_critical: Optional[float] = None
    high_critical: Optional[float] = None
    text: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    gender: Optional[str] = None  # M, F, or None for both


@dataclass
class LabResult:
    """Single lab result value."""
    result_id: str
    order_id: str
    test_id: str
    loinc_code: str
    test_name: str

    # Result value
    value: Optional[str] = None
    value_numeric: Optional[float] = None
    units: str = ""

    # Interpretation
    reference_range: Optional[ReferenceRange] = None
    interpretation: InterpretationFlag = InterpretationFlag.NORMAL
    is_critical: bool = False

    # Status
    status: ResultStatus = ResultStatus.PRELIMINARY
    resulted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resulted_by: Optional[str] = None

    # Notes
    notes: Optional[str] = None
    method: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resultId": self.result_id,
            "orderId": self.order_id,
            "testName": self.test_name,
            "value": self.value,
            "valueNumeric": self.value_numeric,
            "units": self.units,
            "interpretation": self.interpretation.value,
            "isCritical": self.is_critical,
            "status": self.status.value,
            "resultedAt": self.resulted_at.isoformat(),
        }


@dataclass
class Specimen:
    """Specimen information."""
    specimen_id: str
    order_id: str
    specimen_type: SpecimenType
    collection_time: Optional[datetime] = None
    collected_by: Optional[str] = None
    container_id: Optional[str] = None
    accession_number: Optional[str] = None
    received_time: Optional[datetime] = None
    condition: str = "acceptable"  # acceptable, hemolyzed, lipemic, etc.
    notes: Optional[str] = None


@dataclass
class LabOrder:
    """Laboratory order."""
    order_id: str
    tenant_id: str
    patient_id: str
    ordering_provider_id: str
    encounter_id: Optional[str] = None

    # Tests
    tests: List[LabTest] = field(default_factory=list)
    test_ids: List[str] = field(default_factory=list)

    # Priority and timing
    priority: OrderPriority = OrderPriority.ROUTINE
    scheduled_date: Optional[datetime] = None

    # Diagnosis
    diagnosis_codes: List[str] = field(default_factory=list)  # ICD-10
    clinical_indication: str = ""

    # Collection
    specimen: Optional[Specimen] = None
    collection_site: str = ""
    fasting_status: Optional[bool] = None

    # Lab routing
    performing_lab_id: Optional[str] = None
    performing_lab_name: Optional[str] = None

    # Results
    results: List[LabResult] = field(default_factory=list)
    has_critical_results: bool = False

    # Status
    status: LabOrderStatus = LabOrderStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ordered_at: Optional[datetime] = None
    resulted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

    # Notes
    notes: Optional[str] = None
    internal_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "orderId": self.order_id,
            "patientId": self.patient_id,
            "orderingProviderId": self.ordering_provider_id,
            "tests": [t.name for t in self.tests],
            "priority": self.priority.value,
            "status": self.status.value,
            "hasCriticalResults": self.has_critical_results,
            "createdAt": self.created_at.isoformat(),
        }


@dataclass
class OrderSet:
    """Pre-defined order set for common scenarios."""
    order_set_id: str
    name: str
    description: str
    category: str  # admission, routine, disease-specific
    tests: List[LabTest] = field(default_factory=list)
    diagnosis_codes: List[str] = field(default_factory=list)
    is_active: bool = True


class LabCatalog:
    """
    Laboratory test catalog service.

    Manages test definitions, order sets, and reference data.
    """

    def __init__(self):
        self._tests: Dict[str, LabTest] = {}
        self._order_sets: Dict[str, OrderSet] = {}

    async def search_tests(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> List[LabTest]:
        """Search for lab tests."""
        results = []
        query_lower = query.lower()

        for test in self._tests.values():
            if query_lower in test.name.lower() or query_lower in test.loinc_code:
                if category is None or test.category == category:
                    results.append(test)
                    if len(results) >= limit:
                        break

        return results

    async def get_test(self, test_id: str) -> Optional[LabTest]:
        """Get test by ID."""
        return self._tests.get(test_id)

    async def get_test_by_loinc(self, loinc_code: str) -> Optional[LabTest]:
        """Get test by LOINC code."""
        for test in self._tests.values():
            if test.loinc_code == loinc_code:
                return test
        return None

    async def get_order_sets(
        self,
        category: Optional[str] = None,
    ) -> List[OrderSet]:
        """Get available order sets."""
        sets = list(self._order_sets.values())
        if category:
            sets = [s for s in sets if s.category == category]
        return [s for s in sets if s.is_active]

    async def get_order_set(self, order_set_id: str) -> Optional[OrderSet]:
        """Get order set by ID."""
        return self._order_sets.get(order_set_id)

    async def get_reference_ranges(
        self,
        test_id: str,
        patient_age: Optional[int] = None,
        patient_gender: Optional[str] = None,
    ) -> Optional[ReferenceRange]:
        """Get reference ranges for a test based on patient demographics."""
        # Would look up from database
        return None


class LabOrderService:
    """
    Main laboratory order management service.

    Handles:
    - Order creation and submission
    - Specimen tracking
    - Results processing
    - Critical value notifications
    - Order history and trending
    """

    def __init__(self, lab_catalog: Optional[LabCatalog] = None):
        self.catalog = lab_catalog or LabCatalog()

    async def create_order(
        self,
        tenant_id: str,
        patient_id: str,
        ordering_provider_id: str,
        test_ids: List[str],
        priority: OrderPriority = OrderPriority.ROUTINE,
        diagnosis_codes: Optional[List[str]] = None,
        clinical_indication: str = "",
        encounter_id: Optional[str] = None,
        scheduled_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> LabOrder:
        """
        Create a new lab order.

        Args:
            tenant_id: Tenant ID
            patient_id: Patient ID
            ordering_provider_id: Ordering provider ID
            test_ids: List of test IDs to order
            priority: Order priority
            diagnosis_codes: ICD-10 codes
            clinical_indication: Clinical reason for order
            encounter_id: Associated encounter
            scheduled_date: When to collect specimen
            notes: Additional notes

        Returns:
            Created LabOrder
        """
        # Get test details
        tests = []
        for test_id in test_ids:
            test = await self.catalog.get_test(test_id)
            if test:
                tests.append(test)

        order = LabOrder(
            order_id=str(uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            ordering_provider_id=ordering_provider_id,
            encounter_id=encounter_id,
            tests=tests,
            test_ids=test_ids,
            priority=priority,
            scheduled_date=scheduled_date,
            diagnosis_codes=diagnosis_codes or [],
            clinical_indication=clinical_indication,
            notes=notes,
        )

        # Check for duplicate orders
        duplicates = await self._check_duplicate_orders(
            patient_id, test_ids
        )
        if duplicates:
            order.internal_notes = f"Duplicate check: {len(duplicates)} similar orders in past 24h"

        logger.info(f"Created lab order: {order.order_id}")
        return order

    async def create_from_order_set(
        self,
        tenant_id: str,
        patient_id: str,
        ordering_provider_id: str,
        order_set_id: str,
        encounter_id: Optional[str] = None,
        **kwargs,
    ) -> LabOrder:
        """Create an order from a predefined order set."""
        order_set = await self.catalog.get_order_set(order_set_id)
        if not order_set:
            raise ValueError(f"Order set not found: {order_set_id}")

        return await self.create_order(
            tenant_id=tenant_id,
            patient_id=patient_id,
            ordering_provider_id=ordering_provider_id,
            test_ids=[t.test_id for t in order_set.tests],
            diagnosis_codes=order_set.diagnosis_codes,
            encounter_id=encounter_id,
            **kwargs,
        )

    async def submit_order(self, order: LabOrder) -> LabOrder:
        """
        Submit order to lab system.

        Transmits order via HL7 ORM message.
        """
        if order.status not in [LabOrderStatus.DRAFT, LabOrderStatus.PENDING]:
            raise ValueError(f"Cannot submit order in status: {order.status}")

        # Validate order
        validation = await self._validate_order(order)
        if not validation["valid"]:
            raise ValueError(f"Order validation failed: {validation['errors']}")

        # Would send HL7 ORM message to lab system
        order.status = LabOrderStatus.ORDERED
        order.ordered_at = datetime.now(timezone.utc)

        logger.info(f"Order submitted: {order.order_id}")
        return order

    async def _validate_order(self, order: LabOrder) -> Dict[str, Any]:
        """Validate an order before submission."""
        errors = []

        if not order.tests:
            errors.append("No tests specified")

        if not order.diagnosis_codes:
            errors.append("Diagnosis code required for billing")

        # Check fasting requirements
        fasting_required = any(t.fasting_required for t in order.tests)
        if fasting_required and order.fasting_status is None:
            errors.append("Fasting status required for ordered tests")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    async def _check_duplicate_orders(
        self,
        patient_id: str,
        test_ids: List[str],
        hours: int = 24,
    ) -> List[LabOrder]:
        """Check for duplicate orders within time window."""
        # Would query database for recent orders
        return []

    async def record_specimen_collection(
        self,
        order: LabOrder,
        collected_by: str,
        collection_time: Optional[datetime] = None,
        container_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> LabOrder:
        """Record specimen collection."""
        specimen = Specimen(
            specimen_id=str(uuid4()),
            order_id=order.order_id,
            specimen_type=order.tests[0].specimen_type if order.tests else SpecimenType.BLOOD,
            collection_time=collection_time or datetime.now(timezone.utc),
            collected_by=collected_by,
            container_id=container_id,
            notes=notes,
        )

        order.specimen = specimen
        order.status = LabOrderStatus.SPECIMEN_COLLECTED

        logger.info(f"Specimen collected for order: {order.order_id}")
        return order

    async def process_results(
        self,
        order: LabOrder,
        results: List[LabResult],
    ) -> Tuple[LabOrder, List[Dict[str, Any]]]:
        """
        Process incoming lab results.

        Args:
            order: The lab order
            results: List of results from lab

        Returns:
            Updated order and list of critical alerts
        """
        alerts = []

        for result in results:
            # Check for critical values
            if result.interpretation in [InterpretationFlag.CRITICAL_LOW, InterpretationFlag.CRITICAL_HIGH]:
                result.is_critical = True
                order.has_critical_results = True

                alerts.append({
                    "type": "critical_value",
                    "testName": result.test_name,
                    "value": result.value,
                    "interpretation": result.interpretation.value,
                    "orderId": order.order_id,
                    "patientId": order.patient_id,
                })

            order.results.append(result)

        # Update order status
        all_final = all(r.status == ResultStatus.FINAL for r in order.results)
        if all_final:
            order.status = LabOrderStatus.FINAL
        else:
            order.status = LabOrderStatus.RESULTED

        order.resulted_at = datetime.now(timezone.utc)

        logger.info(f"Results processed for order: {order.order_id}, critical alerts: {len(alerts)}")
        return order, alerts

    async def acknowledge_results(
        self,
        order: LabOrder,
        reviewed_by: str,
        notes: Optional[str] = None,
    ) -> LabOrder:
        """Mark results as reviewed."""
        order.reviewed_at = datetime.now(timezone.utc)
        order.reviewed_by = reviewed_by

        if notes:
            order.notes = f"{order.notes or ''}\nReview: {notes}"

        logger.info(f"Results reviewed for order: {order.order_id}")
        return order

    async def cancel_order(
        self,
        order: LabOrder,
        reason: str,
        cancelled_by: str,
    ) -> LabOrder:
        """Cancel a lab order."""
        if order.status in [LabOrderStatus.RESULTED, LabOrderStatus.FINAL]:
            raise ValueError("Cannot cancel order with results")

        order.status = LabOrderStatus.CANCELLED
        order.notes = f"{order.notes or ''}\nCancelled: {reason}"

        # Would send HL7 ORM cancel message if already submitted
        logger.info(f"Order cancelled: {order.order_id}")
        return order

    async def get_patient_results(
        self,
        tenant_id: str,
        patient_id: str,
        test_loinc: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[LabResult]:
        """Get lab results for a patient."""
        # Would query database
        return []

    async def get_result_trend(
        self,
        tenant_id: str,
        patient_id: str,
        test_loinc: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get trending data for a specific test."""
        # Would query database and return time series
        return []
