"""
AI Diagnostic Support Service

Provides AI-powered differential diagnosis suggestions,
explainable reasoning, and feedback learning.

EPIC-020: Clinical Decision Support
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from modules.cds.models import (
    DiagnosticSession,
    DiagnosisSuggestion,
    DiagnosticFeedback,
    DiagnosisSuggestionSource,
)
from modules.cds.schemas import (
    DiagnosticSessionCreate,
    DiagnosticSessionUpdate,
    DiagnosisSuggestionResponse,
    DiagnosticSessionResponse,
    DifferentialDiagnosisRequest,
    DifferentialDiagnosisResponse,
    DiagnosisFeedback as DiagnosisFeedbackSchema,
    SymptomInput,
    FindingInput,
)


class DiagnosticService:
    """Service for AI-powered diagnostic support."""

    # Common "can't miss" diagnoses by symptom
    CANT_MISS_DIAGNOSES = {
        "chest_pain": ["I21.9", "I26.9", "I71.00"],  # MI, PE, Aortic dissection
        "headache": ["I60.9", "G00.9", "C71.9"],  # SAH, Meningitis, Brain tumor
        "abdominal_pain": ["K35.80", "K80.00", "K56.60"],  # Appendicitis, Cholecystitis, Bowel obstruction
        "shortness_of_breath": ["I26.9", "J18.9", "I50.9"],  # PE, Pneumonia, Heart failure
        "syncope": ["I21.9", "I26.9", "I49.9"],  # MI, PE, Arrhythmia
    }

    # Symptom-diagnosis probability mappings (simplified)
    SYMPTOM_DIAGNOSIS_MAP = {
        "chest_pain": [
            ("I20.9", 0.3, "Angina pectoris"),
            ("I21.9", 0.15, "Acute myocardial infarction"),
            ("M54.6", 0.25, "Musculoskeletal chest pain"),
            ("K21.0", 0.15, "GERD"),
        ],
        "fever": [
            ("J06.9", 0.35, "Upper respiratory infection"),
            ("J18.9", 0.15, "Pneumonia"),
            ("N39.0", 0.10, "Urinary tract infection"),
        ],
        "cough": [
            ("J06.9", 0.40, "Upper respiratory infection"),
            ("J45.909", 0.15, "Asthma"),
            ("J18.9", 0.10, "Pneumonia"),
            ("J44.9", 0.08, "COPD exacerbation"),
        ],
    }

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create_session(
        self,
        data: DiagnosticSessionCreate,
        provider_id: UUID,
    ) -> DiagnosticSession:
        """Create a new diagnostic session."""
        session = DiagnosticSession(
            tenant_id=self.tenant_id,
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            provider_id=provider_id,
            chief_complaint=data.chief_complaint,
            symptoms=[s.dict() for s in data.symptoms],
            findings=[f.dict() for f in data.findings],
            history=data.history,
            patient_age=data.patient_age,
            patient_gender=data.patient_gender,
            relevant_conditions=data.relevant_conditions,
            relevant_medications=data.relevant_medications,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session(self, session_id: UUID) -> Optional[DiagnosticSession]:
        """Get a diagnostic session by ID."""
        query = select(DiagnosticSession).where(
            and_(
                DiagnosticSession.id == session_id,
                DiagnosticSession.tenant_id == self.tenant_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_session(
        self,
        session_id: UUID,
        data: DiagnosticSessionUpdate,
    ) -> Optional[DiagnosticSession]:
        """Update a diagnostic session."""
        session = await self.get_session(session_id)
        if not session:
            return None

        if data.chief_complaint is not None:
            session.chief_complaint = data.chief_complaint
        if data.symptoms is not None:
            session.symptoms = [s.dict() for s in data.symptoms]
        if data.findings is not None:
            session.findings = [f.dict() for f in data.findings]
        if data.status is not None:
            session.status = data.status
            if data.status == "completed":
                session.completed_at = datetime.utcnow()

        await self.db.flush()
        return session

    async def generate_differential(
        self,
        request: DifferentialDiagnosisRequest,
        provider_id: UUID,
    ) -> DifferentialDiagnosisResponse:
        """Generate differential diagnosis for symptoms and findings."""
        # Create session
        session_data = DiagnosticSessionCreate(
            patient_id=request.patient_id,
            chief_complaint=request.chief_complaint,
            symptoms=request.symptoms,
            findings=request.findings,
            patient_age=request.patient_age,
            patient_gender=request.patient_gender,
        )
        session = await self.create_session(session_data, provider_id)

        # Generate suggestions
        suggestions = await self._generate_suggestions(
            symptoms=request.symptoms,
            findings=request.findings,
            patient_age=request.patient_age,
            patient_gender=request.patient_gender,
            max_suggestions=request.max_suggestions,
        )

        # Store suggestions
        suggestion_records = []
        for rank, suggestion in enumerate(suggestions, 1):
            record = DiagnosisSuggestion(
                tenant_id=self.tenant_id,
                session_id=session.id,
                diagnosis_code=suggestion["code"],
                diagnosis_code_system="icd10",
                diagnosis_name=suggestion["name"],
                probability=suggestion.get("probability"),
                confidence=suggestion.get("confidence"),
                rank=rank,
                source=suggestion.get("source", DiagnosisSuggestionSource.DIFFERENTIAL_ENGINE),
                is_cant_miss=suggestion.get("is_cant_miss", False),
                urgency=suggestion.get("urgency"),
                reasoning=suggestion.get("reasoning"),
                supporting_evidence=suggestion.get("supporting_evidence", []),
                against_evidence=suggestion.get("against_evidence", []),
                recommended_tests=suggestion.get("recommended_tests", []),
                recommended_imaging=suggestion.get("recommended_imaging", []),
                recommended_referrals=suggestion.get("recommended_referrals", []),
            )
            self.db.add(record)
            suggestion_records.append(record)

        await self.db.flush()

        # Separate can't miss diagnoses
        cant_miss = [s for s in suggestion_records if s.is_cant_miss]
        differential = [s for s in suggestion_records if not s.is_cant_miss]

        # Generate recommended workup
        workup = await self._generate_workup_recommendations(
            suggestions[:5], request.symptoms, request.findings
        )

        return DifferentialDiagnosisResponse(
            session_id=session.id,
            patient_id=request.patient_id,
            differential=[DiagnosisSuggestionResponse.from_orm(s) for s in differential],
            cant_miss_diagnoses=[DiagnosisSuggestionResponse.from_orm(s) for s in cant_miss],
            recommended_workup=workup,
            generated_at=datetime.utcnow(),
        )

    async def _generate_suggestions(
        self,
        symptoms: List[SymptomInput],
        findings: List[FindingInput],
        patient_age: Optional[int],
        patient_gender: Optional[str],
        max_suggestions: int = 10,
    ) -> List[Dict[str, Any]]:
        """Generate diagnostic suggestions based on symptoms and findings."""
        suggestions = []
        diagnosis_scores: Dict[str, Dict[str, Any]] = {}

        # Process each symptom
        for symptom in symptoms:
            symptom_key = symptom.name.lower().replace(" ", "_")

            # Check for can't miss diagnoses
            if symptom_key in self.CANT_MISS_DIAGNOSES:
                for code in self.CANT_MISS_DIAGNOSES[symptom_key]:
                    if code not in diagnosis_scores:
                        diagnosis_scores[code] = {
                            "code": code,
                            "probability": 0.05,  # Low but non-zero
                            "is_cant_miss": True,
                            "supporting_evidence": [],
                        }
                    diagnosis_scores[code]["supporting_evidence"].append(
                        {"type": "symptom", "value": symptom.name}
                    )

            # Check symptom-diagnosis mappings
            if symptom_key in self.SYMPTOM_DIAGNOSIS_MAP:
                for code, prob, name in self.SYMPTOM_DIAGNOSIS_MAP[symptom_key]:
                    if code not in diagnosis_scores:
                        diagnosis_scores[code] = {
                            "code": code,
                            "name": name,
                            "probability": 0,
                            "is_cant_miss": False,
                            "supporting_evidence": [],
                        }

                    # Adjust probability based on symptom characteristics
                    adjusted_prob = prob
                    if symptom.severity == "severe":
                        adjusted_prob *= 1.2
                    if symptom.duration and "days" in symptom.duration.lower():
                        if "7" in symptom.duration or any(c.isdigit() and int(c) > 5 for c in symptom.duration):
                            adjusted_prob *= 1.1

                    diagnosis_scores[code]["probability"] += adjusted_prob
                    diagnosis_scores[code]["supporting_evidence"].append(
                        {"type": "symptom", "value": symptom.name, "contribution": prob}
                    )

        # Adjust for demographics
        for code, data in diagnosis_scores.items():
            if patient_age:
                # Age-specific adjustments
                if patient_age >= 65:
                    # Increase probability for age-related conditions
                    if code.startswith("I"):  # Cardiovascular
                        data["probability"] *= 1.3
                elif patient_age < 18:
                    # Decrease probability for adult-onset conditions
                    if code.startswith("I2"):  # Heart disease
                        data["probability"] *= 0.3

            if patient_gender:
                # Gender-specific adjustments
                if patient_gender.lower() == "female":
                    if code.startswith("N"):  # GU conditions
                        data["probability"] *= 1.2
                elif patient_gender.lower() == "male":
                    if code.startswith("N4"):  # Prostate conditions
                        data["probability"] *= 1.5

        # Normalize probabilities
        total_prob = sum(d["probability"] for d in diagnosis_scores.values())
        if total_prob > 0:
            for data in diagnosis_scores.values():
                data["probability"] = min(data["probability"] / total_prob, 0.95)
                data["confidence"] = min(0.8, data["probability"] * 1.5)  # Confidence related to probability

        # Generate reasoning and recommendations
        for code, data in diagnosis_scores.items():
            data["reasoning"] = self._generate_reasoning(code, data["supporting_evidence"])
            data["source"] = DiagnosisSuggestionSource.DIFFERENTIAL_ENGINE
            data["urgency"] = "emergent" if data.get("is_cant_miss") else "routine"

            # Add recommended workup
            data["recommended_tests"] = self._get_recommended_tests(code)
            data["recommended_imaging"] = self._get_recommended_imaging(code)

        # Sort by probability (can't miss first, then by probability)
        sorted_suggestions = sorted(
            diagnosis_scores.values(),
            key=lambda x: (not x.get("is_cant_miss", False), -x.get("probability", 0)),
        )

        return sorted_suggestions[:max_suggestions]

    def _generate_reasoning(
        self,
        diagnosis_code: str,
        supporting_evidence: List[Dict[str, Any]],
    ) -> str:
        """Generate human-readable reasoning for a diagnosis."""
        if not supporting_evidence:
            return "Suggested based on clinical pattern matching."

        symptoms = [e["value"] for e in supporting_evidence if e["type"] == "symptom"]
        if symptoms:
            return f"Suggested based on presenting symptoms: {', '.join(symptoms)}. " \
                   f"Consider this diagnosis in the differential based on symptom pattern."

        return "Suggested based on clinical presentation."

    def _get_recommended_tests(self, diagnosis_code: str) -> List[Dict[str, Any]]:
        """Get recommended tests for a diagnosis."""
        # Common test recommendations by diagnosis category
        tests = []

        if diagnosis_code.startswith("I2"):  # Ischemic heart disease
            tests = [
                {"code": "93000", "name": "ECG", "urgency": "stat"},
                {"code": "82553", "name": "Troponin", "urgency": "stat"},
                {"code": "85025", "name": "CBC", "urgency": "routine"},
            ]
        elif diagnosis_code.startswith("J"):  # Respiratory
            tests = [
                {"code": "85025", "name": "CBC", "urgency": "routine"},
                {"code": "82803", "name": "BMP", "urgency": "routine"},
            ]
        elif diagnosis_code.startswith("N"):  # GU
            tests = [
                {"code": "81001", "name": "Urinalysis", "urgency": "routine"},
                {"code": "87086", "name": "Urine culture", "urgency": "routine"},
            ]

        return tests

    def _get_recommended_imaging(self, diagnosis_code: str) -> List[Dict[str, Any]]:
        """Get recommended imaging for a diagnosis."""
        imaging = []

        if diagnosis_code.startswith("I2"):  # Ischemic heart disease
            imaging = [
                {"code": "71046", "name": "Chest X-ray", "urgency": "routine"},
            ]
        elif diagnosis_code.startswith("J18"):  # Pneumonia
            imaging = [
                {"code": "71046", "name": "Chest X-ray", "urgency": "stat"},
            ]
        elif diagnosis_code.startswith("K"):  # GI
            imaging = [
                {"code": "74176", "name": "CT Abdomen/Pelvis", "urgency": "routine"},
            ]

        return imaging

    async def _generate_workup_recommendations(
        self,
        top_suggestions: List[DiagnosisSuggestion],
        symptoms: List[SymptomInput],
        findings: List[FindingInput],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate consolidated workup recommendations."""
        tests = {}
        imaging = {}
        referrals = []

        for suggestion in top_suggestions:
            for test in suggestion.recommended_tests or []:
                code = test.get("code")
                if code and code not in tests:
                    tests[code] = test

            for img in suggestion.recommended_imaging or []:
                code = img.get("code")
                if code and code not in imaging:
                    imaging[code] = img

            for ref in suggestion.recommended_referrals or []:
                if ref not in referrals:
                    referrals.append(ref)

        return {
            "labs": list(tests.values()),
            "imaging": list(imaging.values()),
            "referrals": referrals,
        }

    # Feedback Methods

    async def submit_feedback(
        self,
        data: DiagnosisFeedbackSchema,
    ) -> Optional[DiagnosisSuggestion]:
        """Submit feedback on a diagnosis suggestion."""
        query = select(DiagnosisSuggestion).where(
            and_(
                DiagnosisSuggestion.id == data.suggestion_id,
                DiagnosisSuggestion.tenant_id == self.tenant_id,
            )
        )
        result = await self.db.execute(query)
        suggestion = result.scalar_one_or_none()

        if suggestion:
            suggestion.was_accepted = data.was_accepted
            suggestion.feedback_rating = data.feedback_rating
            suggestion.feedback_comment = data.feedback_comment
            suggestion.final_diagnosis = data.final_diagnosis

            await self.db.flush()

            # Update aggregated feedback
            await self._update_feedback_aggregates(suggestion)

        return suggestion

    async def _update_feedback_aggregates(
        self,
        suggestion: DiagnosisSuggestion,
    ):
        """Update aggregated feedback metrics."""
        today = date.today()
        period_start = today.replace(day=1)

        if today.month == 12:
            period_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = date(today.year, today.month + 1, 1) - timedelta(days=1)

        # Get or create feedback record
        query = select(DiagnosticFeedback).where(
            and_(
                DiagnosticFeedback.tenant_id == self.tenant_id,
                DiagnosticFeedback.diagnosis_code == suggestion.diagnosis_code,
                DiagnosticFeedback.period_start == period_start,
                DiagnosticFeedback.period_end == period_end,
            )
        )
        result = await self.db.execute(query)
        feedback = result.scalar_one_or_none()

        if not feedback:
            feedback = DiagnosticFeedback(
                tenant_id=self.tenant_id,
                diagnosis_code=suggestion.diagnosis_code,
                period_start=period_start,
                period_end=period_end,
            )
            self.db.add(feedback)

        # Update metrics
        feedback.times_suggested = (feedback.times_suggested or 0) + 1

        if suggestion.was_accepted is True:
            feedback.times_accepted = (feedback.times_accepted or 0) + 1
        elif suggestion.was_accepted is False:
            feedback.times_rejected = (feedback.times_rejected or 0) + 1

        if suggestion.feedback_rating:
            feedback.feedback_count = (feedback.feedback_count or 0) + 1
            # Update average rating
            if feedback.avg_rating:
                feedback.avg_rating = (
                    (feedback.avg_rating * (feedback.feedback_count - 1) + suggestion.feedback_rating)
                    / feedback.feedback_count
                )
            else:
                feedback.avg_rating = suggestion.feedback_rating

        await self.db.flush()

    async def get_session_history(
        self,
        patient_id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None,
        limit: int = 20,
    ) -> List[DiagnosticSession]:
        """Get diagnostic session history."""
        query = select(DiagnosticSession).where(
            DiagnosticSession.tenant_id == self.tenant_id
        )

        if patient_id:
            query = query.where(DiagnosticSession.patient_id == patient_id)
        if provider_id:
            query = query.where(DiagnosticSession.provider_id == provider_id)

        query = query.order_by(DiagnosticSession.started_at.desc())
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_model_performance(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Get AI model performance metrics."""
        query = select(DiagnosisSuggestion).where(
            and_(
                DiagnosisSuggestion.tenant_id == self.tenant_id,
                DiagnosisSuggestion.created_at >= datetime.combine(start_date, datetime.min.time()),
                DiagnosisSuggestion.created_at <= datetime.combine(end_date, datetime.max.time()),
                DiagnosisSuggestion.was_accepted.isnot(None),
            )
        )

        result = await self.db.execute(query)
        suggestions = list(result.scalars().all())

        total = len(suggestions)
        accepted = sum(1 for s in suggestions if s.was_accepted is True)
        rejected = sum(1 for s in suggestions if s.was_accepted is False)

        ratings = [s.feedback_rating for s in suggestions if s.feedback_rating]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        # Calculate accuracy by rank
        rank_accuracy = {}
        for suggestion in suggestions:
            if suggestion.rank and suggestion.was_accepted:
                if suggestion.rank not in rank_accuracy:
                    rank_accuracy[suggestion.rank] = {"total": 0, "accepted": 0}
                rank_accuracy[suggestion.rank]["total"] += 1
                if suggestion.was_accepted:
                    rank_accuracy[suggestion.rank]["accepted"] += 1

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_suggestions": total,
            "acceptance_rate": round(accepted / total * 100, 2) if total > 0 else 0,
            "rejection_rate": round(rejected / total * 100, 2) if total > 0 else 0,
            "avg_feedback_rating": round(avg_rating, 2) if avg_rating else None,
            "accuracy_by_rank": {
                rank: round(data["accepted"] / data["total"] * 100, 2)
                for rank, data in rank_accuracy.items()
                if data["total"] > 0
            },
        }
