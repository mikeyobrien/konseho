"""Step planner that uses model-generated workflow specifications."""
from __future__ import annotations

from typing import Any, Callable
from konseho.protocols import JSON
from ..agents.base import AgentWrapper
from ..core.steps import DebateStep, ParallelStep, SplitStep, Step


class ModelStepPlanner:
    """Creates workflow steps from model-generated specifications."""

    def create_steps_from_spec(self, workflow_specs: list[dict[str, JSON]],
        agents: list[AgentWrapper]) ->list[Step]:
        """Create steps from model-generated workflow specification.

        Args:
            workflow_specs: List of workflow step specifications
            agents: List of available agents

        Returns:
            List of configured steps
        """
        agent_map = {agent.name: agent for agent in agents}
        steps: list[Step] = []
        for spec in workflow_specs:
            step_type = spec.get('type', 'debate')
            description = spec.get('description', '')
            participants = spec.get('participants', [])
            
            # Type narrowing for values from JSON
            if not isinstance(step_type, str):
                step_type = 'debate'
            if not isinstance(description, str):
                description = ''
            if not isinstance(participants, list):
                participants = []
            
            participant_names = [p for p in participants if isinstance(p, str)]
            step_agents = [agent_map[name] for name in participant_names if name in
                agent_map]
            if not step_agents:
                step_agents = agents
            
            # Create appropriate step type
            step: Step
            if step_type == 'debate':
                step = DebateStep(agents=step_agents, rounds=self.
                    _determine_rounds(description), voting_strategy=self.
                    _determine_voting_strategy(len(step_agents)))
            elif step_type == 'parallel':
                step = ParallelStep(agents=step_agents, task_splitter=self.
                    _create_task_splitter(description, participant_names))
            elif step_type == 'split':
                step = SplitStep(agent_template=step_agents[0].agent if
                    step_agents else agents[0].agent, max_agents=min(len(
                    participant_names), 4) if participant_names else 3)
            else:
                step = DebateStep(agents=step_agents)
            # Store description as step metadata (public API)
            step.metadata = {'description': description}
            steps.append(step)
        return steps

    def _determine_rounds(self, description: str) ->int:
        """Determine number of debate rounds based on description."""
        description_lower = description.lower()
        if 'final' in description_lower or 'integration' in description_lower:
            return 1
        elif 'detailed' in description_lower or 'thorough' in description_lower:
            return 3
        else:
            return 2

    def _determine_voting_strategy(self, num_agents: int) ->str:
        """Determine voting strategy based on number of agents."""
        if num_agents == 2:
            return 'consensus'
        elif num_agents > 4:
            return 'weighted'
        else:
            return 'majority'

    def _create_task_splitter(self, description: str, participants: list[str]
        ) ->Callable[[str, int], list[str]]:
        """Create a task splitter function for parallel steps."""

        def splitter(task: str, n: int) ->list[str]:
            """Split task based on participant roles."""
            if len(participants) == n:
                tasks = []
                for participant in participants[:n]:
                    if 'review' in description.lower():
                        tasks.append(
                            f'As {participant}, review and analyze: {task}')
                    elif 'design' in description.lower():
                        tasks.append(
                            f'As {participant}, design your component for: {task}'
                            )
                    elif 'implement' in description.lower():
                        tasks.append(
                            f'As {participant}, implement your part of: {task}'
                            )
                    else:
                        tasks.append(f'As {participant}, work on: {task}')
                return tasks
            else:
                return [f'Work on aspect {i + 1} of: {task}' for i in range(n)]
        return splitter
