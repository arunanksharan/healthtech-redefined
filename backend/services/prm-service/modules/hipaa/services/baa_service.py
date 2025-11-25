"""
Business Associate Agreement (BAA) Management Service

BAA tracking, template management, and compliance reporting for HIPAA.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from modules.hipaa.models import (
    BusinessAssociateAgreement,
    BAAAmendment,
    BAATemplate,
    BAAType,
    BAAStatus,
)


class BAAService:
    """
    Service for HIPAA Business Associate Agreement management.

    Features:
    - BAA template library
    - Vendor and customer BAA tracking
    - E-signature integration support
    - Expiration alerting and renewal workflow
    - Subcontractor BAA chain tracking
    - Compliance reporting
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # BAA Management
    # =========================================================================

    async def create_baa(
        self,
        baa_type: BAAType,
        counterparty_name: str,
        counterparty_type: str,
        services_description: str,
        phi_categories_covered: List[str],
        counterparty_address: Optional[str] = None,
        counterparty_contact_name: Optional[str] = None,
        counterparty_contact_email: Optional[str] = None,
        counterparty_contact_phone: Optional[str] = None,
        template_used: Optional[str] = None,
        effective_date: Optional[date] = None,
        expiration_date: Optional[date] = None,
        auto_renew: bool = False,
        renewal_term_months: Optional[int] = None,
        parent_baa_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None,
    ) -> BusinessAssociateAgreement:
        """Create a new BAA."""
        baa_number = f"BAA-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

        baa = BusinessAssociateAgreement(
            tenant_id=self.tenant_id,
            baa_number=baa_number,
            baa_type=baa_type,
            counterparty_name=counterparty_name,
            counterparty_type=counterparty_type,
            counterparty_address=counterparty_address,
            counterparty_contact_name=counterparty_contact_name,
            counterparty_contact_email=counterparty_contact_email,
            counterparty_contact_phone=counterparty_contact_phone,
            services_description=services_description,
            phi_categories_covered=phi_categories_covered,
            status=BAAStatus.DRAFT,
            template_used=template_used,
            effective_date=effective_date,
            expiration_date=expiration_date,
            auto_renew=auto_renew,
            renewal_term_months=renewal_term_months,
            parent_baa_id=parent_baa_id,
            created_by=created_by,
        )

        self.db.add(baa)
        await self.db.commit()
        await self.db.refresh(baa)

        return baa

    async def get_baa(self, baa_id: UUID) -> Optional[BusinessAssociateAgreement]:
        """Get BAA by ID."""
        query = select(BusinessAssociateAgreement).where(
            and_(
                BusinessAssociateAgreement.id == baa_id,
                BusinessAssociateAgreement.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_baa_status(
        self,
        baa_id: UUID,
        status: BAAStatus,
    ) -> Optional[BusinessAssociateAgreement]:
        """Update BAA status."""
        baa = await self.get_baa(baa_id)
        if baa:
            baa.status = status
            baa.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(baa)
        return baa

    async def execute_baa(
        self,
        baa_id: UUID,
        our_signatory_name: str,
        our_signatory_title: str,
        counterparty_signatory_name: str,
        counterparty_signatory_title: str,
        execution_date: date,
        effective_date: date,
        document_url: Optional[str] = None,
        document_hash: Optional[str] = None,
    ) -> Optional[BusinessAssociateAgreement]:
        """Execute (sign) a BAA."""
        baa = await self.get_baa(baa_id)
        if baa:
            baa.status = BAAStatus.EXECUTED
            baa.our_signatory_name = our_signatory_name
            baa.our_signatory_title = our_signatory_title
            baa.our_signature_date = execution_date
            baa.counterparty_signatory_name = counterparty_signatory_name
            baa.counterparty_signatory_title = counterparty_signatory_title
            baa.counterparty_signature_date = execution_date
            baa.execution_date = execution_date
            baa.effective_date = effective_date
            if document_url:
                baa.document_url = document_url
            if document_hash:
                baa.document_hash = document_hash
            baa.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(baa)

        return baa

    async def terminate_baa(
        self,
        baa_id: UUID,
        termination_date: date,
        termination_reason: str,
    ) -> Optional[BusinessAssociateAgreement]:
        """Terminate a BAA."""
        baa = await self.get_baa(baa_id)
        if baa:
            baa.status = BAAStatus.TERMINATED
            baa.terminated = True
            baa.termination_date = termination_date
            baa.termination_reason = termination_reason
            baa.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(baa)

        return baa

    async def renew_baa(
        self,
        baa_id: UUID,
        new_expiration_date: date,
    ) -> Optional[BusinessAssociateAgreement]:
        """Renew a BAA by extending expiration date."""
        baa = await self.get_baa(baa_id)
        if baa:
            baa.expiration_date = new_expiration_date
            baa.status = BAAStatus.EXECUTED
            baa.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(baa)

        return baa

    async def list_baas(
        self,
        baa_type: Optional[BAAType] = None,
        status: Optional[BAAStatus] = None,
        counterparty_name: Optional[str] = None,
    ) -> List[BusinessAssociateAgreement]:
        """List BAAs with filtering."""
        query = select(BusinessAssociateAgreement).where(
            BusinessAssociateAgreement.tenant_id == self.tenant_id
        )

        if baa_type:
            query = query.where(BusinessAssociateAgreement.baa_type == baa_type)
        if status:
            query = query.where(BusinessAssociateAgreement.status == status)
        if counterparty_name:
            query = query.where(
                BusinessAssociateAgreement.counterparty_name.ilike(f"%{counterparty_name}%")
            )

        query = query.order_by(BusinessAssociateAgreement.counterparty_name)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_expiring_baas(
        self,
        days_ahead: int = 90,
    ) -> List[BusinessAssociateAgreement]:
        """Get BAAs expiring within specified days."""
        expiration_threshold = date.today() + timedelta(days=days_ahead)

        query = select(BusinessAssociateAgreement).where(
            and_(
                BusinessAssociateAgreement.tenant_id == self.tenant_id,
                BusinessAssociateAgreement.status == BAAStatus.EXECUTED,
                BusinessAssociateAgreement.expiration_date.isnot(None),
                BusinessAssociateAgreement.expiration_date <= expiration_threshold,
                BusinessAssociateAgreement.terminated == False
            )
        ).order_by(BusinessAssociateAgreement.expiration_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_subcontractor_chain(
        self,
        baa_id: UUID,
    ) -> List[BusinessAssociateAgreement]:
        """Get the chain of subcontractor BAAs under a parent BAA."""
        chain = []
        current_id = baa_id

        # Get direct children (subcontractors)
        query = select(BusinessAssociateAgreement).where(
            and_(
                BusinessAssociateAgreement.tenant_id == self.tenant_id,
                BusinessAssociateAgreement.parent_baa_id == current_id
            )
        )
        result = await self.db.execute(query)
        children = list(result.scalars().all())

        for child in children:
            chain.append(child)
            # Recursively get subcontractor chains
            sub_chain = await self.get_subcontractor_chain(child.id)
            chain.extend(sub_chain)

        return chain

    # =========================================================================
    # BAA Amendments
    # =========================================================================

    async def create_amendment(
        self,
        baa_id: UUID,
        description: str,
        changes_summary: str,
        effective_date: date,
        document_url: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> BAAAmendment:
        """Create a BAA amendment."""
        # Get next amendment number
        query = select(func.count()).select_from(BAAAmendment).where(
            BAAAmendment.baa_id == baa_id
        )
        result = await self.db.execute(query)
        amendment_count = result.scalar()

        amendment = BAAAmendment(
            tenant_id=self.tenant_id,
            baa_id=baa_id,
            amendment_number=amendment_count + 1,
            description=description,
            changes_summary=changes_summary,
            effective_date=effective_date,
            document_url=document_url,
            created_by=created_by,
        )

        self.db.add(amendment)
        await self.db.commit()
        await self.db.refresh(amendment)

        return amendment

    async def execute_amendment(
        self,
        amendment_id: UUID,
        execution_date: date,
    ) -> Optional[BAAAmendment]:
        """Execute (sign) a BAA amendment."""
        query = select(BAAAmendment).where(
            and_(
                BAAAmendment.id == amendment_id,
                BAAAmendment.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        amendment = result.scalar_one_or_none()

        if amendment:
            amendment.executed = True
            amendment.execution_date = execution_date

            await self.db.commit()
            await self.db.refresh(amendment)

        return amendment

    async def list_amendments(
        self,
        baa_id: UUID,
    ) -> List[BAAAmendment]:
        """List all amendments for a BAA."""
        query = select(BAAAmendment).where(
            and_(
                BAAAmendment.tenant_id == self.tenant_id,
                BAAAmendment.baa_id == baa_id
            )
        ).order_by(BAAAmendment.amendment_number)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # BAA Templates
    # =========================================================================

    async def create_template(
        self,
        name: str,
        template_type: BAAType,
        template_content: str,
        version: str,
        description: Optional[str] = None,
        variable_fields: Optional[Dict[str, Any]] = None,
        is_default: bool = False,
        created_by: Optional[UUID] = None,
    ) -> BAATemplate:
        """Create a BAA template."""
        if is_default:
            # Clear existing default for this type
            query = select(BAATemplate).where(
                and_(
                    BAATemplate.tenant_id == self.tenant_id,
                    BAATemplate.template_type == template_type,
                    BAATemplate.is_default == True
                )
            )
            result = await self.db.execute(query)
            existing_default = result.scalar_one_or_none()
            if existing_default:
                existing_default.is_default = False

        template = BAATemplate(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            template_type=template_type,
            template_content=template_content,
            variable_fields=variable_fields,
            version=version,
            is_default=is_default,
            created_by=created_by,
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        return template

    async def get_template(
        self,
        template_id: UUID,
    ) -> Optional[BAATemplate]:
        """Get BAA template by ID."""
        query = select(BAATemplate).where(
            and_(
                BAATemplate.id == template_id,
                BAATemplate.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_default_template(
        self,
        template_type: BAAType,
    ) -> Optional[BAATemplate]:
        """Get the default template for a BAA type."""
        query = select(BAATemplate).where(
            and_(
                BAATemplate.tenant_id == self.tenant_id,
                BAATemplate.template_type == template_type,
                BAATemplate.is_default == True,
                BAATemplate.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def approve_template(
        self,
        template_id: UUID,
        approved_by: UUID,
        legal_review_date: date,
    ) -> Optional[BAATemplate]:
        """Approve a BAA template after legal review."""
        template = await self.get_template(template_id)
        if template:
            template.approved = True
            template.approved_by = approved_by
            template.approved_at = datetime.utcnow()
            template.legal_review_date = legal_review_date
            template.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(template)

        return template

    async def list_templates(
        self,
        template_type: Optional[BAAType] = None,
        active_only: bool = True,
        approved_only: bool = False,
    ) -> List[BAATemplate]:
        """List BAA templates."""
        query = select(BAATemplate).where(
            BAATemplate.tenant_id == self.tenant_id
        )

        if template_type:
            query = query.where(BAATemplate.template_type == template_type)
        if active_only:
            query = query.where(BAATemplate.is_active == True)
        if approved_only:
            query = query.where(BAATemplate.approved == True)

        query = query.order_by(BAATemplate.template_type, BAATemplate.name)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def render_template(
        self,
        template_id: UUID,
        variables: Dict[str, Any],
    ) -> str:
        """Render a BAA template with provided variables."""
        template = await self.get_template(template_id)
        if not template:
            raise ValueError("Template not found")

        content = template.template_content

        # Simple variable substitution
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"  # {{variable_name}}
            content = content.replace(placeholder, str(value))

        return content

    # =========================================================================
    # BAA Compliance Reporting
    # =========================================================================

    async def get_baa_compliance_report(self) -> Dict[str, Any]:
        """Generate BAA compliance report."""
        # Total BAAs
        total_query = select(func.count()).select_from(BusinessAssociateAgreement).where(
            and_(
                BusinessAssociateAgreement.tenant_id == self.tenant_id,
                BusinessAssociateAgreement.terminated == False
            )
        )
        total_result = await self.db.execute(total_query)
        total_baas = total_result.scalar()

        # By status
        status_query = (
            select(BusinessAssociateAgreement.status, func.count(BusinessAssociateAgreement.id))
            .where(
                and_(
                    BusinessAssociateAgreement.tenant_id == self.tenant_id,
                    BusinessAssociateAgreement.terminated == False
                )
            )
            .group_by(BusinessAssociateAgreement.status)
        )
        status_result = await self.db.execute(status_query)
        by_status = {row[0].value: row[1] for row in status_result.all()}

        # By type
        type_query = (
            select(BusinessAssociateAgreement.baa_type, func.count(BusinessAssociateAgreement.id))
            .where(
                and_(
                    BusinessAssociateAgreement.tenant_id == self.tenant_id,
                    BusinessAssociateAgreement.terminated == False
                )
            )
            .group_by(BusinessAssociateAgreement.baa_type)
        )
        type_result = await self.db.execute(type_query)
        by_type = {row[0].value: row[1] for row in type_result.all()}

        # Expiring soon
        expiring = await self.get_expiring_baas(90)

        # Pending signatures
        pending_query = select(func.count()).select_from(BusinessAssociateAgreement).where(
            and_(
                BusinessAssociateAgreement.tenant_id == self.tenant_id,
                BusinessAssociateAgreement.status.in_([
                    BAAStatus.DRAFT,
                    BAAStatus.NEGOTIATING,
                    BAAStatus.PENDING_SIGNATURE,
                ])
            )
        )
        pending_result = await self.db.execute(pending_query)
        pending_count = pending_result.scalar()

        return {
            "total_active_baas": total_baas,
            "by_status": by_status,
            "by_type": by_type,
            "expiring_within_90_days": len(expiring),
            "expiring_baas": [
                {
                    "baa_number": baa.baa_number,
                    "counterparty": baa.counterparty_name,
                    "expiration_date": baa.expiration_date.isoformat(),
                    "auto_renew": baa.auto_renew,
                }
                for baa in expiring
            ],
            "pending_signatures": pending_count,
        }

    async def check_vendor_baa_coverage(
        self,
        vendor_name: str,
    ) -> Tuple[bool, Optional[BusinessAssociateAgreement]]:
        """Check if a vendor has an executed BAA."""
        query = select(BusinessAssociateAgreement).where(
            and_(
                BusinessAssociateAgreement.tenant_id == self.tenant_id,
                BusinessAssociateAgreement.counterparty_name.ilike(f"%{vendor_name}%"),
                BusinessAssociateAgreement.baa_type == BAAType.VENDOR,
                BusinessAssociateAgreement.status == BAAStatus.EXECUTED,
                BusinessAssociateAgreement.terminated == False,
                or_(
                    BusinessAssociateAgreement.expiration_date.is_(None),
                    BusinessAssociateAgreement.expiration_date >= date.today()
                )
            )
        )
        result = await self.db.execute(query)
        baa = result.scalar_one_or_none()

        return (baa is not None, baa)

    async def get_vendors_without_baa(
        self,
        vendor_list: List[str],
    ) -> List[str]:
        """Check which vendors in a list don't have BAA coverage."""
        uncovered = []
        for vendor in vendor_list:
            has_baa, _ = await self.check_vendor_baa_coverage(vendor)
            if not has_baa:
                uncovered.append(vendor)
        return uncovered
