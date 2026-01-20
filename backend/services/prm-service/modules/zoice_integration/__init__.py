"""
Zoice Integration Module

This module provides a proxy gateway to the Zoice telephony backend,
allowing the PRM dashboard to manage Zoice resources (pipelines, agents, calls)
through the PRM service using API key authentication.
"""

from .router import router

__all__ = ["router"]
