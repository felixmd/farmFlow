"""
Memory Service - Singleton Pattern for Vertex AI Memory Bank

Provides centralized access to Memory Bank for all agents.
"""

import os
import logging
from dotenv import load_dotenv
from google.adk.memory import VertexAiMemoryBankService

load_dotenv()

logger = logging.getLogger(__name__)

# Singleton instance
_memory_service_instance = None


def get_memory_service():
    """
    Get or create the singleton Memory Bank service instance.

    Returns:
        VertexAiMemoryBankService: Configured memory service, or None if not available
    """
    global _memory_service_instance

    if _memory_service_instance is not None:
        return _memory_service_instance

    # Check required environment variables
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    agent_engine_id = os.getenv("AGENT_ENGINE_ID")

    if not all([project, location, agent_engine_id]):
        logger.warning(
            "[MemoryService] Memory Bank not configured. "
            "Missing: GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, or AGENT_ENGINE_ID"
        )
        return None

    try:
        logger.info(f"[MemoryService] Initializing Memory Bank (Engine: {agent_engine_id})")

        _memory_service_instance = VertexAiMemoryBankService(
            project=project,
            location=location,
            agent_engine_id=agent_engine_id
        )

        logger.info("[MemoryService] Memory Bank service initialized successfully")
        return _memory_service_instance

    except Exception as e:
        logger.error(f"[MemoryService] Failed to initialize Memory Bank: {e}", exc_info=True)
        return None


def is_memory_available():
    """
    Check if Memory Bank service is available.

    Returns:
        bool: True if memory service is configured and ready
    """
    return get_memory_service() is not None
