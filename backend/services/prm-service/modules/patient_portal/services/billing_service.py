"""
Patient Portal Billing Service
EPIC-014: Billing, payments, and payment plan management
"""
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc

from modules.patient_portal.models import (
    PortalUser, PortalPayment, SavedPaymentMethod, PaymentPlan,
    PortalAuditLog, AuditAction, PaymentMethod, PaymentStatus
)
from modules.patient_portal.schemas import (
    BillingSummaryResponse, BillingStatementResponse,
    PaymentMethodCreate, PaymentMethodResponse,
    PaymentRequest, PaymentResponse,
    PaymentPlanRequest, PaymentPlanResponse,
    PaymentHistoryResponse, PaymentStatusEnum, PaymentMethodEnum
)


class BillingService:
    """
    Handles all billing operations for the patient portal including:
    - Billing statements and summary
    - Payment method management
    - Payment processing
    - Payment plans
    - Payment history
    """

    def __init__(self):
        # In production, these would come from config/env
        self.payment_processor = "stripe"  # Could also be "square"

    # ==================== Billing Summary ====================

    async def get_billing_summary(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        patient_id: UUID = None
    ) -> BillingSummaryResponse:
        """Get billing summary for patient"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        target_patient_id = patient_id or user.patient_id

        # Get current balance from billing system
        # This would integrate with the billing module (EPIC-008)
        balance = await self._get_patient_balance(db, tenant_id, target_patient_id)

        # Get recent statements
        statements = await self._get_recent_statements(db, tenant_id, target_patient_id)

        # Get last payment
        last_payment = await self._get_last_payment(db, target_patient_id)

        # Check for active payment plan
        result = await db.execute(
            select(PaymentPlan).where(
                and_(
                    PaymentPlan.patient_id == target_patient_id,
                    PaymentPlan.is_active == True
                )
            )
        )
        payment_plan = result.scalar_one_or_none()

        return BillingSummaryResponse(
            current_balance=balance.get('current_balance', 0),
            total_due=balance.get('total_due', 0),
            past_due_amount=balance.get('past_due', 0),
            last_payment_date=last_payment.get('date') if last_payment else None,
            last_payment_amount=last_payment.get('amount') if last_payment else None,
            payment_plan_active=payment_plan is not None,
            statements=statements
        )

    async def _get_patient_balance(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID
    ) -> Dict:
        """Get patient balance from billing system"""
        # Would integrate with billing module
        return {
            'current_balance': 0.0,
            'total_due': 0.0,
            'past_due': 0.0
        }

    async def _get_recent_statements(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        limit: int = 6
    ) -> List[BillingStatementResponse]:
        """Get recent billing statements"""
        # Would integrate with billing module
        return []

    async def _get_last_payment(
        self,
        db: AsyncSession,
        patient_id: UUID
    ) -> Optional[Dict]:
        """Get last successful payment"""
        result = await db.execute(
            select(PortalPayment).where(
                and_(
                    PortalPayment.patient_id == patient_id,
                    PortalPayment.status == PaymentStatus.COMPLETED
                )
            ).order_by(desc(PortalPayment.completed_at)).limit(1)
        )
        payment = result.scalar_one_or_none()

        if payment:
            return {
                'date': payment.completed_at.date(),
                'amount': float(payment.amount)
            }
        return None

    # ==================== Payment Methods ====================

    async def get_payment_methods(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> List[PaymentMethodResponse]:
        """Get saved payment methods for user"""

        result = await db.execute(
            select(SavedPaymentMethod).where(
                and_(
                    SavedPaymentMethod.user_id == user_id,
                    SavedPaymentMethod.is_active == True
                )
            ).order_by(desc(SavedPaymentMethod.is_default), SavedPaymentMethod.created_at)
        )
        methods = result.scalars().all()

        return [
            PaymentMethodResponse(
                id=m.id,
                payment_type=PaymentMethodEnum(m.payment_type.value),
                nickname=m.nickname,
                is_default=m.is_default,
                card_brand=m.card_brand,
                card_last_four=m.card_last_four,
                card_exp_month=m.card_exp_month,
                card_exp_year=m.card_exp_year,
                bank_name=m.bank_name,
                account_type=m.account_type,
                account_last_four=m.account_last_four,
                is_active=m.is_active,
                is_verified=m.is_verified,
                created_at=m.created_at,
                updated_at=m.updated_at
            )
            for m in methods
        ]

    async def add_payment_method(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        request: PaymentMethodCreate
    ) -> PaymentMethodResponse:
        """Add new payment method"""

        # If setting as default, unset other defaults
        if request.is_default:
            await db.execute(
                update(SavedPaymentMethod).where(
                    and_(
                        SavedPaymentMethod.user_id == user_id,
                        SavedPaymentMethod.is_default == True
                    )
                ).values(is_default=False)
            )

        # Create payment method
        method = SavedPaymentMethod(
            id=uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
            payment_type=PaymentMethod(request.payment_type.value),
            nickname=request.nickname,
            is_default=request.is_default,

            # Card details
            card_brand=request.card_brand,
            card_last_four=request.card_last_four,
            card_exp_month=request.card_exp_month,
            card_exp_year=request.card_exp_year,
            card_holder_name=request.card_holder_name,

            # Bank details
            bank_name=request.bank_name,
            account_type=request.account_type,
            account_last_four=request.account_last_four,

            # Processor token
            processor=self.payment_processor,
            processor_token=request.card_token or request.bank_token,

            # Billing address
            billing_address=request.billing_address,

            # Status
            is_active=True,
            is_verified=True  # Token already verified by processor
        )
        db.add(method)
        await db.commit()

        return PaymentMethodResponse(
            id=method.id,
            payment_type=PaymentMethodEnum(method.payment_type.value),
            nickname=method.nickname,
            is_default=method.is_default,
            card_brand=method.card_brand,
            card_last_four=method.card_last_four,
            card_exp_month=method.card_exp_month,
            card_exp_year=method.card_exp_year,
            bank_name=method.bank_name,
            account_type=method.account_type,
            account_last_four=method.account_last_four,
            is_active=method.is_active,
            is_verified=method.is_verified,
            created_at=method.created_at,
            updated_at=method.updated_at
        )

    async def delete_payment_method(
        self,
        db: AsyncSession,
        user_id: UUID,
        method_id: UUID
    ):
        """Delete (deactivate) payment method"""

        result = await db.execute(
            select(SavedPaymentMethod).where(
                and_(
                    SavedPaymentMethod.id == method_id,
                    SavedPaymentMethod.user_id == user_id
                )
            )
        )
        method = result.scalar_one_or_none()

        if not method:
            raise ValueError("Payment method not found")

        method.is_active = False
        await db.commit()

    async def set_default_payment_method(
        self,
        db: AsyncSession,
        user_id: UUID,
        method_id: UUID
    ):
        """Set payment method as default"""

        # Unset current default
        await db.execute(
            update(SavedPaymentMethod).where(
                and_(
                    SavedPaymentMethod.user_id == user_id,
                    SavedPaymentMethod.is_default == True
                )
            ).values(is_default=False)
        )

        # Set new default
        await db.execute(
            update(SavedPaymentMethod).where(
                and_(
                    SavedPaymentMethod.id == method_id,
                    SavedPaymentMethod.user_id == user_id
                )
            ).values(is_default=True)
        )

        await db.commit()

    # ==================== Payment Processing ====================

    async def process_payment(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        request: PaymentRequest,
        ip_address: str = None
    ) -> PaymentResponse:
        """Process a payment"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # Get payment method
        if request.payment_method_id:
            result = await db.execute(
                select(SavedPaymentMethod).where(
                    and_(
                        SavedPaymentMethod.id == request.payment_method_id,
                        SavedPaymentMethod.user_id == user_id,
                        SavedPaymentMethod.is_active == True
                    )
                )
            )
            payment_method = result.scalar_one_or_none()

            if not payment_method:
                raise ValueError("Payment method not found")

            processor_token = payment_method.processor_token
            payment_type = payment_method.payment_type
        else:
            # One-time payment
            if not request.card_token:
                raise ValueError("Payment token required for one-time payment")
            processor_token = request.card_token
            payment_type = PaymentMethod(request.payment_type.value)

        # Create payment record
        payment = PortalPayment(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=user.patient_id,
            payment_method_id=request.payment_method_id,
            payment_type=payment_type,
            amount=Decimal(str(request.amount)),
            statement_ids=request.statement_ids,
            payment_plan_id=request.payment_plan_id,
            status=PaymentStatus.PROCESSING
        )
        db.add(payment)

        try:
            # Process with payment processor
            processor_result = await self._process_with_stripe(
                processor_token,
                request.amount,
                payment.id
            )

            payment.processor = self.payment_processor
            payment.processor_transaction_id = processor_result['transaction_id']
            payment.processor_response = processor_result
            payment.confirmation_number = self._generate_confirmation_number()
            payment.status = PaymentStatus.COMPLETED
            payment.processed_at = datetime.now(timezone.utc)
            payment.completed_at = datetime.now(timezone.utc)

            # Update payment plan if applicable
            if request.payment_plan_id:
                await self._apply_to_payment_plan(db, request.payment_plan_id, request.amount)

            # Save card if requested
            if request.save_payment_method and request.card_token and not request.payment_method_id:
                await self._save_payment_method_from_token(
                    db, user_id, tenant_id, request.card_token
                )

            # Generate receipt URL
            payment.receipt_url = f"/portal/receipts/{payment.confirmation_number}"

            # Log payment
            audit_log = PortalAuditLog(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                patient_id=user.patient_id,
                action=AuditAction.PAYMENT_MADE,
                action_category="billing",
                action_description=f"Payment of ${request.amount:.2f} processed",
                details={
                    "amount": float(request.amount),
                    "confirmation_number": payment.confirmation_number
                },
                ip_address=ip_address,
                success=True
            )
            db.add(audit_log)

            await db.commit()

            # Send receipt email
            await self._send_payment_receipt(user.email, payment)

            return PaymentResponse(
                id=payment.id,
                amount=float(payment.amount),
                currency=payment.currency,
                status=PaymentStatusEnum(payment.status.value),
                confirmation_number=payment.confirmation_number,
                receipt_url=payment.receipt_url,
                processed_at=payment.processed_at,
                created_at=payment.created_at,
                updated_at=payment.updated_at
            )

        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.failed_at = datetime.now(timezone.utc)
            payment.error_message = str(e)
            await db.commit()

            raise ValueError(f"Payment failed: {str(e)}")

    async def _process_with_stripe(
        self,
        token: str,
        amount: float,
        payment_id: UUID
    ) -> Dict:
        """Process payment with Stripe (placeholder)"""
        # In production, this would use the Stripe SDK
        # stripe.PaymentIntent.create(...)
        return {
            'transaction_id': f"txn_{uuid4().hex[:16]}",
            'status': 'succeeded',
            'amount': int(amount * 100),  # Stripe uses cents
            'currency': 'usd'
        }

    def _generate_confirmation_number(self) -> str:
        """Generate unique confirmation number"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

    async def _apply_to_payment_plan(
        self,
        db: AsyncSession,
        plan_id: UUID,
        amount: float
    ):
        """Apply payment to payment plan"""
        result = await db.execute(
            select(PaymentPlan).where(PaymentPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if plan:
            plan.remaining_amount = max(0, float(plan.remaining_amount) - amount)
            plan.payments_made += 1

            if plan.remaining_amount <= 0:
                plan.is_active = False
                plan.status = "completed"
                plan.completed_at = datetime.now(timezone.utc)
            else:
                # Calculate next payment date
                plan.next_payment_date = (
                    date.today().replace(day=plan.payment_day_of_month) + timedelta(days=32)
                ).replace(day=plan.payment_day_of_month)

    async def _save_payment_method_from_token(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        token: str
    ):
        """Save payment method from processor token"""
        # Would retrieve card details from processor and save
        pass

    async def _send_payment_receipt(
        self,
        email: str,
        payment: PortalPayment
    ):
        """Send payment receipt email"""
        # Integrate with email service
        print(f"Sending receipt to {email} for payment {payment.confirmation_number}")

    # ==================== Payment Plans ====================

    async def create_payment_plan(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        request: PaymentPlanRequest
    ) -> PaymentPlanResponse:
        """Create a new payment plan"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        # Calculate monthly payment
        monthly_payment = Decimal(str(request.total_amount)) / request.number_of_payments

        plan = PaymentPlan(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=user.patient_id,
            total_amount=Decimal(str(request.total_amount)),
            remaining_amount=Decimal(str(request.total_amount)),
            monthly_payment=monthly_payment,
            number_of_payments=request.number_of_payments,
            start_date=request.start_date,
            next_payment_date=request.start_date,
            payment_day_of_month=request.payment_day_of_month,
            auto_pay_enabled=request.auto_pay_enabled,
            payment_method_id=request.payment_method_id
        )
        db.add(plan)
        await db.commit()

        return PaymentPlanResponse(
            id=plan.id,
            total_amount=float(plan.total_amount),
            remaining_amount=float(plan.remaining_amount),
            monthly_payment=float(plan.monthly_payment),
            number_of_payments=plan.number_of_payments,
            payments_made=plan.payments_made,
            start_date=plan.start_date,
            next_payment_date=plan.next_payment_date,
            payment_day_of_month=plan.payment_day_of_month,
            auto_pay_enabled=plan.auto_pay_enabled,
            is_active=plan.is_active,
            status=plan.status,
            created_at=plan.created_at,
            updated_at=plan.updated_at
        )

    async def get_payment_plans(
        self,
        db: AsyncSession,
        user_id: UUID,
        active_only: bool = True
    ) -> List[PaymentPlanResponse]:
        """Get user's payment plans"""

        query = select(PaymentPlan).where(PaymentPlan.user_id == user_id)

        if active_only:
            query = query.where(PaymentPlan.is_active == True)

        result = await db.execute(query.order_by(desc(PaymentPlan.created_at)))
        plans = result.scalars().all()

        return [
            PaymentPlanResponse(
                id=p.id,
                name=p.name,
                total_amount=float(p.total_amount),
                remaining_amount=float(p.remaining_amount),
                monthly_payment=float(p.monthly_payment),
                number_of_payments=p.number_of_payments,
                payments_made=p.payments_made,
                start_date=p.start_date,
                next_payment_date=p.next_payment_date,
                payment_day_of_month=p.payment_day_of_month,
                auto_pay_enabled=p.auto_pay_enabled,
                is_active=p.is_active,
                status=p.status,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in plans
        ]

    async def cancel_payment_plan(
        self,
        db: AsyncSession,
        user_id: UUID,
        plan_id: UUID,
        reason: str = None
    ):
        """Cancel a payment plan"""

        result = await db.execute(
            select(PaymentPlan).where(
                and_(
                    PaymentPlan.id == plan_id,
                    PaymentPlan.user_id == user_id,
                    PaymentPlan.is_active == True
                )
            )
        )
        plan = result.scalar_one_or_none()

        if not plan:
            raise ValueError("Payment plan not found")

        plan.is_active = False
        plan.status = "cancelled"
        plan.cancelled_at = datetime.now(timezone.utc)
        plan.cancellation_reason = reason

        await db.commit()

    # ==================== Payment History ====================

    async def get_payment_history(
        self,
        db: AsyncSession,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        date_from: date = None,
        date_to: date = None
    ) -> PaymentHistoryResponse:
        """Get payment history for user"""

        result = await db.execute(
            select(PortalUser).where(PortalUser.id == user_id)
        )
        user = result.scalar_one()

        query = select(PortalPayment).where(
            PortalPayment.patient_id == user.patient_id
        )

        if date_from:
            query = query.where(PortalPayment.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            query = query.where(PortalPayment.created_at <= datetime.combine(date_to, datetime.max.time()))

        # Get total count
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total_count = count_result.scalar()

        # Get total paid
        total_result = await db.execute(
            select(func.sum(PortalPayment.amount)).where(
                and_(
                    PortalPayment.patient_id == user.patient_id,
                    PortalPayment.status == PaymentStatus.COMPLETED
                )
            )
        )
        total_paid = float(total_result.scalar() or 0)

        # Get paginated results
        query = query.order_by(desc(PortalPayment.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        payments = result.scalars().all()

        return PaymentHistoryResponse(
            payments=[
                PaymentResponse(
                    id=p.id,
                    amount=float(p.amount),
                    currency=p.currency,
                    status=PaymentStatusEnum(p.status.value),
                    confirmation_number=p.confirmation_number,
                    receipt_url=p.receipt_url,
                    processed_at=p.processed_at,
                    error_message=p.error_message,
                    created_at=p.created_at,
                    updated_at=p.updated_at
                )
                for p in payments
            ],
            total_count=total_count,
            total_paid=total_paid
        )
