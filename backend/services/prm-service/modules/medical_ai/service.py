"""
Medical AI Service
EPIC-010: Medical AI Capabilities Service Layer
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from dataclasses import asdict
from loguru import logger

from sqlalchemy.orm import Session

from shared.medical_ai import (
    # Triage
    triage_engine,
    # Documentation
    ambient_transcription_service,
    soap_generator,
    code_suggester,
    # Entity Recognition
    medical_entity_extractor,
    # Decision Intelligence
    clinical_decision_intelligence,
    # Predictive Analytics
    predictive_analytics_service,
    # Image Analysis
    medical_image_analysis_service,
    # NLP Pipeline
    clinical_nlp_pipeline,
    # Voice Biomarkers
    voice_biomarker_service,
)

from modules.medical_ai.schemas import (
    # Triage
    TriageRequest,
    TriageResponse,
    RedFlagAlertResponse,
    TriageExplanationResponse,
    # Documentation
    TranscriptionRequest,
    TranscriptionResponse,
    SpeakerSegmentResponse,
    SOAPNoteRequest,
    SOAPNoteResponse,
    CodeSuggestionRequest,
    CodeSuggestionResponse,
    # Entity Recognition
    EntityExtractionRequest,
    EntityExtractionResponse,
    MedicalEntityResponse,
    EntityRelationshipResponse,
    EntityTypeEnum,
    NegationStatusEnum,
    # Clinical Decision Support
    ClinicalDecisionRequest,
    ClinicalDecisionResponse,
    GuidelineRecommendationResponse,
    DrugInteractionResponse,
    DifferentialDiagnosisResponse,
    InteractionSeverityEnum,
    # Predictive Analytics
    PredictiveAnalyticsRequest,
    PredictiveAnalyticsResponse,
    ReadmissionRiskResponse,
    DeteriorationAlertResponse,
    NoShowPredictionResponse,
    FallRiskResponse,
    RiskLevelEnum,
    # Image Analysis
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    ChestXrayResponse,
    RadiologyFindingResponse,
    SkinLesionResponse,
    WoundAssessmentResponse,
    ImageTypeEnum,
    # NLP Pipeline
    NLPPipelineRequest,
    NLPPipelineResponse,
    ClinicalSectionResponse,
    ProblemEntryResponse,
    MedicationEntryResponse,
    SocialDeterminantResponse,
    QualityMeasureResponse,
    # Voice Biomarkers
    VoiceBiomarkerRequest,
    VoiceBiomarkerResponse,
    DepressionAssessmentResponse,
    CognitiveAssessmentResponse,
    RespiratoryAssessmentResponse,
    # Statistics
    MedicalAIStatistics,
    MedicalAIHealthCheck,
)


class MedicalAIService:
    """
    Service layer for Medical AI capabilities.
    Integrates all shared medical AI services and provides
    a unified interface for the API router.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self._stats = {
            "triage_requests": 0,
            "documentation_requests": 0,
            "entity_extractions": 0,
            "decision_support_requests": 0,
            "predictions": 0,
            "image_analyses": 0,
            "nlp_pipeline_runs": 0,
            "voice_analyses": 0,
            "total_confidence": 0.0,
            "total_processing_time": 0.0,
            "red_flag_count": 0,
        }

    # ==================== Triage ====================

    async def perform_triage(
        self,
        org_id: UUID,
        request: TriageRequest
    ) -> TriageResponse:
        """Perform AI-powered medical triage"""
        start_time = datetime.utcnow()

        try:
            # Build patient context
            patient_context = {
                "age": request.age,
                "gender": request.gender,
                "vital_signs": request.vital_signs or {},
                "medical_history": request.medical_history or [],
                "current_medications": request.current_medications or [],
            }

            # Perform triage using the shared service
            result = await triage_engine.perform_triage(
                symptoms=request.symptoms,
                patient_context=patient_context,
                chief_complaint=request.chief_complaint,
            )

            # Update stats
            self._stats["triage_requests"] += 1
            self._stats["total_confidence"] += result.confidence
            self._stats["red_flag_count"] += len(result.red_flags)

            # Convert to response schema
            red_flags = [
                RedFlagAlertResponse(
                    name=rf.name,
                    description=rf.description,
                    severity=rf.severity,
                    action_required=rf.action_required,
                    evidence=rf.evidence,
                )
                for rf in result.red_flags
            ]

            explanation = TriageExplanationResponse(
                decision_path=result.explanation.decision_path,
                factors_considered=result.explanation.factors_considered,
                rationale=result.explanation.rationale,
                evidence_citations=result.explanation.evidence_citations,
                confidence_breakdown=result.explanation.confidence_breakdown,
                alternative_considerations=result.explanation.alternative_considerations,
            )

            return TriageResponse(
                triage_id=uuid.uuid4(),
                urgency_level=result.urgency_level.value,
                esi_level=result.esi_level,
                confidence=result.confidence,
                recommended_department=result.recommended_department,
                red_flags=red_flags,
                symptom_analysis=asdict(result.symptom_analysis) if result.symptom_analysis else {},
                explanation=explanation,
                suggested_questions=result.suggested_questions,
                estimated_wait_time=result.estimated_wait_time,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Triage error: {e}", exc_info=True)
            raise

    # ==================== Documentation AI ====================

    async def transcribe_encounter(
        self,
        org_id: UUID,
        request: TranscriptionRequest
    ) -> TranscriptionResponse:
        """Transcribe clinical encounter audio"""
        try:
            # Get audio data
            audio_data = None
            if request.audio_base64:
                import base64
                audio_data = base64.b64decode(request.audio_base64)

            result = await ambient_transcription_service.transcribe(
                audio_data=audio_data,
                audio_url=request.audio_url,
                encounter_type=request.encounter_type,
            )

            self._stats["documentation_requests"] += 1

            segments = [
                SpeakerSegmentResponse(
                    speaker=seg.speaker,
                    role=seg.role,
                    text=seg.text,
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    confidence=seg.confidence,
                )
                for seg in result.segments
            ]

            return TranscriptionResponse(
                transcription_id=result.transcription_id,
                full_text=result.full_text,
                segments=segments,
                duration_seconds=result.duration_seconds,
                word_count=result.word_count,
                clinical_summary=result.clinical_summary,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            raise

    async def generate_soap_note(
        self,
        org_id: UUID,
        request: SOAPNoteRequest
    ) -> SOAPNoteResponse:
        """Generate SOAP note from encounter"""
        try:
            result = await soap_generator.generate(
                transcript=request.transcript,
                provider_notes=request.provider_notes,
            )

            # Get code suggestions if requested
            icd10_codes = []
            cpt_codes = []
            hcc_codes = []

            if request.include_coding:
                full_text = f"{result.subjective} {result.objective} {result.assessment} {result.plan}"
                code_results = await code_suggester.suggest_codes(
                    clinical_text=full_text,
                    code_types=["icd10", "cpt", "hcc"],
                )

                for code in code_results:
                    code_dict = {
                        "code": code.code,
                        "description": code.description,
                        "confidence": code.confidence,
                        "evidence": code.evidence,
                    }
                    if code.code_type == "icd10":
                        icd10_codes.append(code_dict)
                    elif code.code_type == "cpt":
                        cpt_codes.append(code_dict)
                    elif code.code_type == "hcc":
                        hcc_codes.append(code_dict)

            return SOAPNoteResponse(
                note_id=result.note_id,
                subjective=result.subjective,
                objective=result.objective,
                assessment=result.assessment,
                plan=result.plan,
                icd10_codes=icd10_codes,
                cpt_codes=cpt_codes,
                hcc_codes=hcc_codes,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"SOAP note generation error: {e}", exc_info=True)
            raise

    async def suggest_codes(
        self,
        org_id: UUID,
        request: CodeSuggestionRequest
    ) -> List[CodeSuggestionResponse]:
        """Suggest medical codes from clinical text"""
        try:
            results = await code_suggester.suggest_codes(
                clinical_text=request.clinical_text,
                code_types=request.code_types,
                max_suggestions=request.max_suggestions,
            )

            return [
                CodeSuggestionResponse(
                    code=r.code,
                    description=r.description,
                    code_type=r.code_type,
                    confidence=r.confidence,
                    evidence=r.evidence,
                    category=r.category,
                )
                for r in results
            ]

        except Exception as e:
            logger.error(f"Code suggestion error: {e}", exc_info=True)
            raise

    # ==================== Entity Recognition ====================

    async def extract_entities(
        self,
        org_id: UUID,
        request: EntityExtractionRequest
    ) -> EntityExtractionResponse:
        """Extract medical entities from text"""
        start_time = datetime.utcnow()

        try:
            result = await medical_entity_extractor.extract(
                text=request.text,
                entity_types=[et.value for et in request.entity_types] if request.entity_types else None,
                include_negation=request.include_negation,
                include_relationships=request.include_relationships,
            )

            self._stats["entity_extractions"] += 1

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            entities = [
                MedicalEntityResponse(
                    entity_id=uuid.uuid4(),
                    text=e.text,
                    entity_type=EntityTypeEnum(e.entity_type.value),
                    start=e.start,
                    end=e.end,
                    confidence=e.confidence,
                    negation_status=NegationStatusEnum(e.negation_status.value),
                    normalized_code=e.normalized_code,
                    code_system=e.code_system,
                    preferred_term=e.preferred_term,
                    attributes=e.attributes,
                )
                for e in result.entities
            ]

            relationships = [
                EntityRelationshipResponse(
                    relationship_id=uuid.uuid4(),
                    source_entity_id=uuid.uuid4(),  # Would map to actual entity IDs
                    target_entity_id=uuid.uuid4(),
                    relationship_type=r.relationship_type,
                    confidence=r.confidence,
                )
                for r in result.relationships
            ]

            entity_counts = {}
            for e in entities:
                entity_counts[e.entity_type.value] = entity_counts.get(e.entity_type.value, 0) + 1

            return EntityExtractionResponse(
                extraction_id=uuid.uuid4(),
                entities=entities,
                relationships=relationships,
                entity_counts=entity_counts,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Entity extraction error: {e}", exc_info=True)
            raise

    # ==================== Clinical Decision Support ====================

    async def get_clinical_decision_support(
        self,
        org_id: UUID,
        request: ClinicalDecisionRequest
    ) -> ClinicalDecisionResponse:
        """Get clinical decision support recommendations"""
        try:
            result = await clinical_decision_intelligence.analyze(
                conditions=request.conditions,
                medications=request.medications or [],
                lab_results=request.lab_results or {},
                vital_signs=request.vital_signs or {},
                symptoms=request.symptoms or [],
            )

            self._stats["decision_support_requests"] += 1

            guidelines = [
                GuidelineRecommendationResponse(
                    recommendation_id=uuid.uuid4(),
                    condition=g.condition,
                    guideline_source=g.guideline_source,
                    recommendation=g.recommendation,
                    evidence_level=g.evidence_level,
                    recommendation_grade=g.recommendation_grade,
                    monitoring_parameters=g.monitoring_parameters,
                    contraindications=g.contraindications,
                    citations=g.citations,
                )
                for g in result.guidelines
            ]

            interactions = [
                DrugInteractionResponse(
                    interaction_id=uuid.uuid4(),
                    drug_a=i.drug_a,
                    drug_b=i.drug_b,
                    severity=InteractionSeverityEnum(i.severity.value),
                    description=i.description,
                    mechanism=i.mechanism,
                    clinical_significance=i.clinical_significance,
                    management=i.management,
                    evidence_level=i.evidence_level,
                )
                for i in result.drug_interactions
            ]

            differentials = [
                DifferentialDiagnosisResponse(
                    diagnosis=d.diagnosis,
                    icd10_code=d.icd10_code,
                    probability=d.probability,
                    supporting_evidence=d.supporting_evidence,
                    contradicting_evidence=d.contradicting_evidence,
                    recommended_workup=d.recommended_workup,
                )
                for d in result.differential_diagnoses
            ]

            return ClinicalDecisionResponse(
                decision_id=uuid.uuid4(),
                guidelines=guidelines,
                drug_interactions=interactions,
                differential_diagnoses=differentials,
                treatment_recommendations=[asdict(t) for t in result.treatment_recommendations],
                alerts=result.alerts,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Clinical decision support error: {e}", exc_info=True)
            raise

    # ==================== Predictive Analytics ====================

    async def get_predictions(
        self,
        org_id: UUID,
        request: PredictiveAnalyticsRequest
    ) -> PredictiveAnalyticsResponse:
        """Get predictive analytics for patient"""
        try:
            self._stats["predictions"] += 1

            readmission_risk = None
            deterioration_alert = None
            no_show_prediction = None
            fall_risk = None

            if request.include_readmission and request.admission_data:
                result = await predictive_analytics_service.predict_readmission(
                    patient_id=str(request.patient_id),
                    admission_data=request.admission_data,
                )
                readmission_risk = ReadmissionRiskResponse(
                    risk_level=RiskLevelEnum(result.risk_level.value),
                    probability=result.probability,
                    lace_score=result.lace_score.total_score if result.lace_score else 0,
                    contributing_factors=result.contributing_factors,
                    interventions=result.interventions,
                    risk_factors=result.risk_factors,
                )

            if request.include_deterioration and request.vital_signs:
                result = await predictive_analytics_service.detect_deterioration(
                    patient_id=str(request.patient_id),
                    vital_signs=request.vital_signs,
                )
                deterioration_alert = DeteriorationAlertResponse(
                    risk_level=RiskLevelEnum(result.risk_level.value),
                    mews_score=result.mews_score.total_score if result.mews_score else 0,
                    probability=result.probability,
                    trigger_reasons=result.trigger_reasons,
                    recommended_actions=result.recommended_actions,
                    vital_sign_trends=result.vital_sign_trends,
                )

            if request.include_no_show and request.appointment_data:
                result = await predictive_analytics_service.predict_no_show(
                    patient_id=str(request.patient_id),
                    appointment_data=request.appointment_data,
                )
                no_show_prediction = NoShowPredictionResponse(
                    risk_level=RiskLevelEnum(result.risk_level.value),
                    probability=result.probability,
                    contributing_factors=result.contributing_factors,
                    recommendations=result.recommendations,
                )

            if request.include_fall_risk and request.mobility_data:
                result = await predictive_analytics_service.assess_fall_risk(
                    patient_id=str(request.patient_id),
                    mobility_data=request.mobility_data,
                )
                fall_risk = FallRiskResponse(
                    risk_level=RiskLevelEnum(result.risk_level.value),
                    morse_score=result.morse_score.total_score if result.morse_score else 0,
                    probability=result.probability,
                    risk_factors=result.risk_factors,
                    preventive_measures=result.preventive_measures,
                )

            # Generate overall summary
            risk_levels = []
            if readmission_risk:
                risk_levels.append(f"Readmission: {readmission_risk.risk_level.value}")
            if deterioration_alert:
                risk_levels.append(f"Deterioration: {deterioration_alert.risk_level.value}")
            if no_show_prediction:
                risk_levels.append(f"No-show: {no_show_prediction.risk_level.value}")
            if fall_risk:
                risk_levels.append(f"Fall: {fall_risk.risk_level.value}")

            overall_summary = "; ".join(risk_levels) if risk_levels else "No predictions requested"

            return PredictiveAnalyticsResponse(
                analysis_id=uuid.uuid4(),
                patient_id=request.patient_id,
                readmission_risk=readmission_risk,
                deterioration_alert=deterioration_alert,
                no_show_prediction=no_show_prediction,
                fall_risk=fall_risk,
                overall_risk_summary=overall_summary,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Predictive analytics error: {e}", exc_info=True)
            raise

    # ==================== Image Analysis ====================

    async def analyze_image(
        self,
        org_id: UUID,
        request: ImageAnalysisRequest
    ) -> ImageAnalysisResponse:
        """Analyze medical image"""
        start_time = datetime.utcnow()

        try:
            # Get image data
            image_data = None
            if request.image_base64:
                import base64
                image_data = base64.b64decode(request.image_base64)

            self._stats["image_analyses"] += 1

            chest_xray_result = None
            skin_lesion_result = None
            wound_result = None

            if request.image_type == ImageTypeEnum.CHEST_XRAY:
                result = await medical_image_analysis_service.analyze_chest_xray(
                    image_data=image_data,
                    image_url=request.image_url,
                    clinical_context=request.clinical_context,
                )
                findings = [
                    RadiologyFindingResponse(
                        finding=f.finding,
                        location=f.location,
                        confidence=f.confidence,
                        severity=f.severity,
                        measurements=f.measurements,
                        related_conditions=f.related_conditions,
                    )
                    for f in result.findings
                ]
                chest_xray_result = ChestXrayResponse(
                    findings=findings,
                    overall_impression=result.overall_impression,
                    recommendations=result.recommendations,
                    comparison_notes=result.comparison_notes,
                    critical_findings=result.critical_findings,
                )

            elif request.image_type == ImageTypeEnum.SKIN_LESION:
                result = await medical_image_analysis_service.analyze_skin_lesion(
                    image_data=image_data,
                    image_url=request.image_url,
                    clinical_context=request.clinical_context,
                )
                skin_lesion_result = SkinLesionResponse(
                    lesion_type=result.lesion_type,
                    malignancy_risk=result.malignancy_risk,
                    confidence=result.confidence,
                    abcde_scores=asdict(result.abcde_scores) if result.abcde_scores else {},
                    differential_diagnoses=result.differential_diagnoses,
                    recommendations=result.recommendations,
                    urgent_referral=result.urgent_referral,
                )

            elif request.image_type == ImageTypeEnum.WOUND:
                result = await medical_image_analysis_service.analyze_wound(
                    image_data=image_data,
                    image_url=request.image_url,
                    clinical_context=request.clinical_context,
                )
                wound_result = WoundAssessmentResponse(
                    wound_type=result.wound_type,
                    stage=result.stage,
                    tissue_composition=asdict(result.tissue_composition) if result.tissue_composition else {},
                    dimensions=result.dimensions,
                    infection_risk=result.infection_risk,
                    healing_trajectory=result.healing_trajectory,
                    treatment_recommendations=result.treatment_recommendations,
                )

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._stats["total_processing_time"] += processing_time

            return ImageAnalysisResponse(
                analysis_id=uuid.uuid4(),
                image_type=request.image_type,
                chest_xray_result=chest_xray_result,
                skin_lesion_result=skin_lesion_result,
                wound_result=wound_result,
                processing_time_ms=processing_time,
                model_version="medical-image-v1.0",
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Image analysis error: {e}", exc_info=True)
            raise

    # ==================== NLP Pipeline ====================

    async def run_nlp_pipeline(
        self,
        org_id: UUID,
        request: NLPPipelineRequest
    ) -> NLPPipelineResponse:
        """Run clinical NLP pipeline on text"""
        start_time = datetime.utcnow()

        try:
            result = await clinical_nlp_pipeline.process(
                text=request.text,
                document_type=request.document_type,
                include_sections=request.include_sections,
                include_problems=request.include_problems,
                include_medications=request.include_medications,
                include_sdoh=request.include_sdoh,
                include_quality_measures=request.include_quality_measures,
            )

            self._stats["nlp_pipeline_runs"] += 1

            sections = [
                ClinicalSectionResponse(
                    section_type=s.section_type,
                    title=s.title,
                    content=s.content,
                    start=s.start,
                    end=s.end,
                )
                for s in result.sections
            ]

            problems = [
                ProblemEntryResponse(
                    problem=p.problem,
                    icd10_code=p.icd10_code,
                    snomed_code=p.snomed_code,
                    status=p.status,
                    onset_date=p.onset_date,
                    evidence=p.evidence,
                )
                for p in result.problems
            ]

            medications = [
                MedicationEntryResponse(
                    medication=m.medication,
                    rxnorm_code=m.rxnorm_code,
                    dose=m.dose,
                    route=m.route,
                    frequency=m.frequency,
                    status=m.status,
                    indication=m.indication,
                )
                for m in result.medications
            ]

            sdoh = [
                SocialDeterminantResponse(
                    category=s.category,
                    description=s.description,
                    z_code=s.z_code,
                    impact_level=s.impact_level,
                    evidence=s.evidence,
                    interventions=s.interventions,
                )
                for s in result.social_determinants
            ]

            quality_measures = [
                QualityMeasureResponse(
                    measure_id=q.measure_id,
                    measure_name=q.measure_name,
                    applicable=q.applicable,
                    evidence=q.evidence,
                    numerator_eligible=q.numerator_eligible,
                    denominator_eligible=q.denominator_eligible,
                    gap_in_care=q.gap_in_care,
                    recommended_actions=q.recommended_actions,
                )
                for q in result.quality_measures
            ]

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._stats["total_processing_time"] += processing_time

            return NLPPipelineResponse(
                pipeline_id=uuid.uuid4(),
                sections=sections,
                problems=problems,
                medications=medications,
                social_determinants=sdoh,
                quality_measures=quality_measures,
                processing_time_ms=processing_time,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"NLP pipeline error: {e}", exc_info=True)
            raise

    # ==================== Voice Biomarkers ====================

    async def analyze_voice(
        self,
        org_id: UUID,
        request: VoiceBiomarkerRequest
    ) -> VoiceBiomarkerResponse:
        """Analyze voice biomarkers"""
        try:
            # Get audio data
            audio_data = None
            if request.audio_base64:
                import base64
                audio_data = base64.b64decode(request.audio_base64)

            result = await voice_biomarker_service.analyze(
                audio_data=audio_data,
                audio_url=request.audio_url,
                patient_id=str(request.patient_id) if request.patient_id else None,
                baseline_id=str(request.baseline_id) if request.baseline_id else None,
            )

            self._stats["voice_analyses"] += 1

            depression = None
            cognitive = None
            respiratory = None

            if request.include_depression and result.depression_assessment:
                d = result.depression_assessment
                depression = DepressionAssessmentResponse(
                    depression_risk=RiskLevelEnum(d.risk_level.value),
                    phq9_equivalent=d.phq9_equivalent,
                    confidence=d.confidence,
                    vocal_markers=d.vocal_markers,
                    trend=d.trend,
                    recommendations=d.recommendations,
                )

            if request.include_cognitive and result.cognitive_assessment:
                c = result.cognitive_assessment
                cognitive = CognitiveAssessmentResponse(
                    cognitive_risk=RiskLevelEnum(c.risk_level.value),
                    mci_risk_score=c.mci_risk_score,
                    confidence=c.confidence,
                    fluency_score=c.fluency_score,
                    word_finding_score=c.word_finding_score,
                    coherence_score=c.coherence_score,
                    concerns=c.concerns,
                    recommendations=c.recommendations,
                )

            if request.include_respiratory and result.respiratory_assessment:
                r = result.respiratory_assessment
                respiratory = RespiratoryAssessmentResponse(
                    respiratory_status=r.status,
                    breath_support_score=r.breath_support_score,
                    detected_patterns=r.detected_patterns,
                    severity=r.severity,
                    recommendations=r.recommendations,
                )

            return VoiceBiomarkerResponse(
                analysis_id=uuid.uuid4(),
                patient_id=request.patient_id,
                audio_features=asdict(result.audio_features) if result.audio_features else {},
                depression_assessment=depression,
                cognitive_assessment=cognitive,
                respiratory_assessment=respiratory,
                baseline_comparison=result.baseline_comparison,
                overall_summary=result.overall_summary,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Voice biomarker analysis error: {e}", exc_info=True)
            raise

    # ==================== Statistics ====================

    def get_statistics(self, org_id: UUID) -> MedicalAIStatistics:
        """Get medical AI usage statistics"""
        total_requests = sum([
            self._stats["triage_requests"],
            self._stats["documentation_requests"],
            self._stats["entity_extractions"],
            self._stats["decision_support_requests"],
            self._stats["predictions"],
            self._stats["image_analyses"],
            self._stats["nlp_pipeline_runs"],
            self._stats["voice_analyses"],
        ])

        avg_confidence = 0.0
        if self._stats["triage_requests"] > 0:
            avg_confidence = self._stats["total_confidence"] / self._stats["triage_requests"]

        avg_processing_time = 0.0
        processing_count = (
            self._stats["image_analyses"] + self._stats["nlp_pipeline_runs"]
        )
        if processing_count > 0:
            avg_processing_time = self._stats["total_processing_time"] / processing_count

        red_flag_rate = 0.0
        if self._stats["triage_requests"] > 0:
            red_flag_rate = self._stats["red_flag_count"] / self._stats["triage_requests"]

        return MedicalAIStatistics(
            total_triage_requests=self._stats["triage_requests"],
            total_documentation_requests=self._stats["documentation_requests"],
            total_entity_extractions=self._stats["entity_extractions"],
            total_decision_support_requests=self._stats["decision_support_requests"],
            total_predictions=self._stats["predictions"],
            total_image_analyses=self._stats["image_analyses"],
            total_nlp_pipeline_runs=self._stats["nlp_pipeline_runs"],
            total_voice_analyses=self._stats["voice_analyses"],
            average_triage_confidence=avg_confidence,
            average_processing_time_ms=avg_processing_time,
            red_flag_detection_rate=red_flag_rate,
            model_versions={
                "triage": "triage-v1.0",
                "documentation": "doc-ai-v1.0",
                "entity_recognition": "ner-v1.0",
                "decision_support": "cds-v1.0",
                "predictive": "pred-v1.0",
                "image_analysis": "image-v1.0",
                "nlp_pipeline": "nlp-v1.0",
                "voice_biomarkers": "voice-v1.0",
            },
        )

    def health_check(self) -> MedicalAIHealthCheck:
        """Health check for medical AI module"""
        return MedicalAIHealthCheck(
            status="healthy",
            module="medical_ai",
            features=[
                "triage",
                "documentation_ai",
                "entity_recognition",
                "decision_support",
                "predictive_analytics",
                "image_analysis",
                "nlp_pipeline",
                "voice_biomarkers",
            ],
            model_status={
                "triage_engine": "ready",
                "documentation_ai": "ready",
                "entity_extractor": "ready",
                "decision_intelligence": "ready",
                "predictive_service": "ready",
                "image_analyzer": "ready",
                "nlp_pipeline": "ready",
                "voice_analyzer": "ready",
            },
            last_calibration=datetime.utcnow(),
        )
