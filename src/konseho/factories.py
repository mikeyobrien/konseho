"""Factory classes for dependency injection in Konseho.

from __future__ import annotations

This module provides factory patterns to create Council instances with
proper dependency injection, making the code more testable and maintainable.
"""
from pathlib import Path
from typing import Any
from konseho.core.context import Context
from konseho.core.output_manager import OutputManager
from konseho.execution.events import EventEmitter
from konseho.protocols import IAgent, IContext, IEventEmitter, IOutputManager, IStep


class CouncilDependencies:
    """Container for Council dependencies.

    This class holds all the dependencies that a Council needs,
    allowing for easy substitution during testing or runtime.
    """

    def __init__(self, context: (IContext | None)=None, event_emitter: (
        IEventEmitter | None)=None, output_manager: (IOutputManager | None)
        =None):
        """Initialize dependencies container.

        Args:
            context: Context implementation (defaults to Context)
            event_emitter: Event emitter implementation (defaults to EventEmitter)
            output_manager: Output manager implementation (optional)
        """
        self.context = context or Context()
        self.event_emitter = event_emitter or EventEmitter()
        self.output_manager = output_manager

    @classmethod
    def with_output_manager(cls, output_dir: (str | Path)='council_outputs',
        context: (IContext | None)=None, event_emitter: (IEventEmitter |
        None)=None) ->'CouncilDependencies':
        """Create dependencies with an output manager.

        Args:
            output_dir: Directory for saving outputs
            context: Context implementation
            event_emitter: Event emitter implementation

        Returns:
            CouncilDependencies instance with OutputManager
        """
        return cls(context=context, event_emitter=event_emitter,
            output_manager=OutputManager(output_dir))


class CouncilFactory:
    """Factory for creating Council instances with dependency injection."""

    def __init__(self, dependencies: (CouncilDependencies | None)=None):
        """Initialize the factory.

        Args:
            dependencies: Dependencies container (defaults to new instance)
        """
        self.dependencies = dependencies or CouncilDependencies()

    def create_council(self, name: str='council', steps: (list[IStep] |
        None)=None, agents: (list[IAgent] | None)=None, error_strategy: str
        ='halt', workflow: str='sequential', save_outputs: bool=False,
        output_dir: (str | Path | None)=None) ->Any:
        """Create a Council instance with injected dependencies.

        Args:
            name: Council identifier
            steps: Ordered list of execution steps
            agents: List of agents (creates DebateStep if provided without steps)
            error_strategy: How to handle errors (halt, continue, retry, fallback)
            workflow: Workflow type (sequential, iterative)
            save_outputs: Whether to automatically save outputs
            output_dir: Directory for saving outputs

        Returns:
            Council instance with injected dependencies
        """
        from konseho.core.council import Council
        dependencies = self.dependencies
        if save_outputs and not dependencies.output_manager:
            dependencies = CouncilDependencies.with_output_manager(output_dir
                =output_dir or 'council_outputs', context=dependencies.
                context, event_emitter=dependencies.event_emitter)
        return Council(name=name, steps=steps, agents=agents, dependencies=
            dependencies, error_strategy=error_strategy, workflow=workflow)

    def create_test_council(self, name: str='test_council', mock_context: (
        IContext | None)=None, mock_event_emitter: (IEventEmitter | None)=
        None, mock_output_manager: (IOutputManager | None)=None, **kwargs
        ) ->Any:
        """Create a Council for testing with mock dependencies.

        Args:
            name: Council identifier
            mock_context: Mock context for testing
            mock_event_emitter: Mock event emitter for testing
            mock_output_manager: Mock output manager for testing
            **kwargs: Additional arguments passed to Council

        Returns:
            Council instance with mock dependencies
        """
        test_deps = CouncilDependencies(context=mock_context, event_emitter
            =mock_event_emitter, output_manager=mock_output_manager)
        self.dependencies = test_deps
        return self.create_council(name=name, **kwargs)
