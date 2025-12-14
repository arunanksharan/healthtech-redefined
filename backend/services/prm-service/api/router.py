"""
API Router Aggregator
Combines all module routers into a single API router
"""
from fastapi import APIRouter

# Phase 1 Modules (Core)
from modules.journeys.router import router as journeys_router
from modules.communications.router import router as communications_router
from modules.tickets.router import router as tickets_router

# Phase 2 Modules (WhatsApp & Appointments)
from modules.webhooks.router import router as webhooks_router
from modules.conversations.router import router as conversations_router
from modules.appointments.router import router as appointments_router
from modules.n8n_integration.router import router as n8n_router

# Phase 3 Modules (Supporting Features)
from modules.media.router import router as media_router
from modules.patients.router import router as patients_router
from modules.notifications.router import router as notifications_router
from modules.practitioners.router import router as practitioners_router

# Phase 4 Modules (Final Features)
from modules.vector.router import router as vector_router
from modules.agents.router import router as agents_router
from modules.intake.router import router as intake_router

# Phase 5 Modules (Analytics, Reports, Integrations)
from modules.analytics.router import router as analytics_router
from modules.reports.router import router as reports_router
from modules.voice_webhooks.router import router as voice_webhooks_router
from modules.whatsapp_webhooks.router import router as whatsapp_webhooks_router

# Phase 6 Modules (Authentication & Security)
from modules.auth.router import router as auth_router

# FHIR Module (Standards-based API)
from modules.fhir.router import router as fhir_router

# Clinical Workflows Module (EPIC-006)
from modules.clinical_workflows.router import router as clinical_workflows_router

# Telehealth Platform Module (EPIC-007)
from modules.telehealth.router import router as telehealth_router

# Insurance & Billing Module (EPIC-008)
from modules.billing.router import router as billing_router

# AI Platform Module (EPIC-009)
from modules.ai.router import router as ai_router

# Medical AI Module (EPIC-010)
from modules.medical_ai.router import router as medical_ai_router

# Advanced Analytics Platform Module (EPIC-011)
from modules.advanced_analytics.router import router as advanced_analytics_router

# Intelligent Automation Platform Module (EPIC-012)
from modules.automation.router import router as automation_router

# Omnichannel Communications Platform Module (EPIC-013)
from modules.omnichannel.router import router as omnichannel_router

# Patient Portal Platform Module (EPIC-014)
from modules.patient_portal.router import router as patient_portal_router

# Provider Collaboration Platform Module (EPIC-015)
from modules.provider_collaboration.router import router as provider_collaboration_router

# Mobile Applications Platform Module (EPIC-016)
from modules.mobile.router import router as mobile_router

# Revenue Infrastructure Platform Module (EPIC-017)
from modules.revenue.router import router as revenue_router

# API Marketplace & Developer Platform Module (EPIC-018)
from modules.marketplace.router import router as marketplace_router


# Create main API router
api_router = APIRouter(prefix="/api/v1/prm")

# ==================== Phase 1 Modules ====================
api_router.include_router(journeys_router)
api_router.include_router(communications_router)
api_router.include_router(tickets_router)

# ==================== Phase 2 Modules ====================
api_router.include_router(webhooks_router)
api_router.include_router(conversations_router)
api_router.include_router(appointments_router)
api_router.include_router(n8n_router)

# ==================== Phase 3 Modules ====================
api_router.include_router(media_router)
api_router.include_router(patients_router)
api_router.include_router(notifications_router)
api_router.include_router(practitioners_router)

# ==================== Phase 4 Modules ====================
api_router.include_router(vector_router)
api_router.include_router(agents_router)
api_router.include_router(intake_router)

# ==================== Phase 5 Modules ====================
api_router.include_router(analytics_router)
api_router.include_router(reports_router)
api_router.include_router(voice_webhooks_router)
api_router.include_router(whatsapp_webhooks_router)

# ==================== Phase 6 Modules ====================
api_router.include_router(auth_router)

# ==================== FHIR Module ====================
# Note: FHIR router has its own /fhir prefix, so it appears at /api/v1/prm/fhir
api_router.include_router(fhir_router)

# ==================== Clinical Workflows Module (EPIC-006) ====================
# Clinical workflows: prescriptions, lab orders, imaging, referrals, documentation,
# care plans, decision support, vital signs, and discharge management
api_router.include_router(clinical_workflows_router)

# ==================== Telehealth Platform Module (EPIC-007) ====================
# Telehealth: video consultation, virtual waiting room, scheduling,
# session recording, payments, analytics, and interpreter services
api_router.include_router(telehealth_router)

# ==================== Insurance & Billing Module (EPIC-008) ====================
# Billing: insurance eligibility, prior authorization, claims generation,
# payment processing, patient billing, fee schedules, contracts, and analytics
api_router.include_router(billing_router)

# ==================== AI Platform Module (EPIC-009) ====================
# AI: chat completions, conversations, medical triage, NLP entity extraction,
# knowledge base, PHI protection, documentation generation, monitoring, and experiments
api_router.include_router(ai_router)

# ==================== Medical AI Module (EPIC-010) ====================
# Medical AI: advanced triage, clinical documentation AI, medical entity recognition,
# clinical decision intelligence, predictive analytics, medical image analysis,
# clinical NLP pipeline, and voice biomarker analysis
api_router.include_router(medical_ai_router)

# ==================== Advanced Analytics Platform Module (EPIC-011) ====================
# Advanced Analytics: executive dashboards, clinical quality analytics, population health,
# financial analytics, operational efficiency, predictive analytics engine,
# and custom report builder
api_router.include_router(advanced_analytics_router)

# ==================== Intelligent Automation Platform Module (EPIC-012) ====================
# Intelligent Automation: workflow engine, appointment optimization, care gap detection,
# document processing, patient outreach campaigns, clinical task automation,
# revenue cycle automation, and human-in-the-loop task management
api_router.include_router(automation_router)

# ==================== Omnichannel Communications Platform Module (EPIC-013) ====================
# Omnichannel Communications: multi-channel messaging (WhatsApp, SMS, Email, Voice),
# unified conversation management, communication preferences, consent tracking,
# campaign management, unified inbox, and HIPAA-compliant audit logging
api_router.include_router(omnichannel_router)

# ==================== Patient Portal Platform Module (EPIC-014) ====================
# Patient Portal: user registration and authentication, health records access,
# appointment management, secure messaging, billing and payments,
# prescription refills, proxy access management, and HIPAA-compliant audit logging
api_router.include_router(patient_portal_router)

# ==================== Provider Collaboration Platform Module (EPIC-015) ====================
# Provider Collaboration: real-time provider messaging, presence tracking,
# specialist consultation management, care team coordination, SBAR shift handoffs,
# on-call schedule management, clinical alerts, and case discussions
api_router.include_router(provider_collaboration_router)

# ==================== Mobile Applications Platform Module (EPIC-016) ====================
# Mobile Applications: device registration, push notifications (FCM/APNs),
# offline-first sync with delta updates, wearable device integration,
# health metrics and goals tracking, biometric authentication, mobile sessions
api_router.include_router(mobile_router)

# ==================== Revenue Infrastructure Platform Module (EPIC-017) ====================
# Revenue Infrastructure: subscription management, usage metering, Stripe payment processing,
# invoice generation, dunning and collections, ASC 606 revenue recognition,
# customer billing portal, and SaaS metrics (MRR, ARR, churn, LTV)
api_router.include_router(revenue_router)

# ==================== API Marketplace & Developer Platform Module (EPIC-018) ====================
# API Marketplace: developer portal registration, OAuth 2.0 & SMART on FHIR authentication,
# API gateway with rate limiting & circuit breaker, marketplace app catalog with reviews,
# app publishing workflow with version management, SDK documentation & code samples
api_router.include_router(marketplace_router)
