"""Strategies for parallel step execution."""

import asyncio
from abc import ABC, abstractmethod

from konseho.protocols import IAgent, IContext


class ParallelStrategy(ABC):
    """Abstract base for parallel execution strategies."""

    @abstractmethod
    async def execute_parallel(
        self,
        agents: list[IAgent],
        task: str,
        context: IContext,
    ) -> dict[str, str]:
        """Execute task in parallel across agents.

        Args:
            agents: List of agents to execute with
            task: The task to execute
            context: Shared context

        Returns:
            Dictionary mapping agent/domain to results
        """
        pass

    @abstractmethod
    def merge_results(self, results: dict[str, str]) -> str:
        """Merge parallel results into a single output.

        Args:
            results: Dictionary of parallel results

        Returns:
            Merged output string
        """
        pass


class DomainParallelStrategy(ParallelStrategy):
    """Each agent handles a different domain/perspective."""

    def __init__(self, domains: list[str] | None = None):
        """Initialize domain parallel strategy.

        Args:
            domains: List of domains to assign to agents
        """
        self.domains = domains or ["technical", "business", "user", "security"]

    async def execute_parallel(
        self,
        agents: list[IAgent],
        task: str,
        context: IContext,
    ) -> dict[str, str]:
        """Execute task from different domain perspectives.

        Args:
            agents: List of agents
            task: The task to analyze
            context: Shared context

        Returns:
            Dictionary mapping domain to analysis
        """
        # Create domain-specific tasks
        tasks = []
        agent_domains = []

        for i, agent in enumerate(agents):
            domain = self.domains[i % len(self.domains)]
            domain_task = f"Analyze this from a {domain} perspective: {task}"
            tasks.append(agent.work_on(domain_task))
            agent_domains.append((agent.name, domain))

        # Execute in parallel
        results = await asyncio.gather(*tasks)

        # Map results to domains
        return {
            f"{agent_name} ({domain})": result
            for (agent_name, domain), result in zip(agent_domains, results, strict=True)
        }

    def merge_results(self, results: dict[str, str]) -> str:
        """Merge domain analyses into comprehensive output.

        Args:
            results: Dictionary of domain analyses

        Returns:
            Merged analysis
        """
        merged_parts = ["Multi-perspective Analysis:\n"]

        for domain_info, analysis in results.items():
            merged_parts.append(f"\n**{domain_info}:**")
            merged_parts.append(analysis)
            merged_parts.append("")  # Empty line between sections

        return "\n".join(merged_parts)


class TaskSplitStrategy(ParallelStrategy):
    """Split task into subtasks for parallel execution."""

    def __init__(self, split_method: str = "auto"):
        """Initialize task split strategy.

        Args:
            split_method: How to split tasks ("auto", "by_lines", "by_components")
        """
        self.split_method = split_method

    async def execute_parallel(
        self,
        agents: list[IAgent],
        task: str,
        context: IContext,
    ) -> dict[str, str]:
        """Split task and execute subtasks in parallel.

        Args:
            agents: List of agents
            task: The task to split
            context: Shared context

        Returns:
            Dictionary mapping subtask to result
        """
        # Split the task
        subtasks = self._split_task(task, len(agents))

        # Execute subtasks in parallel
        tasks = []
        for agent, subtask in zip(agents, subtasks, strict=False):
            tasks.append(agent.work_on(subtask))

        results = await asyncio.gather(*tasks)

        # Map results
        return {f"Subtask {i+1}": result for i, result in enumerate(results)}

    def merge_results(self, results: dict[str, str]) -> str:
        """Merge subtask results.

        Args:
            results: Dictionary of subtask results

        Returns:
            Combined result
        """
        merged_parts = ["Combined Results:\n"]

        for subtask_id, result in results.items():
            merged_parts.append(f"\n{subtask_id}:")
            merged_parts.append(result)

        return "\n".join(merged_parts)

    def _split_task(self, task: str, num_agents: int) -> list[str]:
        """Split task into subtasks.

        Args:
            task: The task to split
            num_agents: Number of subtasks needed

        Returns:
            List of subtasks
        """
        if self.split_method == "by_lines":
            lines = task.strip().split("\n")
            if len(lines) >= num_agents:
                # Distribute lines among agents
                lines_per_agent = len(lines) // num_agents
                subtasks = []
                for i in range(num_agents):
                    start = i * lines_per_agent
                    end = start + lines_per_agent if i < num_agents - 1 else len(lines)
                    subtasks.append("\n".join(lines[start:end]))
                return subtasks

        # Default: same task for all
        return [task] * num_agents


class LoadBalancedStrategy(ParallelStrategy):
    """Distribute work based on agent capabilities and load."""

    def __init__(self, capability_key: str = "expertise_level"):
        """Initialize load balanced strategy.

        Args:
            capability_key: Agent capability to use for load balancing
        """
        self.capability_key = capability_key

    async def execute_parallel(
        self,
        agents: list[IAgent],
        task: str,
        context: IContext,
    ) -> dict[str, str]:
        """Execute with load balancing based on capabilities.

        Args:
            agents: List of agents
            task: The task to execute
            context: Shared context

        Returns:
            Dictionary mapping agent to result
        """
        # Get agent capabilities
        agent_loads = []
        for agent in agents:
            capabilities = agent.get_capabilities()
            load_factor = capabilities.get(self.capability_key, 1.0)
            agent_loads.append((agent, load_factor))

        # Sort by capability (higher capability = can handle more)
        agent_loads.sort(key=lambda x: x[1], reverse=True)

        # Assign tasks based on capability
        tasks = []
        for agent, load_factor in agent_loads:
            # More capable agents get slightly modified prompts
            if load_factor > 0.7:
                agent_task = f"{task} (Provide comprehensive analysis)"
            else:
                agent_task = f"{task} (Focus on key points)"

            tasks.append(agent.work_on(agent_task))

        results = await asyncio.gather(*tasks)

        # Map results
        return {
            agent.name: result
            for (agent, _), result in zip(agent_loads, results, strict=True)
        }

    def merge_results(self, results: dict[str, str]) -> str:
        """Merge load-balanced results.

        Args:
            results: Dictionary of agent results

        Returns:
            Merged output
        """
        # Combine all results with agent attribution
        merged_parts = ["Collaborative Analysis:\n"]

        for agent_name, result in results.items():
            merged_parts.append(f"\n[{agent_name}]:")
            merged_parts.append(result)

        return "\n".join(merged_parts)

