"""Konseho: Multi-agent council framework built on Strands Agents SDK."""

import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Core exports
# Agent exports
from .agents.base import AgentWrapper
from .agents.human import HumanAgent
from .core.context import Context
from .core.council import Council
from .core.steps import DebateStep, ParallelStep, SplitStep, Step
from .dynamic.analyzer import QueryAnalyzer, TaskType

# Dynamic council exports
from .dynamic.builder import DynamicCouncilBuilder, create_dynamic_council

# Execution exports
from .execution.events import EventEmitter
from .execution.executor import AsyncExecutor

# Interface exports
from .interface.chat import ChatInterface

__version__ = "0.1.0"

__all__ = [
    # Core
    "Council",
    "Context", 
    "Step",
    "DebateStep",
    "ParallelStep",
    "SplitStep",
    # Agents
    "AgentWrapper",
    "HumanAgent",
    # Execution
    "EventEmitter",
    "AsyncExecutor",
    # Interface
    "ChatInterface",
    # Dynamic
    "DynamicCouncilBuilder",
    "create_dynamic_council",
    "QueryAnalyzer",
    "TaskType",
]