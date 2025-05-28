"""Council orchestrator for managing multi-agent workflows."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from strands import Agent
from ..agents.base import AgentWrapper
from ..factories import CouncilDependencies
from ..protocols import IAgent, IStepResult
from .error_handler import ErrorHandler, ErrorStrategy
from .moderator_assigner import ModeratorAssigner
from .step_orchestrator import StepOrchestrator
from .steps import DebateStep, Step
logger = logging.getLogger(__name__)


class Council:
    __slots__ = ()
    """Coordinates multi-agent workflows through composition of specialized components."""

    def __init__(self, name: str='council', steps: (list[Step] | None)=None,
        agents: (list[Agent | AgentWrapper] | None)=None, dependencies: (
        CouncilDependencies | None)=None, error_strategy: str='halt',
        workflow: str='sequential', max_retries: int=3):
        """Initialize a council.

        Args:
            name: Council identifier
            steps: Ordered list of execution steps
            agents: List of agents (creates a DebateStep if provided without steps)
            dependencies: Container with all dependencies (required)
            error_strategy: How to handle errors (halt, continue, retry, fallback)
            workflow: Workflow type (sequential, iterative)
            max_retries: Maximum retry attempts for retry strategy
        """
        if dependencies is None:
            raise ValueError(
                'Council requires dependencies. Use CouncilFactory or provide CouncilDependencies.'
                )
        self.name = name
        self.workflow = workflow
        self.dependencies = dependencies
        self.context = dependencies.context
        self._event_emitter = dependencies.event_emitter
        self.output_manager = dependencies.output_manager
        self.save_outputs = dependencies.output_manager is not None
        if steps is not None:
            self.steps = steps
        elif agents is not None:
            self.steps = [DebateStep(agents)]
        else:
            self.steps = []
        self._error_handler = ErrorHandler(error_strategy=ErrorStrategy(
            error_strategy), max_retries=max_retries, event_emitter=self.
            _event_emitter)
        self._step_orchestrator = StepOrchestrator(steps=self.steps,
            event_emitter=self._event_emitter, output_manager=self.
            output_manager, error_handler=self._error_handler)
        self._moderator_assigner = ModeratorAssigner()
        self._moderator_assigner.assign_moderators(self.steps)

    async def execute(self, task: str) ->dict[str, Any]:
        """Execute the council workflow with the given task.

        Args:
            task: The task to execute

        Returns:
            Summary of execution results
        """
        results = await self._step_orchestrator.execute_steps(task, self.
            context, self.name)
        final_result = self._prepare_final_result(task, results)
        if self.save_outputs:
            await self._save_output(task, final_result)
        return final_result

    def run(self, task: str) ->dict[str, Any]:
        """Synchronous wrapper for execute.

        Args:
            task: The task to execute

        Returns:
            Summary of execution results
        """
        return asyncio.run(self.execute(task))

    async def stream_execute(self, task: str):
        """Execute the council workflow with streaming events.

        Args:
            task: The task to execute

        Yields:
            CouncilEvent: Events as they occur during execution
        """
        result = await self.execute(task)
        yield {'type': 'complete', 'result': result}

    def add_step(self, step: Step) ->None:
        """Add a step to the council workflow.

        Args:
            step: The step to add
        """
        self.steps.append(step)
        self._step_orchestrator.steps = self.steps
        self._moderator_assigner.assign_moderators([step])

    def set_moderator_pool(self, agents: list[IAgent]) ->None:
        """Set the pool of agents that can act as moderators.

        Args:
            agents: List of agents to use as moderators
        """
        self._moderator_assigner.set_moderator_pool(agents)
        self._moderator_assigner.assign_moderators(self.steps)

    def set_fallback_handler(self, handler) ->None:
        """Set a custom fallback handler for error handling.

        Args:
            handler: Callable that handles fallback scenarios
        """
        self._error_handler.fallback_handler = handler

    def _prepare_final_result(self, task: str, results: list[IStepResult]
        ) ->dict[str, Any]:
        """Prepare the final result summary.

        Args:
            task: The original task
            results: List of step results

        Returns:
            Summary dictionary
        """
        summary = self.context.get_summary()
        summary.update({'council': self.name, 'task': task, 'workflow':
            self.workflow, 'steps_completed': len(results),
            'agents_involved': self._get_agent_names()})
        return summary

    async def _save_output(self, task: str, result: dict[str, Any]) ->None:
        """Save the council output.

        Args:
            task: The original task
            result: The final result to save
        """
        if not self.output_manager:
            return
        try:
            metadata = {'error_strategy': self._error_handler.
                error_strategy.value, 'workflow': self.workflow,
                'num_steps': len(self.steps), 'agents': self._get_agent_names()
                }
            output_path = self.output_manager.save_formatted_output(task=
                task, result=result, council_name=self.name, metadata=metadata)
            logger.info(f'Council output saved to: {output_path}')
            if self._event_emitter:
                self._event_emitter.emit('output:saved', {'path': str(
                    output_path)})
        except Exception as e:
            logger.error(f'Failed to save output: {e}')

    def _get_agent_names(self) ->list[str]:
        """Get names of all agents in the council.

        Returns:
            List of unique agent names
        """
        agent_names = []
        for step in self.steps:
            if hasattr(step, 'agents'):
                for agent in step.agents:
                    if hasattr(agent, 'name'):
                        agent_names.append(agent.name)
                    else:
                        agent_names.append(str(agent))
        return list(set(agent_names))
