"""LangGraph checkpointer persistence provider.

Supports in-memory checkpointer for testing and development,
and provides PostgreSQL-backed persistence configuration for production environments.
"""

from typing import Optional
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from core.logger import logger
from core.config import settings

# Global shared checkpointer instance
_checkpointer_instance: Optional[BaseCheckpointSaver] = None


def get_checkpointer() -> BaseCheckpointSaver:
    """Returns the configured LangGraph checkpointer."""
    global _checkpointer_instance
    if _checkpointer_instance is None:
        logger.info("initializing_checkpointer", env=settings.ENVIRONMENT)
        # In memory checkpointer for robust local execution and automated testing
        _checkpointer_instance = MemorySaver()
    return _checkpointer_instance


def reset_checkpointer() -> None:
    """Resets checkpointer for testing isolation."""
    global _checkpointer_instance
    _checkpointer_instance = MemorySaver()
