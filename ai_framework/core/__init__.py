"""
AI Framework Core Module

This module provides the foundational components for the AI agent framework:
- Multi-LLM integration and management
- Intelligent model routing
- Agent orchestration
- Memory and context management
"""

__version__ = "1.0.0"
__author__ = "AI Framework Team"

from .agent_orchestrator import AgentOrchestrator
from .llm_manager import LLMManager
from .memory_manager import MemoryManager
from .model_router import ModelRouter

# Make OSS20B manager optional to prevent import errors
try:
    from .oss20b_manager import OSS20BManager
    OSS20B_AVAILABLE = True
except ImportError:
    OSS20B_AVAILABLE = False
    OSS20BManager = None

__all__ = [
    "LLMManager",
    "ModelRouter",
    "AgentOrchestrator",
    "MemoryManager",
]

# Add OSS20B manager only if available
if OSS20B_AVAILABLE:
    __all__.append("OSS20BManager")
