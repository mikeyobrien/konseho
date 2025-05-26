"""Konseho: Multi-agent council framework built on Strands Agents SDK."""

import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Core exports
from .core.council import Council
from .core.context import Context
from .core.steps import Step, DebateStep, ParallelStep, SplitStep

# Agent exports
from .agents.base import AgentWrapper
from .agents.human import HumanAgent

# Execution exports
from .execution.events import EventEmitter
from .execution.executor import AsyncExecutor

# Interface exports
from .interface.chat import ChatInterface

# Dynamic council exports
from .dynamic.builder import DynamicCouncilBuilder, create_dynamic_council
from .dynamic.analyzer import QueryAnalyzer, TaskType

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