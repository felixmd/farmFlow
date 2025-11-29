"""
Orchestrator Agent

The central hub that routes user queries to appropriate specialist agents.
"""

from .orchestrator import root_agent, route_query

__all__ = ['root_agent', 'route_query']
