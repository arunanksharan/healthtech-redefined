"""
AI Platform Module

Core AI integration for healthcare:
- LLM chat completions (GPT-4, Claude)
- Conversational AI with multi-turn support
- Medical triage and symptom assessment
- Clinical documentation generation
- Medical NLP and entity extraction
- Vector search for knowledge retrieval
- PHI protection and de-identification
- AI monitoring and observability
- A/B testing for AI features
- Cost tracking and alerts

EPIC-009: Core AI Integration
"""

from .router import router as ai_router

__all__ = ["ai_router"]
