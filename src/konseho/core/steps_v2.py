"""Simplified step implementations following KISS and SOLID principles."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from konseho.protocols import IAgent, IContext, IStepResult

from .debate_components import (
    MajorityVoting,
    ProposalCollector,
    ProposalFormat,
    StandardFormat,
    VotingStrategy,
    VotingSystem,
)
from .parallel_strategies import (
    DomainParallelStrategy,
    ParallelStrategy,
)


@dataclass
class StepResult:
    """Simple result container for step execution."""

    output: str
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    success: bool = True


class Step(ABC):
    """Simplified base step - just the contract."""

    def __init__(self, agents: list[IAgent]):
        """Initialize step with agents.

        Args:
            agents: List of agents to use in the step
        """
        self.agents = agents

    @property
    def name(self) -> str:
        """Return the step name based on class name."""
        return self.__class__.__name__

    @abstractmethod
    async def execute(self, task: str, context: IContext) -> IStepResult:
        """Execute the step - implement in subclasses.

        Args:
            task: The task to execute
            context: Shared context for the execution

        Returns:
            Step execution result
        """
        pass

    def get_required_agents(self) -> int:
        """Override if step needs specific number of agents.

        Returns:
            Minimum number of agents required
        """
        return 1

    def validate(self) -> list[str]:
        """Validate step configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        required = self.get_required_agents()

        if len(self.agents) < required:
            errors.append(
                f"{self.name} requires at least {required} agents, "
                f"got {len(self.agents)}"
            )

        return errors


@dataclass
class DebateConfig:
    """Configuration for debate behavior."""

    voting_strategy: VotingStrategy = field(default_factory=MajorityVoting)
    proposal_format: ProposalFormat = field(default_factory=StandardFormat)
    moderator: IAgent | None = None
    rounds: int = 2
    allow_self_voting: bool = True


class DebateStep(Step):
    """Simplified debate step using composition."""

    def __init__(
        self,
        agents: list[IAgent],
        debate_config: DebateConfig | None = None,
    ):
        """Initialize debate step.

        Args:
            agents: List of agents participating in the debate
            debate_config: Configuration for debate behavior
        """
        super().__init__(agents)
        config = debate_config or DebateConfig()

        # Compose with single-purpose components
        self.proposal_collector = ProposalCollector(config.proposal_format)
        self.voting_system = VotingSystem(config.voting_strategy)
        self.moderator = config.moderator
        self.rounds = config.rounds

    async def execute(self, task: str, context: IContext) -> IStepResult:
        """Execute debate - simple orchestration.

        Args:
            task: The task to debate
            context: Shared context

        Returns:
            Step result with winning proposal
        """
        # 1. Collect initial proposals
        proposals = await self.proposal_collector.collect(
            self.agents, task, self.moderator
        )

        # 2. Conduct debate rounds
        for round_num in range(self.rounds):
            # Show current proposals to agents
            debate_prompt = self._create_debate_prompt(proposals, round_num, task)

            # Collect updated proposals
            round_proposals = await self.proposal_collector.collect(
                self.agents, debate_prompt, None  # No moderator guidance in rounds
            )

            # Update proposals
            for agent_name, proposal in round_proposals.items():
                proposals[f"{agent_name}_round_{round_num}"] = proposal

        # 3. Conduct voting on original proposals
        original_proposals = {
            name: prop for name, prop in proposals.items() if "_round_" not in name
        }
        winner = await self.voting_system.select_winner(self.agents, original_proposals)

        # 4. Return result
        return StepResult(
            output=winner,
            metadata={
                "winner": winner,
                "all_proposals": proposals,
                "vote_details": self.voting_system.last_vote_details,
                "rounds": self.rounds,
                "agents": [agent.name for agent in self.agents],
            },
        )

    def get_required_agents(self) -> int:
        """Debates need at least 2 agents."""
        return 2

    def validate(self) -> list[str]:
        """Validate debate configuration."""
        errors = super().validate()

        if self.rounds < 1:
            errors.append("Debate requires at least 1 round")

        return errors

    def _create_debate_prompt(
        self, proposals: dict[str, str], round_num: int, original_task: str
    ) -> str:
        """Create a prompt for debate rounds.

        Args:
            proposals: Current proposals
            round_num: Current round number
            original_task: The original task

        Returns:
            Formatted debate prompt
        """
        prompt_parts = [
            f"Debate Round {round_num + 1}",
            f"Original Task: {original_task}",
            "\nCurrent Proposals:",
        ]

        for name, proposal in proposals.items():
            if "_round_" not in name:  # Only show original proposals
                if len(proposal) > 300:
                    prompt_parts.append(f"\n{name}: {proposal[:300]}...")
                else:
                    prompt_parts.append(f"\n{name}: {proposal}")

        prompt_parts.append(
            "\nProvide your updated proposal or critique others' proposals."
        )

        return "\n".join(prompt_parts)


class ParallelStep(Step):
    """Simplified parallel step using strategy pattern."""

    def __init__(
        self,
        agents: list[IAgent],
        execution_strategy: ParallelStrategy | None = None,
    ):
        """Initialize parallel step.

        Args:
            agents: List of agents to work in parallel
            execution_strategy: Strategy for parallel execution
        """
        super().__init__(agents)
        self.strategy = execution_strategy or DomainParallelStrategy()

    async def execute(self, task: str, context: IContext) -> IStepResult:
        """Execute parallel work.

        Args:
            task: The task to execute
            context: Shared context

        Returns:
            Step result with merged output
        """
        # Execute in parallel using strategy
        results = await self.strategy.execute_parallel(self.agents, task, context)

        # Merge results
        merged_output = self.strategy.merge_results(results)

        return StepResult(
            output=merged_output,
            metadata={
                "individual_results": results,
                "strategy": self.strategy.__class__.__name__,
                "agents": [agent.name for agent in self.agents],
            },
        )

