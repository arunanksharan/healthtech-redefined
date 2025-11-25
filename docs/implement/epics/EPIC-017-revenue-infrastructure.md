# EPIC-017: Revenue Infrastructure
**Epic ID:** EPIC-017
**Priority:** P0 (Critical)
**Program Increment:** PI-5
**Total Story Points:** 89
**Squad:** Platform Team
**Duration:** 2 Sprints (4 weeks)

---

## 📋 Epic Overview

### Description
Build a comprehensive revenue infrastructure that enables sustainable monetization of the PRM platform through subscription management, usage-based billing for AI features, payment processing, and financial operations. This epic establishes the commercial foundation that transforms the "Cognitive Operating System for Care" from a technology platform into a viable multi-billion dollar healthcare business.

### Business Value
- **Revenue Generation:** Enable $10K+ MRR from initial customers, scaling to $1M+ ARR
- **Pricing Flexibility:** Support multiple monetization models (subscription, usage, hybrid)
- **Operational Efficiency:** Automated billing reduces finance overhead by 80%
- **Customer Experience:** Self-service billing portal increases satisfaction by 40%
- **Cash Flow:** Accelerated collections with automated dunning reduces DSO by 15 days

### Success Criteria
- [ ] Subscription lifecycle management operational (create, upgrade, downgrade, cancel)
- [ ] Usage metering capturing all billable AI interactions with <1% error rate
- [ ] Payment processing via Stripe with 99.9% success rate
- [ ] Invoice generation automated with tax compliance
- [ ] Revenue recognition compliant with ASC 606
- [ ] Customer billing portal with self-service capabilities

### Alignment with Core Philosophy
This epic enables the monetization of the "Bionic Workflows" - specifically pricing the AI agents that handle low-empathy, high-repetition cognitive load. The billing system itself follows "Invisibility over Interface" principles with automated, ambient billing that requires minimal customer interaction.

---

## 🎯 User Stories

### US-017.1: Subscription Management System
**Story Points:** 13 | **Priority:** P0 | **Sprint:** 5.1

**As a** healthcare organization administrator
**I want** to manage my PRM subscription plan
**So that** I can control costs and scale features as my practice grows

#### Acceptance Criteria:
- [ ] Create subscription with plan selection (Starter, Professional, Enterprise)
- [ ] Upgrade/downgrade plan with automatic proration
- [ ] Support monthly and annual billing cycles
- [ ] Configure quantity (seats, facilities, providers)
- [ ] Handle trial periods (14/30 day trials)
- [ ] Process subscription cancellation with grace periods

#### Tasks:
```yaml
TASK-017.1.1: Design subscription domain models
  - Define Subscription, Plan, PlanFeature entities
  - Create subscription state machine (trialing→active→past_due→canceled)
  - Implement tenant-subscription mapping
  - Time: 6 hours

TASK-017.1.2: Build subscription service
  - Implement create_subscription with plan validation
  - Build change_plan with proration calculation
  - Create cancel_subscription with period-end handling
  - Add renewal processing logic
  - Time: 8 hours

TASK-017.1.3: Implement plan catalog management
  - Create plan CRUD operations
  - Define feature flags per plan
  - Implement usage limits per plan
  - Build plan comparison API
  - Time: 6 hours

TASK-017.1.4: Build entitlement engine
  - Map plans to feature entitlements
  - Implement real-time entitlement checks
  - Create enforcement middleware
  - Build grace period handling
  - Time: 8 hours

TASK-017.1.5: Create subscription webhooks
  - Emit subscription.created events
  - Emit subscription.updated events
  - Emit subscription.canceled events
  - Integrate with event-driven architecture (EPIC-002)
  - Time: 4 hours
```

---

### US-017.2: Usage Metering for AI Features
**Story Points:** 13 | **Priority:** P0 | **Sprint:** 5.1

**As a** platform operator
**I want** to accurately track usage of AI-powered features
**So that** I can implement fair usage-based pricing for high-value capabilities

#### Acceptance Criteria:
- [ ] Track AI interactions (triage, scribe, coding agent calls)
- [ ] Meter API calls per endpoint with tenant attribution
- [ ] Track storage consumption (documents, recordings, FHIR resources)
- [ ] Count active provider seats monthly
- [ ] Monitor telehealth minutes consumed
- [ ] Capture SMS/voice message volumes (Zoice, WhatsApp)

#### Tasks:
```yaml
TASK-017.2.1: Design usage event schema
  - Define UsageEvent model with metric_type, quantity, metadata
  - Create tenant_id + timestamp + metric compound index
  - Implement event validation rules
  - Time: 4 hours

TASK-017.2.2: Build usage ingestion pipeline
  - Create Kafka topic for usage events
  - Build high-throughput event consumer
  - Implement Redis real-time counters
  - Add TimescaleDB for historical storage
  - Time: 8 hours

TASK-017.2.3: Implement AI usage tracking
  - Hook into AI service (EPIC-009) for LLM call counting
  - Track token consumption per request
  - Monitor medical entity extraction calls
  - Capture triage agent interactions
  - Time: 6 hours

TASK-017.2.4: Build communication channel metering
  - Integrate with Zoice webhook for voice minutes
  - Track WhatsApp message volumes
  - Count SMS notifications
  - Monitor email sends
  - Time: 6 hours

TASK-017.2.5: Create usage aggregation service
  - Build hourly/daily/monthly rollups
  - Implement usage report generation
  - Create threshold alerting (80%, 90%, 100%)
  - Add forecasting for usage trends
  - Time: 8 hours
```

---

### US-017.3: Payment Processing Integration
**Story Points:** 13 | **Priority:** P0 | **Sprint:** 5.1

**As a** finance administrator
**I want** secure payment processing with multiple methods
**So that** we can collect revenue efficiently while meeting compliance requirements

#### Acceptance Criteria:
- [ ] Credit/debit card processing via Stripe
- [ ] ACH bank transfer support for enterprise customers
- [ ] Automatic recurring payment collection
- [ ] Payment retry logic with exponential backoff
- [ ] PCI-DSS compliant tokenization (no raw card storage)
- [ ] 3D Secure authentication for high-risk transactions

#### Tasks:
```yaml
TASK-017.3.1: Configure Stripe integration
  - Setup Stripe SDK with API keys (secure vault storage)
  - Implement customer creation sync
  - Configure webhook endpoint for payment events
  - Setup test/production environment separation
  - Time: 6 hours

TASK-017.3.2: Implement payment method management
  - Build add_payment_method with card tokenization
  - Create set_default_payment_method
  - Implement remove_payment_method
  - Add card expiration monitoring
  - Time: 6 hours

TASK-017.3.3: Build payment processing service
  - Implement create_payment_intent for one-time charges
  - Build automatic invoice payment
  - Create refund processing
  - Add partial payment handling
  - Time: 8 hours

TASK-017.3.4: Implement payment retry logic
  - Configure Smart Retries via Stripe
  - Build custom retry scheduling for failed payments
  - Implement payment method update prompts
  - Create escalation to manual collection
  - Time: 4 hours

TASK-017.3.5: Add ACH bank transfer support
  - Implement Plaid integration for bank verification
  - Build ACH payment method creation
  - Handle ACH-specific timing (3-5 day settlement)
  - Create ACH failure handling
  - Time: 6 hours
```

---

### US-017.4: Invoice Generation & Management
**Story Points:** 8 | **Priority:** P0 | **Sprint:** 5.1

**As a** customer
**I want** clear, accurate invoices for my PRM subscription
**So that** I can reconcile expenses and manage my healthcare IT budget

#### Acceptance Criteria:
- [ ] Automatic invoice generation on billing date
- [ ] Itemized line items (subscription, usage overage, add-ons)
- [ ] Tax calculation based on customer location
- [ ] PDF invoice generation with branded template
- [ ] Invoice delivery via email and portal
- [ ] Support for credit memos and adjustments

#### Tasks:
```yaml
TASK-017.4.1: Design invoice data model
  - Create Invoice, InvoiceLineItem, InvoicePayment entities
  - Implement invoice numbering sequence (tenant-prefixed)
  - Build invoice status state machine
  - Time: 4 hours

TASK-017.4.2: Build invoice generation service
  - Implement subscription invoice generation
  - Add usage-based line item calculation
  - Create proration line items
  - Build tax calculation integration
  - Time: 8 hours

TASK-017.4.3: Create PDF invoice generator
  - Design branded invoice template
  - Implement PDF rendering (WeasyPrint/Puppeteer)
  - Add QR code for payment link
  - Store PDFs in S3 with secure URLs
  - Time: 6 hours

TASK-017.4.4: Implement invoice delivery
  - Build email delivery with PDF attachment
  - Create in-app notification
  - Add SMS reminder option
  - Implement delivery tracking
  - Time: 4 hours

TASK-017.4.5: Build credit memo system
  - Implement credit memo generation
  - Create invoice adjustment workflow
  - Build credit application to future invoices
  - Add refund processing from credits
  - Time: 4 hours
```

---

### US-017.5: Dunning & Collections Management
**Story Points:** 8 | **Priority:** P0 | **Sprint:** 5.2

**As a** revenue operations manager
**I want** automated handling of failed payments
**So that** we minimize involuntary churn and maximize revenue recovery

#### Acceptance Criteria:
- [ ] Automatic payment retry on days 1, 3, 5, 7 after failure
- [ ] Escalating notification sequence (friendly→urgent→final)
- [ ] Grace period before service degradation (7 days)
- [ ] Self-service payment update capability
- [ ] Automatic service restoration on successful payment
- [ ] Churn risk identification and intervention triggers

#### Tasks:
```yaml
TASK-017.5.1: Design dunning workflow engine
  - Create DunningSchedule configuration model
  - Build retry attempt tracking
  - Implement grace period management
  - Define escalation rules
  - Time: 6 hours

TASK-017.5.2: Build notification templates
  - Create friendly payment reminder (Day 1)
  - Build urgent payment request (Day 3-5)
  - Create final warning before suspension (Day 7)
  - Design service restoration confirmation
  - Time: 4 hours

TASK-017.5.3: Implement service degradation
  - Build feature restriction on past_due status
  - Create read-only mode for suspended accounts
  - Implement data retention during suspension
  - Add reactivation workflow
  - Time: 6 hours

TASK-017.5.4: Create payment recovery tools
  - Build one-click payment link generation
  - Implement self-service card update flow
  - Create customer service override capabilities
  - Add payment plan options for enterprise
  - Time: 4 hours

TASK-017.5.5: Build churn prediction integration
  - Connect with analytics (EPIC-011) for risk scoring
  - Trigger proactive outreach for at-risk accounts
  - Create customer success alerts
  - Build win-back campaign triggers
  - Time: 4 hours
```

---

### US-017.6: Revenue Recognition & Reporting
**Story Points:** 8 | **Priority:** P1 | **Sprint:** 5.2

**As a** CFO
**I want** ASC 606 compliant revenue recognition and financial reporting
**So that** we meet accounting standards and can make data-driven business decisions

#### Acceptance Criteria:
- [ ] Deferred revenue tracking for prepaid subscriptions
- [ ] Revenue recognition schedule generation
- [ ] MRR/ARR calculation and trending
- [ ] Churn, expansion, and contraction metrics
- [ ] Cohort analysis by signup month
- [ ] Integration with accounting systems (QuickBooks, NetSuite)

#### Tasks:
```yaml
TASK-017.6.1: Implement revenue recognition engine
  - Build revenue schedule generation
  - Implement deferred revenue tracking
  - Create recognition rules (straight-line, usage-based)
  - Handle contract modifications
  - Time: 8 hours

TASK-017.6.2: Build SaaS metrics dashboard
  - Calculate MRR/ARR in real-time
  - Track net revenue retention
  - Compute customer lifetime value
  - Build churn analysis
  - Time: 6 hours

TASK-017.6.3: Create financial reports
  - Build revenue summary report
  - Create deferred revenue report
  - Implement aging report for AR
  - Generate cash flow projections
  - Time: 6 hours

TASK-017.6.4: Implement accounting integration
  - Build QuickBooks Online sync
  - Create journal entry export
  - Implement invoice sync
  - Add payment reconciliation
  - Time: 6 hours
```

---

### US-017.7: Customer Billing Portal
**Story Points:** 13 | **Priority:** P0 | **Sprint:** 5.2

**As a** healthcare organization administrator
**I want** a self-service billing portal
**So that** I can manage billing without contacting support

#### Acceptance Criteria:
- [ ] View current subscription and plan details
- [ ] Update payment methods securely
- [ ] Download invoices and receipts
- [ ] View real-time usage metrics
- [ ] Upgrade/downgrade plan self-service
- [ ] Cancel subscription with feedback collection

#### Tasks:
```yaml
TASK-017.7.1: Build billing portal API
  - Create /billing/subscription endpoint
  - Build /billing/usage endpoint
  - Implement /billing/invoices endpoint
  - Add /billing/payment-methods endpoint
  - Time: 6 hours

TASK-017.7.2: Implement billing portal UI
  - Design subscription overview card
  - Build usage dashboard with charts
  - Create invoice history table
  - Implement payment method manager
  - Time: 10 hours

TASK-017.7.3: Build plan change flow
  - Create plan comparison view
  - Implement upgrade/downgrade preview
  - Show proration calculation
  - Build confirmation workflow
  - Time: 6 hours

TASK-017.7.4: Create usage insights
  - Build real-time usage meter visualization
  - Show usage history trends
  - Display cost breakdown by feature
  - Add usage forecast
  - Time: 4 hours

TASK-017.7.5: Implement cancellation flow
  - Create cancellation reason survey
  - Show retention offers
  - Build cancellation confirmation
  - Add win-back scheduling
  - Time: 4 hours
```

---

### US-017.8: Pricing & Plan Management
**Story Points:** 5 | **Priority:** P1 | **Sprint:** 5.2

**As a** product manager
**I want** flexible pricing plan configuration
**So that** we can iterate on pricing strategy without engineering changes

#### Acceptance Criteria:
- [ ] Create/edit plans with features and limits
- [ ] Configure pricing tiers (per-seat, per-facility, usage-based)
- [ ] Manage promotional coupon codes
- [ ] Set up volume discounts
- [ ] A/B test pricing variations
- [ ] Grandfather existing customers on plan changes

#### Tasks:
```yaml
TASK-017.8.1: Build plan management admin
  - Create plan CRUD interface
  - Implement feature flag configuration
  - Build limit management
  - Add pricing tier configuration
  - Time: 6 hours

TASK-017.8.2: Implement coupon system
  - Create coupon code generation
  - Build discount types (percentage, fixed, trial extension)
  - Implement usage limits and expiration
  - Add redemption tracking
  - Time: 4 hours

TASK-017.8.3: Create pricing calculator
  - Build public pricing page calculator
  - Implement custom quote generator
  - Add volume discount tiers
  - Create enterprise pricing request flow
  - Time: 4 hours
```

---

## 📐 Technical Architecture

### System Components
```yaml
revenue_infrastructure:
  billing_service:
    technology: FastAPI
    database: PostgreSQL
    responsibilities:
      - Subscription lifecycle management
      - Invoice generation
      - Payment processing orchestration
      - Dunning workflow

  metering_service:
    technology: FastAPI
    database: TimescaleDB + Redis
    responsibilities:
      - Usage event ingestion
      - Real-time aggregation
      - Threshold monitoring
      - Usage reporting

  payment_gateway:
    provider: Stripe
    capabilities:
      - Card processing
      - ACH transfers
      - Webhook handling
      - Subscription billing

  billing_portal:
    technology: Next.js
    features:
      - Subscription management
      - Invoice download
      - Usage dashboard
      - Payment method management
```

### Data Flow
```
[AI Service] ──→ [Usage Events] ──→ [Kafka] ──→ [Metering Service]
                                                      │
[Zoice/WhatsApp] ──→ [Usage Events] ──────────────────┘
                                                      │
                                                      ▼
[Billing Service] ←── [Usage Aggregates] ←── [Redis/TimescaleDB]
        │
        ├──→ [Stripe] ──→ [Payment Processing]
        │
        ├──→ [Invoice PDF] ──→ [S3 Storage]
        │
        └──→ [Event Bus] ──→ [Notifications]
```

### Pricing Model Configuration
```python
# Example Plan Configuration
PLANS = {
    "starter": {
        "name": "Starter",
        "monthly_price": 299,
        "annual_price": 2990,  # 2 months free
        "features": {
            "patients": 500,
            "providers": 5,
            "ai_interactions": 1000,
            "telehealth_minutes": 100,
            "sms_messages": 500,
            "fhir_api_calls": 10000,
        },
        "overage_rates": {
            "ai_interactions": 0.05,  # $0.05 per interaction
            "telehealth_minutes": 0.25,  # $0.25 per minute
            "sms_messages": 0.02,  # $0.02 per message
        }
    },
    "professional": {
        "name": "Professional",
        "monthly_price": 799,
        "annual_price": 7990,
        "features": {
            "patients": 2500,
            "providers": 25,
            "ai_interactions": 5000,
            "telehealth_minutes": 500,
            "sms_messages": 2500,
            "fhir_api_calls": 50000,
            "ambient_scribe": True,
            "coding_agent": True,
        }
    },
    "enterprise": {
        "name": "Enterprise",
        "custom_pricing": True,
        "features": {
            "unlimited_patients": True,
            "unlimited_providers": True,
            "dedicated_support": True,
            "custom_integrations": True,
            "sla_guarantee": "99.99%",
            "hipaa_baa": True,
        }
    }
}
```

---

## 🔒 Security & Compliance

### PCI-DSS Compliance
- **No card data storage:** All payment credentials tokenized via Stripe
- **TLS 1.3:** All payment API communications encrypted
- **Webhook verification:** Stripe signature validation on all events
- **Audit logging:** All payment operations logged with user context

### HIPAA Considerations
- Billing data may contain PHI (patient counts, service dates)
- Apply row-level security from EPIC-004
- Encrypt billing records at rest
- Include billing audit in HIPAA audit trail (EPIC-022)

---

## 🔗 Dependencies

### Technical Dependencies
| Dependency | Epic | Reason |
|------------|------|--------|
| Event-Driven Architecture | EPIC-002 | Usage event streaming via Kafka |
| Multi-Tenancy | EPIC-004 | Tenant-isolated billing records |
| AI Integration | EPIC-009 | Usage metering for AI features |
| Omnichannel | EPIC-013 | Usage tracking for Zoice/WhatsApp |

### External Dependencies
- Stripe account with Healthcare MCC approval
- QuickBooks/NetSuite API credentials
- Tax calculation service (TaxJar/Avalara)

---

## 🧪 Testing Strategy

### Unit Tests
- Proration calculation accuracy
- Usage aggregation correctness
- Dunning schedule generation
- Revenue recognition rules

### Integration Tests
- Stripe webhook handling
- Full subscription lifecycle
- Payment retry workflows
- Invoice generation end-to-end

### Performance Tests
- Usage ingestion at 10,000 events/second
- Invoice generation for 1,000 customers
- Real-time usage dashboard response < 500ms

---

## 📋 Rollout Plan

### Phase 1: Core Billing (Week 1)
- [ ] Deploy billing service
- [ ] Stripe integration
- [ ] Basic subscription management
- [ ] Invoice generation

### Phase 2: Usage Metering (Week 2)
- [ ] Usage event pipeline
- [ ] AI interaction tracking
- [ ] Communication channel metering
- [ ] Real-time dashboards

### Phase 3: Customer Experience (Week 3)
- [ ] Billing portal UI
- [ ] Self-service plan changes
- [ ] Dunning automation
- [ ] Notification templates

### Phase 4: Advanced Features (Week 4)
- [ ] Revenue recognition
- [ ] Accounting integrations
- [ ] Admin pricing tools
- [ ] Production hardening

---

**Epic Status:** Ready for Implementation
**Document Owner:** Platform Team Lead
**Last Updated:** November 25, 2024
**Next Review:** Sprint 5.1 Planning
