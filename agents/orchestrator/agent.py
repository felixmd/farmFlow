"""
Orchestrator Agent Entry Point

This file serves as the standard ADK entry point that imports and exposes root_agent.
ADK web server looks for 'agent.py' with 'root_agent' variable.
"""

from orchestrator import root_agent, route_query

__all__ = ['root_agent', 'route_query']
