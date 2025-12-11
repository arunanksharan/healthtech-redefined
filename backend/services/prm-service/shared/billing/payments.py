"""
Payment Processing Service

Patient payment handling:
- Payment collection
- Multiple payment methods
- Refund processing
- Payment plans
- Statement generation

EPIC-008: US-008.3 Payment Processing
"""

from datetime import datetime, timezone, date, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class PaymentStatus(str, Enum):
    """Payment status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL_REFUND = "partial_refund"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Payment method types."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ACH = "ach"
    CHECK = "check"
    CASH = "cash"
    HSA = "hsa"
    FSA = "fsa"
    PAYMENT_PLAN = "payment_plan"


class PaymentType(str, Enum):
    """Type of payment."""
    COPAY = "copay"
    COINSURANCE = "coinsurance"
    DEDUCTIBLE = "deductible"
    SELF_PAY = "self_pay"
    DEPOSIT = "deposit"
    BALANCE = "balance"
    PREPAYMENT = "prepayment"


@dataclass
class PaymentCard:
    """Stored payment card (tokenized)."""
    card_id: str
    patient_id: str
    tenant_id: str

    # Card details (tokenized)
    token: str
    last_four: str
    card_type: str  # visa, mastercard, amex, discover
    expiry_month: int
    expiry_year: int

    # Billing address
    billing_name: str = ""
    billing_zip: str = ""

    # Preferences
    is_default: bool = False
    is_active: bool = True

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PaymentPlanSchedule:
    """A scheduled payment in a payment plan."""
    schedule_id: str
    plan_id: str
    sequence: int

    amount: float
    due_date: date
    status: str = "scheduled"  # scheduled, paid, overdue, cancelled
    payment_id: Optional[str] = None

    paid_at: Optional[datetime] = None


@dataclass
class PaymentPlan:
    """A payment plan for a patient balance."""
    plan_id: str
    patient_id: str
    tenant_id: str

    # Plan details
    total_amount: float
    num_payments: int
    payment_amount: float
    frequency: str = "monthly"  # weekly, biweekly, monthly

    # Schedule
    start_date: date = field(default_factory=date.today)
    schedule: List[PaymentPlanSchedule] = field(default_factory=list)

    # Payment method
    payment_method_id: Optional[str] = None
    auto_pay: bool = False

    # Status
    status: str = "active"  # active, completed, defaulted, cancelled
    amount_paid: float = 0
    amount_remaining: float = 0

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PaymentAllocation:
    """Allocation of payment to a charge/claim."""
    allocation_id: str
    payment_id: str
    charge_id: Optional[str] = None
    claim_id: Optional[str] = None
    amount: float = 0


@dataclass
class Payment:
    """A payment transaction."""
    payment_id: str
    tenant_id: str
    patient_id: str

    # Amount
    amount: float
    currency: str = "USD"

    # Type and method
    payment_type: PaymentType = PaymentType.BALANCE
    payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD

    # Card details (if card payment)
    card_id: Optional[str] = None
    card_last_four: Optional[str] = None

    # Reference
    encounter_id: Optional[str] = None
    claim_id: Optional[str] = None
    appointment_id: Optional[str] = None
    plan_id: Optional[str] = None

    # Processing
    status: PaymentStatus = PaymentStatus.PENDING
    processor_transaction_id: Optional[str] = None
    authorization_code: Optional[str] = None

    # Failure
    failure_reason: Optional[str] = None
    failure_code: Optional[str] = None

    # Refund
    refunded_amount: float = 0
    refund_transaction_ids: List[str] = field(default_factory=list)

    # Allocations
    allocations: List[PaymentAllocation] = field(default_factory=list)

    # Receipt
    receipt_number: Optional[str] = None
    receipt_sent: bool = False

    # Notes
    notes: str = ""

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None


@dataclass
class PatientStatement:
    """Patient billing statement."""
    statement_id: str
    patient_id: str
    tenant_id: str

    # Statement details
    statement_date: date = field(default_factory=date.today)
    due_date: date = field(default_factory=lambda: date.today() + timedelta(days=30))
    statement_number: str = ""

    # Amounts
    previous_balance: float = 0
    new_charges: float = 0
    payments_received: float = 0
    adjustments: float = 0
    current_balance: float = 0

    # Age of balance
    current: float = 0
    over_30: float = 0
    over_60: float = 0
    over_90: float = 0
    over_120: float = 0

    # Line items
    line_items: List[Dict[str, Any]] = field(default_factory=list)

    # Status
    status: str = "generated"  # generated, sent, paid, overdue

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None


class PaymentService:
    """
    Payment processing service.

    Handles:
    - Payment collection
    - Card storage (tokenized)
    - Refunds
    - Payment plans
    - Statements
    """

    def __init__(
        self,
        stripe_api_key: Optional[str] = None,
    ):
        self.stripe_api_key = stripe_api_key

        self._payments: Dict[str, Payment] = {}
        self._cards: Dict[str, PaymentCard] = {}
        self._plans: Dict[str, PaymentPlan] = {}
        self._statements: Dict[str, PatientStatement] = {}

        # Receipt counter
        self._receipt_counter = 10000

    async def process_payment(
        self,
        tenant_id: str,
        patient_id: str,
        amount: float,
        payment_method: PaymentMethod,
        payment_type: PaymentType = PaymentType.BALANCE,
        card_id: Optional[str] = None,
        card_token: Optional[str] = None,
        encounter_id: Optional[str] = None,
        claim_id: Optional[str] = None,
        notes: str = "",
    ) -> Payment:
        """Process a payment."""
        payment = Payment(
            payment_id=str(uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            amount=amount,
            payment_type=payment_type,
            payment_method=payment_method,
            card_id=card_id,
            encounter_id=encounter_id,
            claim_id=claim_id,
            notes=notes,
        )

        # Get card info if using stored card
        if card_id:
            card = self._cards.get(card_id)
            if card:
                payment.card_last_four = card.last_four

        try:
            # In production, this would call payment processor
            payment.status = PaymentStatus.PROCESSING

            # Mock successful processing
            payment.processor_transaction_id = f"txn_{uuid4().hex[:12]}"
            payment.authorization_code = f"AUTH{self._receipt_counter}"
            payment.status = PaymentStatus.COMPLETED
            payment.processed_at = datetime.now(timezone.utc)

            # Generate receipt number
            self._receipt_counter += 1
            payment.receipt_number = f"RCP-{self._receipt_counter}"

            logger.info(f"Processed payment: {payment.payment_id}, amount: {amount}")

        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = str(e)
            logger.error(f"Payment failed: {payment.payment_id} - {e}")

        self._payments[payment.payment_id] = payment
        return payment

    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: str = "",
    ) -> Payment:
        """Refund a payment (full or partial)."""
        payment = self._payments.get(payment_id)
        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")

        if payment.status not in (PaymentStatus.COMPLETED, PaymentStatus.PARTIAL_REFUND):
            raise ValueError("Can only refund completed payments")

        refund_amount = amount or (payment.amount - payment.refunded_amount)

        if refund_amount > (payment.amount - payment.refunded_amount):
            raise ValueError("Refund amount exceeds available balance")

        # Process refund
        refund_txn_id = f"ref_{uuid4().hex[:12]}"
        payment.refund_transaction_ids.append(refund_txn_id)
        payment.refunded_amount += refund_amount
        payment.notes += f"\nRefund: {refund_amount} - {reason}"

        if payment.refunded_amount >= payment.amount:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIAL_REFUND

        logger.info(f"Refunded payment: {payment_id}, amount: {refund_amount}")
        return payment

    async def store_card(
        self,
        tenant_id: str,
        patient_id: str,
        card_token: str,
        last_four: str,
        card_type: str,
        expiry_month: int,
        expiry_year: int,
        billing_name: str = "",
        billing_zip: str = "",
        is_default: bool = False,
    ) -> PaymentCard:
        """Store a payment card (tokenized)."""
        card = PaymentCard(
            card_id=str(uuid4()),
            patient_id=patient_id,
            tenant_id=tenant_id,
            token=card_token,
            last_four=last_four,
            card_type=card_type,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            billing_name=billing_name,
            billing_zip=billing_zip,
            is_default=is_default,
        )

        # If setting as default, unset others
        if is_default:
            for c in self._cards.values():
                if c.patient_id == patient_id and c.tenant_id == tenant_id:
                    c.is_default = False

        self._cards[card.card_id] = card
        return card

    async def get_patient_cards(
        self,
        tenant_id: str,
        patient_id: str,
    ) -> List[PaymentCard]:
        """Get stored cards for a patient."""
        return [
            c for c in self._cards.values()
            if c.tenant_id == tenant_id
            and c.patient_id == patient_id
            and c.is_active
        ]

    async def delete_card(
        self,
        card_id: str,
    ) -> bool:
        """Delete (deactivate) a stored card."""
        card = self._cards.get(card_id)
        if card:
            card.is_active = False
            return True
        return False

    async def create_payment_plan(
        self,
        tenant_id: str,
        patient_id: str,
        total_amount: float,
        num_payments: int,
        frequency: str = "monthly",
        start_date: Optional[date] = None,
        payment_method_id: Optional[str] = None,
        auto_pay: bool = False,
    ) -> PaymentPlan:
        """Create a payment plan for a patient balance."""
        start = start_date or date.today()
        payment_amount = round(total_amount / num_payments, 2)

        plan = PaymentPlan(
            plan_id=str(uuid4()),
            patient_id=patient_id,
            tenant_id=tenant_id,
            total_amount=total_amount,
            num_payments=num_payments,
            payment_amount=payment_amount,
            frequency=frequency,
            start_date=start,
            payment_method_id=payment_method_id,
            auto_pay=auto_pay,
            amount_remaining=total_amount,
        )

        # Create schedule
        current_date = start
        for i in range(num_payments):
            schedule = PaymentPlanSchedule(
                schedule_id=str(uuid4()),
                plan_id=plan.plan_id,
                sequence=i + 1,
                amount=payment_amount,
                due_date=current_date,
            )
            plan.schedule.append(schedule)

            # Advance date
            if frequency == "weekly":
                current_date += timedelta(weeks=1)
            elif frequency == "biweekly":
                current_date += timedelta(weeks=2)
            else:  # monthly
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

        # Adjust last payment for rounding
        total_scheduled = sum(s.amount for s in plan.schedule)
        if total_scheduled != total_amount:
            plan.schedule[-1].amount += (total_amount - total_scheduled)

        self._plans[plan.plan_id] = plan
        logger.info(f"Created payment plan: {plan.plan_id}")

        return plan

    async def process_plan_payment(
        self,
        plan_id: str,
        schedule_id: str,
    ) -> Payment:
        """Process a scheduled payment from a plan."""
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        schedule = next(
            (s for s in plan.schedule if s.schedule_id == schedule_id),
            None
        )
        if not schedule:
            raise ValueError(f"Schedule not found: {schedule_id}")

        if schedule.status == "paid":
            raise ValueError("Payment already processed")

        # Process payment
        payment = await self.process_payment(
            tenant_id=plan.tenant_id,
            patient_id=plan.patient_id,
            amount=schedule.amount,
            payment_method=PaymentMethod.PAYMENT_PLAN,
            payment_type=PaymentType.BALANCE,
            card_id=plan.payment_method_id,
        )

        payment.plan_id = plan_id

        if payment.status == PaymentStatus.COMPLETED:
            schedule.status = "paid"
            schedule.payment_id = payment.payment_id
            schedule.paid_at = datetime.now(timezone.utc)
            plan.amount_paid += schedule.amount
            plan.amount_remaining -= schedule.amount

            # Check if plan is complete
            if all(s.status == "paid" for s in plan.schedule):
                plan.status = "completed"

        return payment

    async def get_payment_plan(
        self,
        plan_id: str,
    ) -> Optional[PaymentPlan]:
        """Get a payment plan by ID."""
        return self._plans.get(plan_id)

    async def get_patient_plans(
        self,
        tenant_id: str,
        patient_id: str,
    ) -> List[PaymentPlan]:
        """Get payment plans for a patient."""
        return [
            p for p in self._plans.values()
            if p.tenant_id == tenant_id and p.patient_id == patient_id
        ]

    async def generate_statement(
        self,
        tenant_id: str,
        patient_id: str,
        charges: List[Dict[str, Any]],
        previous_balance: float = 0,
    ) -> PatientStatement:
        """Generate a patient statement."""
        statement_number = f"STM-{datetime.now().strftime('%Y%m')}-{uuid4().hex[:6].upper()}"

        statement = PatientStatement(
            statement_id=str(uuid4()),
            patient_id=patient_id,
            tenant_id=tenant_id,
            statement_number=statement_number,
            previous_balance=previous_balance,
        )

        # Add charges
        for charge in charges:
            statement.line_items.append({
                "date": charge.get("date", date.today().isoformat()),
                "description": charge.get("description", ""),
                "amount": charge.get("amount", 0),
                "type": charge.get("type", "charge"),
            })

            if charge.get("type") == "charge":
                statement.new_charges += charge.get("amount", 0)
            elif charge.get("type") == "payment":
                statement.payments_received += charge.get("amount", 0)
            elif charge.get("type") == "adjustment":
                statement.adjustments += charge.get("amount", 0)

        # Calculate current balance
        statement.current_balance = (
            statement.previous_balance +
            statement.new_charges -
            statement.payments_received -
            statement.adjustments
        )

        self._statements[statement.statement_id] = statement
        return statement

    async def get_patient_statements(
        self,
        tenant_id: str,
        patient_id: str,
        limit: int = 12,
    ) -> List[PatientStatement]:
        """Get statements for a patient."""
        statements = [
            s for s in self._statements.values()
            if s.tenant_id == tenant_id and s.patient_id == patient_id
        ]
        statements.sort(key=lambda s: s.statement_date, reverse=True)
        return statements[:limit]

    async def get_payment(
        self,
        payment_id: str,
    ) -> Optional[Payment]:
        """Get a payment by ID."""
        return self._payments.get(payment_id)

    async def get_patient_payments(
        self,
        tenant_id: str,
        patient_id: str,
        limit: int = 50,
    ) -> List[Payment]:
        """Get payments for a patient."""
        payments = [
            p for p in self._payments.values()
            if p.tenant_id == tenant_id and p.patient_id == patient_id
        ]
        payments.sort(key=lambda p: p.created_at, reverse=True)
        return payments[:limit]

    async def get_daily_payments(
        self,
        tenant_id: str,
        payment_date: date,
    ) -> List[Payment]:
        """Get all payments for a date."""
        return [
            p for p in self._payments.values()
            if p.tenant_id == tenant_id
            and p.created_at.date() == payment_date
            and p.status == PaymentStatus.COMPLETED
        ]

    async def get_payments_summary(
        self,
        tenant_id: str,
        date_from: date,
        date_to: date,
    ) -> Dict[str, Any]:
        """Get payments summary for a date range."""
        payments = [
            p for p in self._payments.values()
            if p.tenant_id == tenant_id
            and p.created_at.date() >= date_from
            and p.created_at.date() <= date_to
        ]

        completed = [p for p in payments if p.status == PaymentStatus.COMPLETED]

        return {
            "total_transactions": len(payments),
            "successful_transactions": len(completed),
            "total_collected": sum(p.amount for p in completed),
            "total_refunded": sum(p.refunded_amount for p in payments),
            "net_collected": sum(p.amount - p.refunded_amount for p in completed),
            "by_method": {
                method.value: sum(
                    p.amount for p in completed if p.payment_method == method
                )
                for method in PaymentMethod
            },
            "by_type": {
                ptype.value: sum(
                    p.amount for p in completed if p.payment_type == ptype
                )
                for ptype in PaymentType
            },
        }


# Global payment service instance
payment_service = PaymentService()
