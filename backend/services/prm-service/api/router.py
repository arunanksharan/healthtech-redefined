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

# Phase 4 Modules (Final Features)
from modules.vector.router import router as vector_router
from modules.agents.router import router as agents_router
from modules.intake.router import router as intake_router


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

# ==================== Phase 4 Modules ====================
api_router.include_router(vector_router)
api_router.include_router(agents_router)
api_router.include_router(intake_router)
