"""Factory for creating configured steps easily."""


from konseho.protocols import IAgent

from .debate_components import (
    MajorityVoting,
    VotingStrategy,
    WeightedVoting,
)
from .parallel_strategies import (
    DomainParallelStrategy,
    LoadBalancedStrategy,
    ParallelStrategy,
    TaskSplitStrategy,
)
from .steps_v2 import DebateConfig, DebateStep, ParallelStep


class StepFactory:
    """Factory for creating configured steps with sensible defaults."""

    @staticmethod
    def debate(
        agents: list[IAgent],
        voting: VotingStrategy | None = None,
        moderator: IAgent | None = None,
        rounds: int = 2,
    ) -> DebateStep:
        """Create a debate step with configuration.

        Args:
            agents: List of agents to participate
            voting: Voting strategy (defaults to MajorityVoting)
            moderator: Optional moderator agent
            rounds: Number of debate rounds

        Returns:
            Configured DebateStep

        Example:
            >>> step = StepFactory.debate(agents, voting=WeightedVoting())
        """
        config = DebateConfig(
            voting_strategy=voting or MajorityVoting(),
            moderator=moderator,
            rounds=rounds,
        )
        return DebateStep(agents, config)

    @staticmethod
    def parallel(
        agents: list[IAgent],
        strategy: ParallelStrategy | None = None,
    ) -> ParallelStep:
        """Create a parallel step with strategy.

        Args:
            agents: List of agents to work in parallel
            strategy: Execution strategy (defaults to DomainParallelStrategy)

        Returns:
            Configured ParallelStep

        Example:
            >>> step = StepFactory.parallel(agents, strategy=TaskSplitStrategy())
        """
        return ParallelStep(agents, strategy)

    @staticmethod
    def domain_parallel(
        agents: list[IAgent],
        domains: list[str] | None = None,
    ) -> ParallelStep:
        """Create a parallel step with domain-based execution.

        Args:
            agents: List of agents
            domains: List of domains to analyze from

        Returns:
            ParallelStep with domain strategy

        Example:
            >>> step = StepFactory.domain_parallel(
            ...     agents,
            ...     domains=["security", "performance", "usability"]
            ... )
        """
        strategy = DomainParallelStrategy(domains)
        return ParallelStep(agents, strategy)

    @staticmethod
    def task_split(
        agents: list[IAgent],
        split_method: str = "auto",
    ) -> ParallelStep:
        """Create a parallel step that splits tasks.

        Args:
            agents: List of agents
            split_method: How to split tasks

        Returns:
            ParallelStep with task splitting

        Example:
            >>> step = StepFactory.task_split(agents, split_method="by_lines")
        """
        strategy = TaskSplitStrategy(split_method)
        return ParallelStep(agents, strategy)

    @staticmethod
    def load_balanced(
        agents: list[IAgent],
        capability_key: str = "expertise_level",
    ) -> ParallelStep:
        """Create a load-balanced parallel step.

        Args:
            agents: List of agents
            capability_key: Agent capability to use for balancing

        Returns:
            ParallelStep with load balancing

        Example:
            >>> step = StepFactory.load_balanced(agents)
        """
        strategy = LoadBalancedStrategy(capability_key)
        return ParallelStep(agents, strategy)

    @staticmethod
    def consensus_debate(
        agents: list[IAgent],
        moderator: IAgent | None = None,
        max_rounds: int = 5,
    ) -> DebateStep:
        """Create a debate step aiming for consensus.

        Args:
            agents: List of agents
            moderator: Optional moderator
            max_rounds: Maximum debate rounds

        Returns:
            DebateStep configured for consensus

        Example:
            >>> step = StepFactory.consensus_debate(agents, moderator=moderator_agent)
        """
        # Use majority voting but with more rounds for consensus
        config = DebateConfig(
            voting_strategy=MajorityVoting(),
            moderator=moderator,
            rounds=max_rounds,
        )
        return DebateStep(agents, config)

    @staticmethod
    def weighted_debate(
        agents: list[IAgent],
        weights: dict[str, float],
        moderator: IAgent | None = None,
        rounds: int = 2,
    ) -> DebateStep:
        """Create a debate with weighted voting.

        Args:
            agents: List of agents
            weights: Dictionary of agent name to weight
            moderator: Optional moderator
            rounds: Number of debate rounds

        Returns:
            DebateStep with weighted voting

        Example:
            >>> weights = {"expert_agent": 2.0, "junior_agent": 0.5}
            >>> step = StepFactory.weighted_debate(agents, weights)
        """
        config = DebateConfig(
            voting_strategy=WeightedVoting(weights),
            moderator=moderator,
            rounds=rounds,
        )
        return DebateStep(agents, config)

