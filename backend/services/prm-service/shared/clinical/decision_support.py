"""
Clinical Decision Support System

Comprehensive CDS including:
- Rule-based alerts and reminders
- Evidence-based guidelines
- Drug interaction checking
- Preventive care reminders
- Clinical quality measures
- Order sets and protocols

EPIC-006: US-006.9 Clinical Decision Support
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging
import re

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Severity level for clinical alerts."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    CONTRAINDICATION = "contraindication"


class AlertCategory(str, Enum):
    """Category of clinical alert."""
    DRUG_INTERACTION = "drug_interaction"
    DRUG_ALLERGY = "drug_allergy"
    DUPLICATE_THERAPY = "duplicate_therapy"
    DOSE_CHECK = "dose_check"
    LAB_ALERT = "lab_alert"
    PREVENTIVE_CARE = "preventive_care"
    QUALITY_MEASURE = "quality_measure"
    GUIDELINE = "guideline"
    ORDER_RECOMMENDATION = "order_recommendation"
    CONTRAINDICATION = "contraindication"


class AlertStatus(str, Enum):
    """Status of an alert."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    OVERRIDDEN = "overridden"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class RuleOperator(str, Enum):
    """Operators for rule conditions."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    BETWEEN = "between"
    DAYS_SINCE = "days_since"


@dataclass
class RuleCondition:
    """Single condition in a CDS rule."""
    field: str  # Path to field in patient context
    operator: RuleOperator
    value: Any
    value_end: Optional[Any] = None  # For BETWEEN operator


@dataclass
class ClinicalAlert:
    """Clinical decision support alert."""
    alert_id: str
    tenant_id: str
    patient_id: str

    # Alert details
    category: AlertCategory
    severity: AlertSeverity
    title: str
    message: str

    # Source
    rule_id: Optional[str] = None
    guideline_id: Optional[str] = None

    # Context
    encounter_id: Optional[str] = None
    order_id: Optional[str] = None
    medication_id: Optional[str] = None

    # Actions
    suggested_actions: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)

    # Status
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    override_reason: Optional[str] = None

    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


@dataclass
class ClinicalGuideline:
    """Evidence-based clinical guideline."""
    guideline_id: str
    tenant_id: str

    name: str
    description: str
    category: str  # diagnosis, treatment, screening, prevention

    # Applicability
    applicable_conditions: List[str] = field(default_factory=list)
    applicable_age_min: Optional[int] = None
    applicable_age_max: Optional[int] = None
    applicable_gender: Optional[str] = None

    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)

    # Evidence
    evidence_level: str = ""  # A, B, C, D
    source: str = ""
    source_url: Optional[str] = None
    last_reviewed: Optional[datetime] = None

    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CDSRule:
    """Clinical decision support rule."""
    rule_id: str
    tenant_id: str

    name: str
    description: str
    category: AlertCategory

    # Conditions (all must be met)
    conditions: List[RuleCondition] = field(default_factory=list)

    # Alert to generate
    alert_severity: AlertSeverity = AlertSeverity.WARNING
    alert_title_template: str = ""
    alert_message_template: str = ""

    # Actions to suggest
    suggested_actions: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    priority: int = 100  # Lower = higher priority
    is_active: bool = True
    requires_override_reason: bool = False

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PreventiveCareRecommendation:
    """Preventive care/screening recommendation."""
    recommendation_id: str
    tenant_id: str

    # Service details
    name: str
    description: str
    service_type: str  # screening, immunization, counseling, preventive_medication

    # CPT/procedure codes
    procedure_codes: List[str] = field(default_factory=list)

    # Eligibility
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    gender: Optional[str] = None
    risk_factors: List[str] = field(default_factory=list)
    excluded_conditions: List[str] = field(default_factory=list)

    # Frequency
    frequency_months: int = 12
    frequency_description: str = ""

    # Evidence
    uspstf_grade: Optional[str] = None  # A, B, C, D, I
    source: str = ""

    is_active: bool = True


@dataclass
class QualityMeasure:
    """Clinical quality measure definition."""
    measure_id: str
    tenant_id: str

    # Measure details
    name: str
    description: str
    cms_id: Optional[str] = None  # e.g., CMS165v10

    # Measure type
    measure_type: str = "process"  # process, outcome, structure

    # Population definitions
    initial_population_criteria: List[RuleCondition] = field(default_factory=list)
    denominator_criteria: List[RuleCondition] = field(default_factory=list)
    numerator_criteria: List[RuleCondition] = field(default_factory=list)
    exclusion_criteria: List[RuleCondition] = field(default_factory=list)

    # Measurement period
    measurement_period_months: int = 12

    is_active: bool = True


@dataclass
class PatientContext:
    """Patient context for CDS evaluation."""
    patient_id: str
    tenant_id: str

    # Demographics
    age: Optional[int] = None
    gender: Optional[str] = None
    race: Optional[str] = None
    ethnicity: Optional[str] = None

    # Clinical data
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    allergies: List[Dict[str, Any]] = field(default_factory=list)
    medications: List[Dict[str, Any]] = field(default_factory=list)
    lab_results: List[Dict[str, Any]] = field(default_factory=list)
    vitals: Dict[str, Any] = field(default_factory=dict)
    procedures: List[Dict[str, Any]] = field(default_factory=list)
    immunizations: List[Dict[str, Any]] = field(default_factory=list)

    # Risk scores
    risk_scores: Dict[str, float] = field(default_factory=dict)

    # Current encounter
    encounter_id: Optional[str] = None
    encounter_type: Optional[str] = None

    # Pending orders
    pending_orders: List[Dict[str, Any]] = field(default_factory=list)


class RuleEvaluator:
    """Evaluates CDS rule conditions against patient context."""

    def evaluate_condition(
        self,
        condition: RuleCondition,
        context: PatientContext,
    ) -> bool:
        """Evaluate a single condition."""
        # Get field value from context
        field_value = self._get_field_value(condition.field, context)

        # Apply operator
        op = condition.operator
        target = condition.value

        if op == RuleOperator.EQUALS:
            return field_value == target
        elif op == RuleOperator.NOT_EQUALS:
            return field_value != target
        elif op == RuleOperator.GREATER_THAN:
            return field_value is not None and field_value > target
        elif op == RuleOperator.LESS_THAN:
            return field_value is not None and field_value < target
        elif op == RuleOperator.GREATER_EQUAL:
            return field_value is not None and field_value >= target
        elif op == RuleOperator.LESS_EQUAL:
            return field_value is not None and field_value <= target
        elif op == RuleOperator.CONTAINS:
            return target in str(field_value) if field_value else False
        elif op == RuleOperator.IN:
            return field_value in target if isinstance(target, (list, tuple)) else False
        elif op == RuleOperator.NOT_IN:
            return field_value not in target if isinstance(target, (list, tuple)) else True
        elif op == RuleOperator.EXISTS:
            return field_value is not None
        elif op == RuleOperator.NOT_EXISTS:
            return field_value is None
        elif op == RuleOperator.BETWEEN:
            return (
                field_value is not None and
                target <= field_value <= condition.value_end
            )
        elif op == RuleOperator.DAYS_SINCE:
            if field_value is None:
                return False
            if isinstance(field_value, datetime):
                days = (datetime.now(timezone.utc) - field_value).days
                return days >= target
            return False

        return False

    def _get_field_value(
        self,
        field_path: str,
        context: PatientContext,
    ) -> Any:
        """Get a field value from context using dot notation path."""
        parts = field_path.split(".")
        value: Any = context

        for part in parts:
            if value is None:
                return None

            # Handle list indexing
            if "[" in part:
                name, idx_str = part.rstrip("]").split("[")
                value = getattr(value, name, None) if hasattr(value, name) else value.get(name)
                if value and isinstance(value, list):
                    idx = int(idx_str)
                    value = value[idx] if idx < len(value) else None
            elif hasattr(value, part):
                value = getattr(value, part)
            elif isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def evaluate_rule(
        self,
        rule: CDSRule,
        context: PatientContext,
    ) -> bool:
        """Evaluate all conditions in a rule (AND logic)."""
        for condition in rule.conditions:
            if not self.evaluate_condition(condition, context):
                return False
        return True


class ClinicalDecisionSupportService:
    """
    Clinical decision support service.

    Provides:
    - Rule-based alerting
    - Evidence-based guidelines
    - Preventive care recommendations
    - Quality measure tracking
    - Order recommendations
    """

    def __init__(self):
        self._rules: Dict[str, CDSRule] = {}
        self._guidelines: Dict[str, ClinicalGuideline] = {}
        self._preventive_care: Dict[str, PreventiveCareRecommendation] = {}
        self._quality_measures: Dict[str, QualityMeasure] = {}
        self._evaluator = RuleEvaluator()

        # Custom alert generators
        self._custom_generators: List[Callable[[PatientContext], List[ClinicalAlert]]] = []

    def register_rule(self, rule: CDSRule):
        """Register a CDS rule."""
        self._rules[rule.rule_id] = rule

    def register_guideline(self, guideline: ClinicalGuideline):
        """Register a clinical guideline."""
        self._guidelines[guideline.guideline_id] = guideline

    def register_preventive_care(self, recommendation: PreventiveCareRecommendation):
        """Register a preventive care recommendation."""
        self._preventive_care[recommendation.recommendation_id] = recommendation

    def register_quality_measure(self, measure: QualityMeasure):
        """Register a quality measure."""
        self._quality_measures[measure.measure_id] = measure

    def register_custom_generator(
        self,
        generator: Callable[[PatientContext], List[ClinicalAlert]],
    ):
        """Register a custom alert generator function."""
        self._custom_generators.append(generator)

    async def evaluate_all_rules(
        self,
        context: PatientContext,
    ) -> List[ClinicalAlert]:
        """Evaluate all applicable rules for a patient context."""
        alerts = []

        # Evaluate registered rules
        for rule in self._rules.values():
            if not rule.is_active:
                continue
            if rule.tenant_id != context.tenant_id:
                continue

            try:
                if self._evaluator.evaluate_rule(rule, context):
                    alert = self._create_alert_from_rule(rule, context)
                    alerts.append(alert)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {e}")

        # Run custom generators
        for generator in self._custom_generators:
            try:
                custom_alerts = generator(context)
                alerts.extend(custom_alerts)
            except Exception as e:
                logger.error(f"Error in custom alert generator: {e}")

        # Sort by severity and priority
        severity_order = {
            AlertSeverity.CONTRAINDICATION: 0,
            AlertSeverity.CRITICAL: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 3,
        }
        alerts.sort(key=lambda a: severity_order.get(a.severity, 99))

        return alerts

    def _create_alert_from_rule(
        self,
        rule: CDSRule,
        context: PatientContext,
    ) -> ClinicalAlert:
        """Create an alert from a triggered rule."""
        # Template substitution
        title = self._substitute_template(rule.alert_title_template, context)
        message = self._substitute_template(rule.alert_message_template, context)

        return ClinicalAlert(
            alert_id=str(uuid4()),
            tenant_id=context.tenant_id,
            patient_id=context.patient_id,
            category=rule.category,
            severity=rule.alert_severity,
            title=title or rule.name,
            message=message or rule.description,
            rule_id=rule.rule_id,
            encounter_id=context.encounter_id,
            suggested_actions=rule.suggested_actions.copy(),
        )

    def _substitute_template(
        self,
        template: str,
        context: PatientContext,
    ) -> str:
        """Substitute placeholders in template."""
        if not template:
            return ""

        # Simple placeholder substitution
        def replace(match):
            field = match.group(1)
            value = self._evaluator._get_field_value(field, context)
            return str(value) if value is not None else ""

        return re.sub(r'\{(\w+(?:\.\w+)*)\}', replace, template)

    async def get_preventive_care_recommendations(
        self,
        context: PatientContext,
    ) -> List[Dict[str, Any]]:
        """Get applicable preventive care recommendations."""
        recommendations = []

        for rec in self._preventive_care.values():
            if not rec.is_active:
                continue
            if rec.tenant_id != context.tenant_id:
                continue

            # Check eligibility
            if not self._check_preventive_care_eligibility(rec, context):
                continue

            # Check if due
            is_due, last_date = self._check_preventive_care_due(rec, context)

            recommendations.append({
                "recommendation": rec,
                "is_due": is_due,
                "last_performed": last_date,
                "next_due": self._calculate_next_due(rec, last_date),
            })

        return recommendations

    def _check_preventive_care_eligibility(
        self,
        rec: PreventiveCareRecommendation,
        context: PatientContext,
    ) -> bool:
        """Check if patient is eligible for preventive care."""
        # Age check
        if context.age is not None:
            if rec.age_min is not None and context.age < rec.age_min:
                return False
            if rec.age_max is not None and context.age > rec.age_max:
                return False

        # Gender check
        if rec.gender and context.gender and context.gender.lower() != rec.gender.lower():
            return False

        # Check exclusions
        if rec.excluded_conditions:
            patient_conditions = {c.get("code") for c in context.conditions}
            for excl in rec.excluded_conditions:
                if excl in patient_conditions:
                    return False

        return True

    def _check_preventive_care_due(
        self,
        rec: PreventiveCareRecommendation,
        context: PatientContext,
    ) -> tuple:
        """Check if preventive care is due."""
        # Find last procedure date
        last_date = None
        for proc in context.procedures:
            if proc.get("code") in rec.procedure_codes:
                proc_date = proc.get("date")
                if proc_date:
                    if isinstance(proc_date, str):
                        proc_date = datetime.fromisoformat(proc_date.replace('Z', '+00:00'))
                    if last_date is None or proc_date > last_date:
                        last_date = proc_date

        if last_date is None:
            return True, None

        # Check if interval has passed
        due_date = last_date + timedelta(days=rec.frequency_months * 30)
        is_due = datetime.now(timezone.utc) >= due_date

        return is_due, last_date

    def _calculate_next_due(
        self,
        rec: PreventiveCareRecommendation,
        last_date: Optional[datetime],
    ) -> Optional[datetime]:
        """Calculate next due date."""
        if last_date is None:
            return datetime.now(timezone.utc)
        return last_date + timedelta(days=rec.frequency_months * 30)

    async def evaluate_quality_measure(
        self,
        measure: QualityMeasure,
        patients: List[PatientContext],
    ) -> Dict[str, Any]:
        """Evaluate a quality measure across a patient population."""
        initial_pop = []
        denominator = []
        numerator = []
        exclusions = []

        for context in patients:
            # Check initial population
            in_initial = all(
                self._evaluator.evaluate_condition(c, context)
                for c in measure.initial_population_criteria
            )
            if not in_initial:
                continue
            initial_pop.append(context.patient_id)

            # Check exclusions
            is_excluded = any(
                self._evaluator.evaluate_condition(c, context)
                for c in measure.exclusion_criteria
            ) if measure.exclusion_criteria else False

            if is_excluded:
                exclusions.append(context.patient_id)
                continue

            # Check denominator
            in_denom = all(
                self._evaluator.evaluate_condition(c, context)
                for c in measure.denominator_criteria
            ) if measure.denominator_criteria else True

            if not in_denom:
                continue
            denominator.append(context.patient_id)

            # Check numerator
            in_num = all(
                self._evaluator.evaluate_condition(c, context)
                for c in measure.numerator_criteria
            )
            if in_num:
                numerator.append(context.patient_id)

        # Calculate performance rate
        performance_rate = (
            len(numerator) / len(denominator) * 100
            if denominator else 0
        )

        return {
            "measure_id": measure.measure_id,
            "measure_name": measure.name,
            "initial_population": len(initial_pop),
            "denominator": len(denominator),
            "numerator": len(numerator),
            "exclusions": len(exclusions),
            "performance_rate": round(performance_rate, 2),
            "denominator_patients": denominator,
            "numerator_patients": numerator,
            "gap_patients": list(set(denominator) - set(numerator)),
        }

    async def acknowledge_alert(
        self,
        alert: ClinicalAlert,
        user_id: str,
    ) -> ClinicalAlert:
        """Acknowledge an alert."""
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        return alert

    async def override_alert(
        self,
        alert: ClinicalAlert,
        user_id: str,
        reason: str,
    ) -> ClinicalAlert:
        """Override an alert with a reason."""
        alert.status = AlertStatus.OVERRIDDEN
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.override_reason = reason

        logger.warning(
            f"Alert {alert.alert_id} overridden by {user_id}: {reason}"
        )
        return alert

    async def get_applicable_guidelines(
        self,
        context: PatientContext,
    ) -> List[ClinicalGuideline]:
        """Get applicable clinical guidelines for patient."""
        applicable = []

        for guideline in self._guidelines.values():
            if not guideline.is_active:
                continue
            if guideline.tenant_id != context.tenant_id:
                continue

            # Check conditions match
            if guideline.applicable_conditions:
                patient_conditions = {c.get("code") for c in context.conditions}
                if not any(c in patient_conditions for c in guideline.applicable_conditions):
                    continue

            # Check age
            if context.age is not None:
                if guideline.applicable_age_min and context.age < guideline.applicable_age_min:
                    continue
                if guideline.applicable_age_max and context.age > guideline.applicable_age_max:
                    continue

            # Check gender
            if guideline.applicable_gender and context.gender:
                if context.gender.lower() != guideline.applicable_gender.lower():
                    continue

            applicable.append(guideline)

        return applicable

    async def create_rule(
        self,
        tenant_id: str,
        name: str,
        category: AlertCategory,
        conditions: List[Dict[str, Any]],
        alert_severity: AlertSeverity = AlertSeverity.WARNING,
        alert_title: str = "",
        alert_message: str = "",
        description: str = "",
        suggested_actions: Optional[List[Dict[str, Any]]] = None,
    ) -> CDSRule:
        """Create a new CDS rule."""
        rule_conditions = [
            RuleCondition(
                field=c["field"],
                operator=RuleOperator(c["operator"]),
                value=c["value"],
                value_end=c.get("value_end"),
            )
            for c in conditions
        ]

        rule = CDSRule(
            rule_id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            description=description,
            category=category,
            conditions=rule_conditions,
            alert_severity=alert_severity,
            alert_title_template=alert_title,
            alert_message_template=alert_message,
            suggested_actions=suggested_actions or [],
        )

        self.register_rule(rule)
        logger.info(f"Created CDS rule: {rule.rule_id} - {name}")

        return rule
