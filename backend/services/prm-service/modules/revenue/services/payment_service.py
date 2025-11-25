"""
Payment Service
EPIC-017: Stripe payment processing integration
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, desc

from modules.revenue.models import (
    Payment, PaymentMethod, Customer, Invoice, BillingAuditLog,
    PaymentStatus, PaymentMethodType, InvoiceStatus
)
from modules.revenue.schemas import (
    PaymentCreate, PaymentRefund, PaymentResponse, PaymentListResponse,
    PaymentMethodCreate, PaymentMethodResponse, PaymentMethodListResponse,
    CustomerCreate, CustomerUpdate, CustomerResponse
)


class PaymentService:
    """
    Handles payment processing:
    - Stripe integration for cards and ACH
    - Payment method management
    - Payment processing and refunds
    - Customer management
    """

    def __init__(self):
        # Stripe client would be initialized here
        self._stripe = None

    async def create_customer(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: CustomerCreate
    ) -> CustomerResponse:
        """Create billing customer"""

        # Check if customer exists
        result = await db.execute(
            select(Customer).where(Customer.tenant_id == tenant_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError("Customer already exists for this tenant")

        # Create Stripe customer (placeholder)
        stripe_customer_id = await self._create_stripe_customer(data)

        customer = Customer(
            id=uuid4(),
            tenant_id=tenant_id,
            name=data.name,
            email=data.email,
            phone=data.phone,
            billing_address_line1=data.billing_address_line1,
            billing_address_line2=data.billing_address_line2,
            billing_city=data.billing_city,
            billing_state=data.billing_state,
            billing_postal_code=data.billing_postal_code,
            billing_country=data.billing_country,
            tax_id=data.tax_id,
            tax_exempt=data.tax_exempt,
            payment_terms_days=data.payment_terms_days,
            currency=data.currency,
            stripe_customer_id=stripe_customer_id
        )
        db.add(customer)

        await db.commit()
        await db.refresh(customer)

        return self._customer_to_response(customer)

    async def update_customer(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: CustomerUpdate
    ) -> CustomerResponse:
        """Update billing customer"""

        result = await db.execute(
            select(Customer).where(Customer.tenant_id == tenant_id)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            raise ValueError("Customer not found")

        if data.name is not None:
            customer.name = data.name
        if data.email is not None:
            customer.email = data.email
        if data.phone is not None:
            customer.phone = data.phone
        if data.billing_address_line1 is not None:
            customer.billing_address_line1 = data.billing_address_line1
        if data.billing_address_line2 is not None:
            customer.billing_address_line2 = data.billing_address_line2
        if data.billing_city is not None:
            customer.billing_city = data.billing_city
        if data.billing_state is not None:
            customer.billing_state = data.billing_state
        if data.billing_postal_code is not None:
            customer.billing_postal_code = data.billing_postal_code
        if data.billing_country is not None:
            customer.billing_country = data.billing_country
        if data.tax_id is not None:
            customer.tax_id = data.tax_id
        if data.tax_exempt is not None:
            customer.tax_exempt = data.tax_exempt
        if data.payment_terms_days is not None:
            customer.payment_terms_days = data.payment_terms_days

        customer.updated_at = datetime.now(timezone.utc)

        # Update Stripe customer (placeholder)
        if customer.stripe_customer_id:
            await self._update_stripe_customer(customer.stripe_customer_id, data)

        await db.commit()
        await db.refresh(customer)

        return self._customer_to_response(customer)

    async def get_customer(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> CustomerResponse:
        """Get billing customer"""

        result = await db.execute(
            select(Customer).where(Customer.tenant_id == tenant_id)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            raise ValueError("Customer not found")

        return self._customer_to_response(customer)

    async def add_payment_method(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: PaymentMethodCreate
    ) -> PaymentMethodResponse:
        """Add payment method"""

        # Get customer
        result = await db.execute(
            select(Customer).where(Customer.tenant_id == tenant_id)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            raise ValueError("Customer not found")

        # Attach to Stripe customer (placeholder)
        stripe_pm = await self._attach_payment_method(
            data.stripe_payment_method_token,
            customer.stripe_customer_id
        )

        payment_method = PaymentMethod(
            id=uuid4(),
            customer_id=customer.id,
            method_type=PaymentMethodType(data.method_type.value),
            is_default=data.set_as_default,
            stripe_payment_method_id=stripe_pm.get("id"),
            is_verified=True,
            is_active=True
        )

        # Set card details from Stripe response
        if data.method_type == PaymentMethodType.CARD:
            card = stripe_pm.get("card", {})
            payment_method.card_brand = card.get("brand")
            payment_method.card_last4 = card.get("last4")
            payment_method.card_exp_month = card.get("exp_month")
            payment_method.card_exp_year = card.get("exp_year")
            payment_method.card_funding = card.get("funding")

        db.add(payment_method)

        # Set as default if requested
        if data.set_as_default:
            await db.execute(
                update(PaymentMethod).where(
                    and_(
                        PaymentMethod.customer_id == customer.id,
                        PaymentMethod.id != payment_method.id
                    )
                ).values(is_default=False)
            )
            customer.default_payment_method_id = payment_method.id

        await db.commit()
        await db.refresh(payment_method)

        return self._payment_method_to_response(payment_method)

    async def remove_payment_method(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payment_method_id: UUID
    ) -> None:
        """Remove payment method"""

        result = await db.execute(
            select(PaymentMethod).join(
                Customer, Customer.id == PaymentMethod.customer_id
            ).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    PaymentMethod.id == payment_method_id
                )
            )
        )
        payment_method = result.scalar_one_or_none()

        if not payment_method:
            raise ValueError("Payment method not found")

        # Detach from Stripe (placeholder)
        if payment_method.stripe_payment_method_id:
            await self._detach_payment_method(payment_method.stripe_payment_method_id)

        payment_method.is_active = False
        payment_method.updated_at = datetime.now(timezone.utc)

        await db.commit()

    async def set_default_payment_method(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payment_method_id: UUID
    ) -> None:
        """Set default payment method"""

        # Get customer
        result = await db.execute(
            select(Customer).where(Customer.tenant_id == tenant_id)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            raise ValueError("Customer not found")

        # Verify payment method belongs to customer
        pm_result = await db.execute(
            select(PaymentMethod).where(
                and_(
                    PaymentMethod.id == payment_method_id,
                    PaymentMethod.customer_id == customer.id,
                    PaymentMethod.is_active == True
                )
            )
        )
        payment_method = pm_result.scalar_one_or_none()

        if not payment_method:
            raise ValueError("Payment method not found")

        # Update default
        await db.execute(
            update(PaymentMethod).where(
                PaymentMethod.customer_id == customer.id
            ).values(is_default=False)
        )

        payment_method.is_default = True
        customer.default_payment_method_id = payment_method_id

        await db.commit()

    async def list_payment_methods(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> PaymentMethodListResponse:
        """List customer payment methods"""

        result = await db.execute(
            select(PaymentMethod).join(
                Customer, Customer.id == PaymentMethod.customer_id
            ).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    PaymentMethod.is_active == True
                )
            )
        )
        methods = result.scalars().all()

        default_id = None
        for method in methods:
            if method.is_default:
                default_id = method.id
                break

        return PaymentMethodListResponse(
            payment_methods=[self._payment_method_to_response(m) for m in methods],
            default_id=default_id
        )

    async def create_payment(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: PaymentCreate,
        user_id: UUID = None
    ) -> PaymentResponse:
        """Create a payment"""

        # Get customer
        result = await db.execute(
            select(Customer).where(Customer.tenant_id == tenant_id)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            raise ValueError("Customer not found")

        # Get payment method
        payment_method_id = data.payment_method_id or customer.default_payment_method_id
        if not payment_method_id:
            raise ValueError("No payment method specified")

        pm_result = await db.execute(
            select(PaymentMethod).where(
                and_(
                    PaymentMethod.id == payment_method_id,
                    PaymentMethod.customer_id == customer.id,
                    PaymentMethod.is_active == True
                )
            )
        )
        payment_method = pm_result.scalar_one_or_none()

        if not payment_method:
            raise ValueError("Payment method not found")

        # Create Stripe payment intent (placeholder)
        stripe_intent = await self._create_payment_intent(
            amount=data.amount,
            currency=customer.currency,
            customer_id=customer.stripe_customer_id,
            payment_method_id=payment_method.stripe_payment_method_id,
            description=data.description
        )

        payment = Payment(
            id=uuid4(),
            customer_id=customer.id,
            invoice_id=data.invoice_id,
            payment_method_id=payment_method_id,
            amount=data.amount,
            currency=customer.currency,
            status=PaymentStatus.PROCESSING,
            stripe_payment_intent_id=stripe_intent.get("id"),
            description=data.description
        )
        db.add(payment)

        # Process payment (placeholder - would be async via webhook)
        if stripe_intent.get("status") == "succeeded":
            payment.status = PaymentStatus.SUCCEEDED
            payment.processed_at = datetime.now(timezone.utc)
            payment.receipt_url = stripe_intent.get("receipt_url")

            # Update invoice if provided
            if data.invoice_id:
                await self._apply_payment_to_invoice(db, data.invoice_id, data.amount)

        # Log audit
        await self._log_audit(
            db, tenant_id, user_id, "payment_created", "payment",
            payment.id, new_values={
                "amount": float(data.amount),
                "status": payment.status.value
            }
        )

        await db.commit()
        await db.refresh(payment)

        return self._payment_to_response(payment)

    async def refund_payment(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payment_id: UUID,
        data: PaymentRefund,
        user_id: UUID = None
    ) -> PaymentResponse:
        """Refund a payment"""

        result = await db.execute(
            select(Payment).join(
                Customer, Customer.id == Payment.customer_id
            ).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Payment.id == payment_id
                )
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise ValueError("Payment not found")

        if payment.status != PaymentStatus.SUCCEEDED:
            raise ValueError("Only succeeded payments can be refunded")

        refund_amount = data.amount or payment.amount - payment.amount_refunded
        if refund_amount > (payment.amount - payment.amount_refunded):
            raise ValueError("Refund amount exceeds remaining balance")

        # Create Stripe refund (placeholder)
        await self._create_refund(
            payment.stripe_payment_intent_id,
            refund_amount,
            data.reason
        )

        payment.amount_refunded += refund_amount
        if payment.amount_refunded >= payment.amount:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED

        payment.updated_at = datetime.now(timezone.utc)

        await self._log_audit(
            db, tenant_id, user_id, "payment_refunded", "payment",
            payment.id, new_values={
                "refund_amount": float(refund_amount),
                "status": payment.status.value
            }
        )

        await db.commit()
        await db.refresh(payment)

        return self._payment_to_response(payment)

    async def get_payment(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payment_id: UUID
    ) -> PaymentResponse:
        """Get payment by ID"""

        result = await db.execute(
            select(Payment).join(
                Customer, Customer.id == Payment.customer_id
            ).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Payment.id == payment_id
                )
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise ValueError("Payment not found")

        return self._payment_to_response(payment)

    async def list_payments(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        status: Optional[PaymentStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> PaymentListResponse:
        """List payments for tenant"""

        query = select(Payment).join(
            Customer, Customer.id == Payment.customer_id
        ).where(Customer.tenant_id == tenant_id)

        if status:
            query = query.where(Payment.status == status)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # Get results
        query = query.order_by(desc(Payment.created_at))
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        payments = result.scalars().all()

        return PaymentListResponse(
            payments=[self._payment_to_response(p) for p in payments],
            total=total
        )

    async def handle_webhook(
        self,
        db: AsyncSession,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Handle Stripe webhook events"""

        if event_type == "payment_intent.succeeded":
            await self._handle_payment_succeeded(db, event_data)
        elif event_type == "payment_intent.payment_failed":
            await self._handle_payment_failed(db, event_data)
        elif event_type == "charge.refunded":
            await self._handle_charge_refunded(db, event_data)
        elif event_type == "payment_method.attached":
            await self._handle_payment_method_attached(db, event_data)
        elif event_type == "payment_method.detached":
            await self._handle_payment_method_detached(db, event_data)

    # Private Stripe integration methods (placeholders)

    async def _create_stripe_customer(self, data: CustomerCreate) -> str:
        """Create Stripe customer"""
        # In production: stripe.Customer.create(...)
        return f"cus_{uuid4().hex[:14]}"

    async def _update_stripe_customer(
        self,
        stripe_customer_id: str,
        data: CustomerUpdate
    ) -> None:
        """Update Stripe customer"""
        # In production: stripe.Customer.modify(...)
        pass

    async def _attach_payment_method(
        self,
        payment_method_token: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """Attach payment method to Stripe customer"""
        # In production: stripe.PaymentMethod.attach(...)
        return {
            "id": f"pm_{uuid4().hex[:14]}",
            "card": {
                "brand": "visa",
                "last4": "4242",
                "exp_month": 12,
                "exp_year": 2025,
                "funding": "credit"
            }
        }

    async def _detach_payment_method(self, payment_method_id: str) -> None:
        """Detach payment method from Stripe"""
        # In production: stripe.PaymentMethod.detach(...)
        pass

    async def _create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        customer_id: str,
        payment_method_id: str,
        description: str = None
    ) -> Dict[str, Any]:
        """Create Stripe payment intent"""
        # In production: stripe.PaymentIntent.create(...)
        return {
            "id": f"pi_{uuid4().hex[:14]}",
            "status": "succeeded",
            "receipt_url": "https://pay.stripe.com/receipts/..."
        }

    async def _create_refund(
        self,
        payment_intent_id: str,
        amount: Decimal,
        reason: str = None
    ) -> Dict[str, Any]:
        """Create Stripe refund"""
        # In production: stripe.Refund.create(...)
        return {"id": f"re_{uuid4().hex[:14]}"}

    async def _apply_payment_to_invoice(
        self,
        db: AsyncSession,
        invoice_id: UUID,
        amount: Decimal
    ) -> None:
        """Apply payment to invoice"""
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()

        if invoice:
            invoice.amount_paid += amount
            if invoice.amount_paid >= invoice.total:
                invoice.status = InvoiceStatus.PAID
                invoice.paid_at = datetime.now(timezone.utc)
            invoice.amount_due = max(Decimal("0"), invoice.total - invoice.amount_paid)

    async def _handle_payment_succeeded(
        self,
        db: AsyncSession,
        event_data: Dict[str, Any]
    ) -> None:
        """Handle successful payment webhook"""
        payment_intent_id = event_data.get("id")
        result = await db.execute(
            select(Payment).where(
                Payment.stripe_payment_intent_id == payment_intent_id
            )
        )
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = PaymentStatus.SUCCEEDED
            payment.processed_at = datetime.now(timezone.utc)
            await db.commit()

    async def _handle_payment_failed(
        self,
        db: AsyncSession,
        event_data: Dict[str, Any]
    ) -> None:
        """Handle failed payment webhook"""
        payment_intent_id = event_data.get("id")
        result = await db.execute(
            select(Payment).where(
                Payment.stripe_payment_intent_id == payment_intent_id
            )
        )
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = event_data.get("last_payment_error", {}).get("message")
            payment.failure_code = event_data.get("last_payment_error", {}).get("code")
            await db.commit()

    async def _handle_charge_refunded(
        self,
        db: AsyncSession,
        event_data: Dict[str, Any]
    ) -> None:
        """Handle charge refunded webhook"""
        pass

    async def _handle_payment_method_attached(
        self,
        db: AsyncSession,
        event_data: Dict[str, Any]
    ) -> None:
        """Handle payment method attached webhook"""
        pass

    async def _handle_payment_method_detached(
        self,
        db: AsyncSession,
        event_data: Dict[str, Any]
    ) -> None:
        """Handle payment method detached webhook"""
        pass

    async def _log_audit(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID,
        old_values: Dict = None,
        new_values: Dict = None
    ) -> None:
        """Log billing audit event"""
        log = BillingAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            actor_type="user" if user_id else "system",
            action=action,
            action_category="payment",
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values
        )
        db.add(log)

    # Response converters

    def _customer_to_response(self, customer: Customer) -> CustomerResponse:
        return CustomerResponse(
            id=customer.id,
            tenant_id=customer.tenant_id,
            name=customer.name,
            email=customer.email,
            phone=customer.phone,
            billing_address_line1=customer.billing_address_line1,
            billing_address_line2=customer.billing_address_line2,
            billing_city=customer.billing_city,
            billing_state=customer.billing_state,
            billing_postal_code=customer.billing_postal_code,
            billing_country=customer.billing_country,
            tax_id=customer.tax_id,
            tax_exempt=customer.tax_exempt,
            stripe_customer_id=customer.stripe_customer_id,
            credit_balance=float(customer.credit_balance),
            created_at=customer.created_at
        )

    def _payment_method_to_response(self, pm: PaymentMethod) -> PaymentMethodResponse:
        return PaymentMethodResponse(
            id=pm.id,
            method_type=pm.method_type.value,
            is_default=pm.is_default,
            card_brand=pm.card_brand,
            card_last4=pm.card_last4,
            card_exp_month=pm.card_exp_month,
            card_exp_year=pm.card_exp_year,
            card_funding=pm.card_funding,
            bank_name=pm.bank_name,
            bank_last4=pm.bank_last4,
            bank_account_type=pm.bank_account_type,
            is_verified=pm.is_verified,
            is_active=pm.is_active,
            created_at=pm.created_at
        )

    def _payment_to_response(self, payment: Payment) -> PaymentResponse:
        return PaymentResponse(
            id=payment.id,
            customer_id=payment.customer_id,
            invoice_id=payment.invoice_id,
            amount=float(payment.amount),
            currency=payment.currency,
            amount_refunded=float(payment.amount_refunded),
            status=payment.status.value,
            failure_reason=payment.failure_reason,
            receipt_url=payment.receipt_url,
            processed_at=payment.processed_at,
            created_at=payment.created_at
        )
