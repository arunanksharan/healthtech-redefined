"""
Clinical Guideline Service

Provides guideline content management, context-aware recommendations,
and integration with external knowledge bases.

EPIC-020: Clinical Decision Support
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from modules.cds.models import (
    ClinicalGuideline,
    GuidelineAccess,
    GuidelineCategory,
    GuidelineSource,
)
from modules.cds.schemas import (
    GuidelineCreate,
    GuidelineUpdate,
    GuidelineResponse,
    GuidelineSearchRequest,
    GuidelineRecommendation,
)


class GuidelineService:
    """Service for clinical guideline management and recommendations."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create_guideline(
        self,
        data: GuidelineCreate,
    ) -> ClinicalGuideline:
        """Create a new clinical guideline."""
        guideline = ClinicalGuideline(
            tenant_id=self.tenant_id,
            external_id=data.external_id,
            title=data.title,
            short_title=data.short_title,
            category=data.category,
            source=data.source,
            publisher=data.publisher,
            conditions=data.conditions,
            condition_names=data.condition_names,
            summary=data.summary,
            key_recommendations=data.key_recommendations,
            full_content=data.full_content,
            content_url=data.content_url,
            evidence_grade=data.evidence_grade,
            recommendation_strength=data.recommendation_strength,
            references=data.references,
            patient_population=data.patient_population,
            age_min=data.age_min,
            age_max=data.age_max,
            gender=data.gender,
            version=data.version,
            published_date=data.published_date,
        )
        self.db.add(guideline)
        await self.db.flush()
        return guideline

    async def get_guideline(self, guideline_id: UUID) -> Optional[ClinicalGuideline]:
        """Get a guideline by ID."""
        query = select(ClinicalGuideline).where(
            and_(
                ClinicalGuideline.id == guideline_id,
                ClinicalGuideline.tenant_id == self.tenant_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_guideline(
        self,
        guideline_id: UUID,
        data: GuidelineUpdate,
    ) -> Optional[ClinicalGuideline]:
        """Update a guideline."""
        guideline = await self.get_guideline(guideline_id)
        if not guideline:
            return None

        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(guideline, key):
                setattr(guideline, key, value)

        await self.db.flush()
        return guideline

    async def list_guidelines(
        self,
        category: Optional[GuidelineCategory] = None,
        source: Optional[GuidelineSource] = None,
        condition: Optional[str] = None,
        is_active: bool = True,
        is_featured: bool = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ClinicalGuideline]:
        """List guidelines with optional filters."""
        query = select(ClinicalGuideline).where(
            and_(
                ClinicalGuideline.tenant_id == self.tenant_id,
                ClinicalGuideline.is_active == is_active,
            )
        )

        if category:
            query = query.where(ClinicalGuideline.category == category)

        if source:
            query = query.where(ClinicalGuideline.source == source)

        if condition:
            query = query.where(ClinicalGuideline.conditions.contains([condition]))

        if is_featured is not None:
            query = query.where(ClinicalGuideline.is_featured == is_featured)

        query = query.order_by(ClinicalGuideline.view_count.desc())
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_guidelines(
        self,
        request: GuidelineSearchRequest,
    ) -> List[ClinicalGuideline]:
        """Search guidelines by query and filters."""
        query = select(ClinicalGuideline).where(
            and_(
                ClinicalGuideline.tenant_id == self.tenant_id,
                ClinicalGuideline.is_active == True,
            )
        )

        # Text search
        if request.query:
            search_term = f"%{request.query}%"
            query = query.where(
                or_(
                    ClinicalGuideline.title.ilike(search_term),
                    ClinicalGuideline.summary.ilike(search_term),
                    ClinicalGuideline.full_content.ilike(search_term),
                )
            )

        # Filter by conditions
        if request.conditions:
            condition_filters = [
                ClinicalGuideline.conditions.contains([cond])
                for cond in request.conditions
            ]
            query = query.where(or_(*condition_filters))

        # Filter by categories
        if request.categories:
            query = query.where(ClinicalGuideline.category.in_(request.categories))

        # Filter by sources
        if request.sources:
            query = query.where(ClinicalGuideline.source.in_(request.sources))

        # Filter by patient demographics
        if request.patient_age is not None:
            query = query.where(
                or_(
                    ClinicalGuideline.age_min.is_(None),
                    ClinicalGuideline.age_min <= request.patient_age,
                )
            ).where(
                or_(
                    ClinicalGuideline.age_max.is_(None),
                    ClinicalGuideline.age_max >= request.patient_age,
                )
            )

        if request.patient_gender:
            query = query.where(
                or_(
                    ClinicalGuideline.gender.is_(None),
                    ClinicalGuideline.gender == "all",
                    ClinicalGuideline.gender == request.patient_gender,
                )
            )

        query = query.limit(request.limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recommendations_for_context(
        self,
        patient_conditions: List[str],
        patient_age: Optional[int] = None,
        patient_gender: Optional[str] = None,
        encounter_type: Optional[str] = None,
        max_recommendations: int = 5,
    ) -> List[GuidelineRecommendation]:
        """Get guideline recommendations based on patient context."""
        recommendations = []

        # Search for guidelines matching patient conditions
        search_request = GuidelineSearchRequest(
            conditions=patient_conditions,
            patient_age=patient_age,
            patient_gender=patient_gender,
            limit=max_recommendations * 2,  # Get extra for scoring
        )

        guidelines = await self.search_guidelines(search_request)

        for guideline in guidelines:
            # Calculate relevance score
            matched_conditions = [
                cond for cond in patient_conditions
                if cond in (guideline.conditions or [])
            ]
            relevance_score = len(matched_conditions) / max(len(patient_conditions), 1)

            # Boost score for evidence grade
            if guideline.evidence_grade == "A":
                relevance_score *= 1.3
            elif guideline.evidence_grade == "B":
                relevance_score *= 1.15

            # Boost featured guidelines
            if guideline.is_featured:
                relevance_score *= 1.1

            recommendations.append(GuidelineRecommendation(
                guideline=GuidelineResponse.from_orm(guideline),
                relevance_score=min(relevance_score, 1.0),
                matched_conditions=matched_conditions,
                reason=self._generate_recommendation_reason(
                    guideline, matched_conditions
                ),
            ))

        # Sort by relevance and limit
        recommendations.sort(key=lambda r: r.relevance_score, reverse=True)
        return recommendations[:max_recommendations]

    def _generate_recommendation_reason(
        self,
        guideline: ClinicalGuideline,
        matched_conditions: List[str],
    ) -> str:
        """Generate human-readable recommendation reason."""
        if matched_conditions:
            condition_names = []
            for code in matched_conditions:
                idx = (guideline.conditions or []).index(code) if code in (guideline.conditions or []) else -1
                if idx >= 0 and idx < len(guideline.condition_names or []):
                    condition_names.append(guideline.condition_names[idx])
                else:
                    condition_names.append(code)

            return f"Relevant to patient's conditions: {', '.join(condition_names)}"

        return f"General guideline for {guideline.category.value}"

    async def log_access(
        self,
        guideline_id: UUID,
        provider_id: UUID,
        patient_id: Optional[UUID] = None,
        encounter_id: Optional[UUID] = None,
        access_context: Optional[str] = None,
        search_query: Optional[str] = None,
        was_recommended: bool = False,
    ) -> GuidelineAccess:
        """Log guideline access for analytics."""
        access_log = GuidelineAccess(
            tenant_id=self.tenant_id,
            guideline_id=guideline_id,
            provider_id=provider_id,
            patient_id=patient_id,
            encounter_id=encounter_id,
            access_context=access_context,
            search_query=search_query,
            was_recommended=was_recommended,
        )
        self.db.add(access_log)

        # Increment view count
        guideline = await self.get_guideline(guideline_id)
        if guideline:
            guideline.view_count = (guideline.view_count or 0) + 1

        await self.db.flush()
        return access_log

    async def update_access_feedback(
        self,
        access_id: UUID,
        time_spent_seconds: Optional[int] = None,
        sections_viewed: Optional[List[str]] = None,
        was_helpful: Optional[bool] = None,
        feedback: Optional[str] = None,
    ) -> Optional[GuidelineAccess]:
        """Update access record with feedback."""
        query = select(GuidelineAccess).where(
            and_(
                GuidelineAccess.id == access_id,
                GuidelineAccess.tenant_id == self.tenant_id,
            )
        )
        result = await self.db.execute(query)
        access_log = result.scalar_one_or_none()

        if access_log:
            if time_spent_seconds is not None:
                access_log.time_spent_seconds = time_spent_seconds
            if sections_viewed is not None:
                access_log.sections_viewed = sections_viewed
            if was_helpful is not None:
                access_log.was_helpful = was_helpful
            if feedback is not None:
                access_log.feedback = feedback

            # Update guideline usefulness rating
            if was_helpful is not None:
                await self._update_guideline_rating(access_log.guideline_id)

            await self.db.flush()

        return access_log

    async def _update_guideline_rating(self, guideline_id: UUID):
        """Update guideline usefulness rating based on feedback."""
        query = select(
            func.avg(func.cast(GuidelineAccess.was_helpful, Integer))
        ).where(
            and_(
                GuidelineAccess.guideline_id == guideline_id,
                GuidelineAccess.was_helpful.isnot(None),
            )
        )

        result = await self.db.execute(query)
        avg_rating = result.scalar_one_or_none()

        if avg_rating is not None:
            guideline = await self.get_guideline(guideline_id)
            if guideline:
                guideline.usefulness_rating = float(avg_rating) * 5  # Convert to 0-5 scale

    async def import_guidelines_from_source(
        self,
        source: GuidelineSource,
        guidelines_data: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """Import guidelines from external source."""
        imported = 0
        updated = 0
        errors = 0

        for data in guidelines_data:
            try:
                external_id = data.get("external_id")

                # Check if guideline already exists
                existing = None
                if external_id:
                    query = select(ClinicalGuideline).where(
                        and_(
                            ClinicalGuideline.tenant_id == self.tenant_id,
                            ClinicalGuideline.external_id == external_id,
                            ClinicalGuideline.source == source,
                        )
                    )
                    result = await self.db.execute(query)
                    existing = result.scalar_one_or_none()

                if existing:
                    # Update existing guideline
                    for key, value in data.items():
                        if hasattr(existing, key) and value is not None:
                            setattr(existing, key, value)
                    updated += 1
                else:
                    # Create new guideline
                    guideline = ClinicalGuideline(
                        tenant_id=self.tenant_id,
                        source=source,
                        **data,
                    )
                    self.db.add(guideline)
                    imported += 1

            except Exception as e:
                errors += 1

        await self.db.flush()

        return {
            "imported": imported,
            "updated": updated,
            "errors": errors,
        }

    async def get_guideline_analytics(
        self,
        guideline_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get guideline usage analytics."""
        query = select(GuidelineAccess).where(
            GuidelineAccess.tenant_id == self.tenant_id
        )

        if guideline_id:
            query = query.where(GuidelineAccess.guideline_id == guideline_id)

        if start_date:
            query = query.where(GuidelineAccess.accessed_at >= datetime.combine(start_date, datetime.min.time()))

        if end_date:
            query = query.where(GuidelineAccess.accessed_at <= datetime.combine(end_date, datetime.max.time()))

        result = await self.db.execute(query)
        access_logs = result.scalars().all()

        total_views = len(access_logs)
        unique_providers = len(set(log.provider_id for log in access_logs))
        unique_patients = len(set(log.patient_id for log in access_logs if log.patient_id))

        helpful_count = sum(1 for log in access_logs if log.was_helpful is True)
        not_helpful_count = sum(1 for log in access_logs if log.was_helpful is False)
        feedback_count = helpful_count + not_helpful_count

        return {
            "total_views": total_views,
            "unique_providers": unique_providers,
            "unique_patients": unique_patients,
            "helpful_rate": helpful_count / feedback_count if feedback_count > 0 else None,
            "avg_time_spent": sum(log.time_spent_seconds or 0 for log in access_logs) / total_views if total_views > 0 else 0,
        }
