"""
Population Health Management Service - EPIC-011: US-011.3
Identifies and stratifies patient populations by risk for targeted interventions.

Features:
- Predictive risk scoring algorithms
- Chronic disease registries
- Social determinants of health integration
- Care gap identification
- Preventive care tracking
- Medication adherence monitoring
- Intervention management and ROI analysis
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
import random


class RiskLevel(Enum):
    """Patient risk stratification levels."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class CareGapPriority(Enum):
    """Priority levels for care gaps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InterventionStatus(Enum):
    """Status of patient interventions."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DECLINED = "declined"
    NO_RESPONSE = "no_response"


class ChronicCondition(Enum):
    """Chronic disease categories."""
    DIABETES = "diabetes"
    HYPERTENSION = "hypertension"
    HEART_FAILURE = "heart_failure"
    COPD = "copd"
    ASTHMA = "asthma"
    CKD = "chronic_kidney_disease"
    DEPRESSION = "depression"
    OBESITY = "obesity"
    CAD = "coronary_artery_disease"
    CANCER = "cancer"


@dataclass
class RiskScore:
    """Patient risk score details."""
    overall_score: float
    risk_level: RiskLevel
    percentile: int
    components: Dict[str, float] = field(default_factory=dict)
    contributing_factors: List[str] = field(default_factory=list)
    predicted_costs: float = 0.0
    predicted_utilization: Dict[str, float] = field(default_factory=dict)
    model_version: str = "1.0"
    calculated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PatientRiskProfile:
    """Complete risk profile for a patient."""
    patient_id: str
    patient_name: str
    date_of_birth: date
    age: int
    gender: str
    risk_score: RiskScore
    chronic_conditions: List[ChronicCondition] = field(default_factory=list)
    hcc_codes: List[str] = field(default_factory=list)
    recent_utilization: Dict[str, int] = field(default_factory=dict)
    care_gaps: List[str] = field(default_factory=list)
    sdoh_factors: Dict[str, Any] = field(default_factory=dict)
    last_pcp_visit: Optional[date] = None
    last_er_visit: Optional[date] = None
    assigned_care_manager: Optional[str] = None


@dataclass
class CareGap:
    """A care gap for a patient."""
    gap_id: str
    gap_type: str
    description: str
    priority: CareGapPriority
    measure_id: Optional[str]
    due_date: Optional[date]
    overdue_days: int
    patient_id: str
    patient_name: str
    recommended_action: str
    potential_value: float  # Value if closed
    last_outreach: Optional[date] = None
    outreach_attempts: int = 0


@dataclass
class PopulationRegistry:
    """Registry for a chronic condition population."""
    condition: ChronicCondition
    total_patients: int
    risk_distribution: Dict[RiskLevel, int]
    average_risk_score: float
    controlled_count: int
    uncontrolled_count: int
    care_gap_count: int
    avg_hba1c: Optional[float] = None  # For diabetes
    avg_bp: Optional[Dict[str, float]] = None  # For hypertension
    avg_egfr: Optional[float] = None  # For CKD
    key_metrics: Dict[str, float] = field(default_factory=dict)
    trends: Dict[str, List[float]] = field(default_factory=dict)


@dataclass
class SDOHFactor:
    """Social determinant of health factor."""
    factor_type: str
    factor_name: str
    prevalence: float
    impact_score: float
    affected_patients: int
    associated_conditions: List[str] = field(default_factory=list)
    recommended_resources: List[str] = field(default_factory=list)


@dataclass
class InterventionCampaign:
    """Outreach or intervention campaign."""
    campaign_id: str
    campaign_name: str
    target_population: str
    target_count: int
    outreach_type: str  # phone, mail, text, email
    start_date: date
    end_date: Optional[date]
    status: str
    reached_count: int
    engaged_count: int
    converted_count: int
    response_rate: float
    conversion_rate: float
    estimated_roi: float
    cost: float


@dataclass
class CohortComparison:
    """Comparison between patient cohorts."""
    cohort_a_name: str
    cohort_a_size: int
    cohort_b_name: str
    cohort_b_size: int
    metrics_comparison: Dict[str, Dict[str, float]]
    statistical_significance: Dict[str, bool]
    effect_sizes: Dict[str, float]


@dataclass
class OutcomeAttribution:
    """Attribution analysis for interventions."""
    intervention_name: str
    cohort_size: int
    baseline_metric: float
    post_intervention_metric: float
    improvement: float
    improvement_percentage: float
    attributed_savings: float
    confidence_level: float
    control_group_metric: Optional[float] = None


class PopulationHealthService:
    """
    Service for population health management analytics.

    Provides risk stratification, care gap identification, registry management,
    and intervention tracking for proactive population health management.
    """

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self.risk_thresholds = {
            RiskLevel.VERY_HIGH: 80,
            RiskLevel.HIGH: 60,
            RiskLevel.MODERATE: 40,
            RiskLevel.LOW: 20,
            RiskLevel.VERY_LOW: 0
        }

    def _calculate_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score."""
        if score >= 80:
            return RiskLevel.VERY_HIGH
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MODERATE
        elif score >= 20:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW

    async def get_risk_stratification(
        self,
        population_type: Optional[str] = None,
        risk_level: Optional[RiskLevel] = None,
        chronic_conditions: Optional[List[ChronicCondition]] = None,
        pcp_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get risk-stratified patient population.

        Args:
            population_type: Type of population filter
            risk_level: Filter by risk level
            chronic_conditions: Filter by chronic conditions
            pcp_id: Filter by primary care provider
            limit: Max records to return
            offset: Pagination offset
            tenant_id: Tenant ID

        Returns:
            Risk stratification data with patient list and summary
        """
        # Generate simulated patient risk profiles
        patients = self._generate_sample_patients(50)

        # Apply filters
        if risk_level:
            patients = [p for p in patients if p.risk_score.risk_level == risk_level]
        if chronic_conditions:
            patients = [
                p for p in patients
                if any(c in p.chronic_conditions for c in chronic_conditions)
            ]

        # Calculate summary statistics
        risk_distribution = {}
        for level in RiskLevel:
            count = len([p for p in patients if p.risk_score.risk_level == level])
            risk_distribution[level.value] = count

        total_patients = len(patients)
        avg_risk_score = sum(p.risk_score.overall_score for p in patients) / total_patients if total_patients else 0

        # Paginate results
        paginated_patients = patients[offset:offset + limit]

        return {
            "summary": {
                "total_patients": total_patients,
                "average_risk_score": round(avg_risk_score, 1),
                "risk_distribution": risk_distribution,
                "high_risk_count": risk_distribution.get("very_high", 0) + risk_distribution.get("high", 0),
                "care_gap_patients": len([p for p in patients if p.care_gaps]),
                "total_predicted_cost": sum(p.risk_score.predicted_costs for p in patients)
            },
            "patients": [self._patient_to_dict(p) for p in paginated_patients],
            "pagination": {
                "total": total_patients,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_patients
            }
        }

    def _generate_sample_patients(self, count: int) -> List[PatientRiskProfile]:
        """Generate sample patient risk profiles."""
        patients = []
        first_names = ["John", "Mary", "Robert", "Patricia", "Michael", "Jennifer", "William", "Linda"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

        for i in range(count):
            random.seed(i * 12345)

            risk_score = random.uniform(10, 95)
            age = random.randint(25, 85)

            # Higher age increases risk
            if age > 65:
                risk_score = min(100, risk_score + 20)

            conditions = []
            if risk_score > 50:
                num_conditions = random.randint(1, 4)
                conditions = random.sample(list(ChronicCondition), min(num_conditions, len(ChronicCondition)))

            care_gaps = []
            if random.random() > 0.5:
                gap_types = ["Annual wellness", "Diabetic eye exam", "Colonoscopy", "Mammogram", "A1c test"]
                care_gaps = random.sample(gap_types, random.randint(1, 3))

            patients.append(PatientRiskProfile(
                patient_id=f"PAT-{i:05d}",
                patient_name=f"{random.choice(first_names)} {random.choice(last_names)}",
                date_of_birth=date(2024 - age, random.randint(1, 12), random.randint(1, 28)),
                age=age,
                gender=random.choice(["Male", "Female"]),
                risk_score=RiskScore(
                    overall_score=round(risk_score, 1),
                    risk_level=self._calculate_risk_level(risk_score),
                    percentile=int(risk_score),
                    components={
                        "clinical": round(random.uniform(0, 40), 1),
                        "utilization": round(random.uniform(0, 30), 1),
                        "sdoh": round(random.uniform(0, 20), 1),
                        "behavioral": round(random.uniform(0, 10), 1)
                    },
                    contributing_factors=[
                        f.value for f in conditions[:2]
                    ] if conditions else [],
                    predicted_costs=round(random.uniform(5000, 150000), 2),
                    predicted_utilization={
                        "ed_visits": round(random.uniform(0, 5), 1),
                        "admissions": round(random.uniform(0, 3), 1),
                        "specialist_visits": round(random.uniform(2, 15), 1)
                    }
                ),
                chronic_conditions=conditions,
                hcc_codes=[f"HCC-{random.randint(1, 200):03d}" for _ in range(len(conditions))],
                recent_utilization={
                    "ed_visits_12m": random.randint(0, 5),
                    "admissions_12m": random.randint(0, 3),
                    "pcp_visits_12m": random.randint(0, 8),
                    "specialist_visits_12m": random.randint(0, 12)
                },
                care_gaps=care_gaps,
                sdoh_factors={
                    "transportation_barrier": random.random() < 0.2,
                    "food_insecurity": random.random() < 0.15,
                    "housing_instability": random.random() < 0.1,
                    "social_isolation": random.random() < 0.25
                },
                last_pcp_visit=date.today() - timedelta(days=random.randint(30, 365)),
                last_er_visit=date.today() - timedelta(days=random.randint(60, 730)) if random.random() > 0.5 else None,
                assigned_care_manager="Care Manager Smith" if risk_score > 70 else None
            ))

        return patients

    def _patient_to_dict(self, patient: PatientRiskProfile) -> Dict[str, Any]:
        """Convert patient profile to dictionary."""
        return {
            "patient_id": patient.patient_id,
            "patient_name": patient.patient_name,
            "age": patient.age,
            "gender": patient.gender,
            "risk_score": patient.risk_score.overall_score,
            "risk_level": patient.risk_score.risk_level.value,
            "risk_percentile": patient.risk_score.percentile,
            "chronic_conditions": [c.value for c in patient.chronic_conditions],
            "care_gaps_count": len(patient.care_gaps),
            "predicted_cost": patient.risk_score.predicted_costs,
            "last_pcp_visit": patient.last_pcp_visit.isoformat() if patient.last_pcp_visit else None,
            "care_manager": patient.assigned_care_manager
        }

    async def get_care_gaps(
        self,
        gap_types: Optional[List[str]] = None,
        priority: Optional[CareGapPriority] = None,
        patient_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        overdue_only: bool = False,
        limit: int = 100,
        offset: int = 0,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get care gaps with optional filters.

        Args:
            gap_types: Filter by gap type
            priority: Filter by priority
            patient_id: Filter by patient
            provider_id: Filter by provider
            overdue_only: Only return overdue gaps
            limit: Max records
            offset: Pagination offset
            tenant_id: Tenant ID

        Returns:
            Care gaps list with summary statistics
        """
        # Generate sample care gaps
        gaps = self._generate_sample_care_gaps(200)

        # Apply filters
        if gap_types:
            gaps = [g for g in gaps if g.gap_type in gap_types]
        if priority:
            gaps = [g for g in gaps if g.priority == priority]
        if patient_id:
            gaps = [g for g in gaps if g.patient_id == patient_id]
        if overdue_only:
            gaps = [g for g in gaps if g.overdue_days > 0]

        # Summary by type
        by_type = {}
        for gap in gaps:
            if gap.gap_type not in by_type:
                by_type[gap.gap_type] = {"count": 0, "overdue": 0, "potential_value": 0}
            by_type[gap.gap_type]["count"] += 1
            if gap.overdue_days > 0:
                by_type[gap.gap_type]["overdue"] += 1
            by_type[gap.gap_type]["potential_value"] += gap.potential_value

        # Summary by priority
        by_priority = {}
        for p in CareGapPriority:
            count = len([g for g in gaps if g.priority == p])
            by_priority[p.value] = count

        total_gaps = len(gaps)
        paginated_gaps = gaps[offset:offset + limit]

        return {
            "summary": {
                "total_gaps": total_gaps,
                "overdue_count": len([g for g in gaps if g.overdue_days > 0]),
                "total_potential_value": sum(g.potential_value for g in gaps),
                "by_type": by_type,
                "by_priority": by_priority
            },
            "gaps": [self._gap_to_dict(g) for g in paginated_gaps],
            "pagination": {
                "total": total_gaps,
                "limit": limit,
                "offset": offset
            }
        }

    def _generate_sample_care_gaps(self, count: int) -> List[CareGap]:
        """Generate sample care gaps."""
        gap_types = [
            ("Annual Wellness Visit", "AWV", "Schedule annual wellness visit", 150),
            ("Diabetic Eye Exam", "DM-EYE", "Complete diabetic retinopathy screening", 75),
            ("HbA1c Test", "DM-A1C", "Order HbA1c test for diabetes monitoring", 50),
            ("Blood Pressure Control", "HTN-BP", "Follow up for blood pressure management", 100),
            ("Colorectal Cancer Screening", "CRC", "Schedule colonoscopy or FIT test", 200),
            ("Breast Cancer Screening", "BCS", "Schedule mammogram", 175),
            ("Cervical Cancer Screening", "CCS", "Schedule Pap smear", 125),
            ("Flu Vaccination", "FLU", "Administer influenza vaccine", 25),
            ("Pneumonia Vaccination", "PPSV", "Administer pneumococcal vaccine", 35),
            ("Medication Adherence", "MED-ADH", "Address medication non-adherence", 80),
        ]

        gaps = []
        for i in range(count):
            random.seed(i * 54321)
            gap_info = random.choice(gap_types)

            overdue = random.randint(-30, 180)  # Negative means not yet due
            priority = CareGapPriority.CRITICAL if overdue > 90 else (
                CareGapPriority.HIGH if overdue > 30 else (
                    CareGapPriority.MEDIUM if overdue > 0 else CareGapPriority.LOW
                )
            )

            gaps.append(CareGap(
                gap_id=f"GAP-{i:06d}",
                gap_type=gap_info[1],
                description=gap_info[0],
                priority=priority,
                measure_id=f"HEDIS-{gap_info[1]}",
                due_date=date.today() - timedelta(days=overdue) if overdue > 0 else date.today() + timedelta(days=abs(overdue)),
                overdue_days=max(0, overdue),
                patient_id=f"PAT-{random.randint(0, 999):05d}",
                patient_name=f"Patient {random.randint(1000, 9999)}",
                recommended_action=gap_info[2],
                potential_value=gap_info[3],
                last_outreach=date.today() - timedelta(days=random.randint(7, 60)) if random.random() > 0.5 else None,
                outreach_attempts=random.randint(0, 3)
            ))

        return gaps

    def _gap_to_dict(self, gap: CareGap) -> Dict[str, Any]:
        """Convert care gap to dictionary."""
        return {
            "gap_id": gap.gap_id,
            "gap_type": gap.gap_type,
            "description": gap.description,
            "priority": gap.priority.value,
            "due_date": gap.due_date.isoformat() if gap.due_date else None,
            "overdue_days": gap.overdue_days,
            "patient_id": gap.patient_id,
            "patient_name": gap.patient_name,
            "recommended_action": gap.recommended_action,
            "potential_value": gap.potential_value,
            "outreach_attempts": gap.outreach_attempts
        }

    async def get_chronic_disease_registry(
        self,
        condition: ChronicCondition,
        tenant_id: Optional[str] = None
    ) -> PopulationRegistry:
        """
        Get registry data for a chronic condition.

        Args:
            condition: The chronic condition
            tenant_id: Tenant ID

        Returns:
            Registry data with population statistics
        """
        random.seed(hash(condition.value))

        total = random.randint(500, 5000)
        controlled_pct = random.uniform(0.4, 0.7)

        risk_dist = {
            RiskLevel.VERY_HIGH: int(total * 0.1),
            RiskLevel.HIGH: int(total * 0.2),
            RiskLevel.MODERATE: int(total * 0.3),
            RiskLevel.LOW: int(total * 0.25),
            RiskLevel.VERY_LOW: int(total * 0.15)
        }

        registry = PopulationRegistry(
            condition=condition,
            total_patients=total,
            risk_distribution=risk_dist,
            average_risk_score=round(random.uniform(35, 65), 1),
            controlled_count=int(total * controlled_pct),
            uncontrolled_count=int(total * (1 - controlled_pct)),
            care_gap_count=int(total * random.uniform(0.2, 0.4)),
            key_metrics={
                "prevalence_rate": round(random.uniform(5, 15), 2),
                "control_rate": round(controlled_pct * 100, 1),
                "adherence_rate": round(random.uniform(60, 85), 1),
                "complication_rate": round(random.uniform(5, 20), 1)
            },
            trends={
                "control_rate": [round(controlled_pct * 100 + random.uniform(-5, 5), 1) for _ in range(12)],
                "patient_count": [int(total + random.uniform(-50, 100)) for _ in range(12)]
            }
        )

        # Condition-specific metrics
        if condition == ChronicCondition.DIABETES:
            registry.avg_hba1c = round(random.uniform(7.0, 9.0), 1)
            registry.key_metrics["avg_hba1c"] = registry.avg_hba1c
            registry.key_metrics["eye_exam_rate"] = round(random.uniform(40, 70), 1)
            registry.key_metrics["foot_exam_rate"] = round(random.uniform(50, 80), 1)
        elif condition == ChronicCondition.HYPERTENSION:
            registry.avg_bp = {"systolic": round(random.uniform(130, 150), 0), "diastolic": round(random.uniform(80, 95), 0)}
            registry.key_metrics["avg_bp_systolic"] = registry.avg_bp["systolic"]
            registry.key_metrics["avg_bp_diastolic"] = registry.avg_bp["diastolic"]
        elif condition == ChronicCondition.CKD:
            registry.avg_egfr = round(random.uniform(35, 55), 1)
            registry.key_metrics["avg_egfr"] = registry.avg_egfr
            registry.key_metrics["stage_distribution"] = {"Stage 1-2": 30, "Stage 3": 45, "Stage 4": 20, "Stage 5": 5}

        return registry

    async def get_sdoh_analysis(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get social determinants of health analysis.

        Returns:
            SDOH prevalence and impact analysis
        """
        factors = [
            SDOHFactor(
                factor_type="Economic Stability",
                factor_name="Financial Strain",
                prevalence=18.5,
                impact_score=8.2,
                affected_patients=1850,
                associated_conditions=["Depression", "Hypertension", "Diabetes"],
                recommended_resources=["Financial counseling", "Payment plans", "Charity care"]
            ),
            SDOHFactor(
                factor_type="Food Access",
                factor_name="Food Insecurity",
                prevalence=12.3,
                impact_score=7.5,
                affected_patients=1230,
                associated_conditions=["Diabetes", "Malnutrition", "Obesity"],
                recommended_resources=["Food bank referral", "SNAP enrollment", "Nutrition counseling"]
            ),
            SDOHFactor(
                factor_type="Transportation",
                factor_name="Transportation Barriers",
                prevalence=15.8,
                impact_score=6.8,
                affected_patients=1580,
                associated_conditions=["Missed appointments", "Delayed care"],
                recommended_resources=["Medical transportation", "Telehealth", "Home visits"]
            ),
            SDOHFactor(
                factor_type="Housing",
                factor_name="Housing Instability",
                prevalence=8.2,
                impact_score=9.1,
                affected_patients=820,
                associated_conditions=["Mental health", "Respiratory conditions", "Infections"],
                recommended_resources=["Housing assistance", "Social work referral", "Shelter resources"]
            ),
            SDOHFactor(
                factor_type="Social Support",
                factor_name="Social Isolation",
                prevalence=22.5,
                impact_score=7.0,
                affected_patients=2250,
                associated_conditions=["Depression", "Anxiety", "Cognitive decline"],
                recommended_resources=["Community programs", "Support groups", "Mental health services"]
            ),
        ]

        return {
            "summary": {
                "total_screened": 10000,
                "positive_screens": sum(f.affected_patients for f in factors),
                "average_impact_score": round(sum(f.impact_score for f in factors) / len(factors), 1),
                "most_prevalent": max(factors, key=lambda f: f.prevalence).factor_name
            },
            "factors": [
                {
                    "factor_type": f.factor_type,
                    "factor_name": f.factor_name,
                    "prevalence": f.prevalence,
                    "impact_score": f.impact_score,
                    "affected_patients": f.affected_patients,
                    "associated_conditions": f.associated_conditions,
                    "recommended_resources": f.recommended_resources
                }
                for f in factors
            ],
            "geographic_distribution": {
                "Urban": {"prevalence": 15.2, "patients": 4500},
                "Suburban": {"prevalence": 10.5, "patients": 3500},
                "Rural": {"prevalence": 22.8, "patients": 2000}
            },
            "z_codes_distribution": {
                "Z59.0 - Homelessness": 245,
                "Z59.4 - Food insecurity": 1230,
                "Z59.8 - Housing problems": 575,
                "Z63.0 - Relationship problems": 890,
                "Z56.0 - Employment problems": 1125
            }
        }

    async def get_intervention_campaigns(
        self,
        status: Optional[str] = None,
        target_population: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[InterventionCampaign]:
        """Get outreach and intervention campaigns."""
        campaigns = [
            InterventionCampaign(
                campaign_id="CAMP-001",
                campaign_name="Diabetes Care Gap Closure",
                target_population="Diabetics missing HbA1c",
                target_count=500,
                outreach_type="phone",
                start_date=date(2024, 1, 15),
                end_date=date(2024, 3, 15),
                status="completed",
                reached_count=425,
                engaged_count=320,
                converted_count=280,
                response_rate=75.3,
                conversion_rate=65.9,
                estimated_roi=3.5,
                cost=15000
            ),
            InterventionCampaign(
                campaign_id="CAMP-002",
                campaign_name="Annual Wellness Visit Outreach",
                target_population="Medicare patients due for AWV",
                target_count=1200,
                outreach_type="mail",
                start_date=date(2024, 2, 1),
                end_date=date(2024, 4, 30),
                status="completed",
                reached_count=1150,
                engaged_count=580,
                converted_count=420,
                response_rate=50.4,
                conversion_rate=36.5,
                estimated_roi=4.2,
                cost=8500
            ),
            InterventionCampaign(
                campaign_id="CAMP-003",
                campaign_name="High-Risk Patient Care Management",
                target_population="Top 5% risk patients",
                target_count=150,
                outreach_type="phone",
                start_date=date(2024, 3, 1),
                end_date=None,
                status="in_progress",
                reached_count=125,
                engaged_count=98,
                converted_count=75,
                response_rate=78.4,
                conversion_rate=60.0,
                estimated_roi=5.8,
                cost=45000
            ),
            InterventionCampaign(
                campaign_id="CAMP-004",
                campaign_name="Colorectal Cancer Screening",
                target_population="Patients 50-75 due for screening",
                target_count=800,
                outreach_type="text",
                start_date=date(2024, 4, 1),
                end_date=None,
                status="in_progress",
                reached_count=720,
                engaged_count=450,
                converted_count=280,
                response_rate=62.5,
                conversion_rate=38.9,
                estimated_roi=2.8,
                cost=12000
            ),
        ]

        if status:
            campaigns = [c for c in campaigns if c.status == status]
        if target_population:
            campaigns = [c for c in campaigns if target_population.lower() in c.target_population.lower()]

        return campaigns

    async def generate_outreach_list(
        self,
        criteria: Dict[str, Any],
        limit: int = 100,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a patient outreach list based on criteria.

        Args:
            criteria: Filter criteria for patient selection
            limit: Maximum patients to include
            tenant_id: Tenant ID

        Returns:
            Outreach list with patient details and priorities
        """
        # Get patients matching criteria
        result = await self.get_risk_stratification(
            risk_level=RiskLevel(criteria.get("risk_level")) if criteria.get("risk_level") else None,
            chronic_conditions=[ChronicCondition(c) for c in criteria.get("conditions", [])],
            limit=limit,
            tenant_id=tenant_id
        )

        patients = result["patients"]

        # Prioritize based on criteria
        prioritized = sorted(
            patients,
            key=lambda p: (p["risk_score"], p["care_gaps_count"]),
            reverse=True
        )

        return {
            "list_id": f"OL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.utcnow().isoformat(),
            "criteria": criteria,
            "total_count": len(prioritized),
            "patients": [
                {
                    **p,
                    "priority_rank": idx + 1,
                    "recommended_outreach": "phone" if p["risk_score"] > 70 else "mail"
                }
                for idx, p in enumerate(prioritized)
            ]
        }

    async def get_cohort_comparison(
        self,
        cohort_a_criteria: Dict[str, Any],
        cohort_b_criteria: Dict[str, Any],
        metrics: List[str],
        tenant_id: Optional[str] = None
    ) -> CohortComparison:
        """
        Compare two patient cohorts on specified metrics.

        Args:
            cohort_a_criteria: Criteria for cohort A
            cohort_b_criteria: Criteria for cohort B
            metrics: Metrics to compare
            tenant_id: Tenant ID

        Returns:
            Comparison analysis
        """
        random.seed(42)

        metrics_comparison = {}
        significance = {}
        effect_sizes = {}

        for metric in metrics:
            a_value = random.uniform(10, 90)
            b_value = a_value + random.uniform(-15, 15)

            metrics_comparison[metric] = {
                "cohort_a": round(a_value, 2),
                "cohort_b": round(b_value, 2),
                "difference": round(b_value - a_value, 2),
                "difference_pct": round((b_value - a_value) / a_value * 100, 2) if a_value else 0
            }

            significance[metric] = abs(b_value - a_value) > 5
            effect_sizes[metric] = round(abs(b_value - a_value) / 10, 3)

        return CohortComparison(
            cohort_a_name=cohort_a_criteria.get("name", "Cohort A"),
            cohort_a_size=random.randint(500, 2000),
            cohort_b_name=cohort_b_criteria.get("name", "Cohort B"),
            cohort_b_size=random.randint(500, 2000),
            metrics_comparison=metrics_comparison,
            statistical_significance=significance,
            effect_sizes=effect_sizes
        )

    async def get_intervention_roi(
        self,
        intervention_id: str,
        tenant_id: Optional[str] = None
    ) -> OutcomeAttribution:
        """
        Get ROI analysis for an intervention.

        Args:
            intervention_id: ID of the intervention
            tenant_id: Tenant ID

        Returns:
            Outcome attribution analysis
        """
        random.seed(hash(intervention_id))

        baseline = random.uniform(15, 30)
        post = baseline - random.uniform(2, 8)
        improvement = baseline - post

        return OutcomeAttribution(
            intervention_name=f"Intervention {intervention_id}",
            cohort_size=random.randint(100, 500),
            baseline_metric=round(baseline, 2),
            post_intervention_metric=round(post, 2),
            improvement=round(improvement, 2),
            improvement_percentage=round(improvement / baseline * 100, 1),
            attributed_savings=round(improvement * random.uniform(5000, 15000), 2),
            confidence_level=round(random.uniform(0.85, 0.98), 2),
            control_group_metric=round(baseline + random.uniform(-2, 2), 2)
        )


# Global service instance
population_health_service = PopulationHealthService()
