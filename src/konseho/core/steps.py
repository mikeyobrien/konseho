"""Step implementations for different agent coordination patterns."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
import asyncio
import logging

from strands import Agent
from .context import Context
from ..agents.base import AgentWrapper

logger = logging.getLogger(__name__)


class Step(ABC):
    """Base class for all execution steps."""
    
    @abstractmethod
    async def execute(self, task: str, context: Context) -> Dict[str, Any]:
        """Execute the step with given task and context."""
        pass


class DebateStep(Step):
    """Agents propose competing solutions and vote on the best one."""
    
    def __init__(
        self,
        agents: List[AgentWrapper],
        moderator: Optional[AgentWrapper] = None,
        rounds: int = 2,
        voting_strategy: str = "majority"
    ):
        """Initialize debate step.
        
        Args:
            agents: List of agents participating in the debate
            moderator: Optional moderator agent
            rounds: Number of debate rounds
            voting_strategy: How to determine winner (majority, consensus, moderator)
        """
        self.agents = agents
        self.moderator = moderator
        self.rounds = rounds
        self.voting_strategy = voting_strategy
    
    async def execute(self, task: str, context: Context) -> Dict[str, Any]:
        """Execute the debate process."""
        proposals = {}
        
        # Initial proposals
        proposal_tasks = []
        for agent in self.agents:
            prompt = f"{task}\n\n{context.to_prompt_context()}"
            proposal_tasks.append(self._get_proposal(agent, prompt))
        
        initial_proposals = await asyncio.gather(*proposal_tasks)
        for agent, proposal in zip(self.agents, initial_proposals):
            proposals[agent.name] = proposal
        
        # Debate rounds
        for round_num in range(self.rounds):
            debate_context = self._create_debate_prompt(proposals, round_num)
            
            debate_tasks = []
            for agent in self.agents:
                prompt = f"{debate_context}\n\nProvide your updated proposal or critique others."
                debate_tasks.append(self._get_proposal(agent, prompt))
            
            round_responses = await asyncio.gather(*debate_tasks)
            for agent, response in zip(self.agents, round_responses):
                proposals[f"{agent.name}_round_{round_num}"] = response
        
        # Vote or select winner
        winner = await self._select_winner(proposals, task, context)
        
        return {
            "winner": winner,
            "proposals": proposals,
            "strategy": self.voting_strategy
        }
    
    async def _get_proposal(self, agent: AgentWrapper, prompt: str) -> str:
        """Get a proposal from an agent."""
        return await agent.work_on(prompt)
    
    def _create_debate_prompt(self, proposals: Dict[str, str], round_num: int) -> str:
        """Create a prompt summarizing the debate so far."""
        prompt = f"Debate Round {round_num + 1}\n\nCurrent Proposals:\n"
        for name, proposal in proposals.items():
            if not name.endswith(f"_round_{round_num}"):  # Skip future rounds
                prompt += f"\n{name}:\n{proposal[:500]}...\n"
        return prompt
    
    async def _select_winner(self, proposals: Dict[str, str], task: str, context: Context) -> str:
        """Select the winning proposal based on voting strategy."""
        if self.voting_strategy == "moderator" and self.moderator:
            prompt = f"Select the best proposal for: {task}\n\nProposals:\n"
            for name, proposal in proposals.items():
                if "_round_" not in name:  # Original proposals only
                    prompt += f"\n{name}: {proposal[:300]}...\n"
            winner = await self.moderator.work_on(prompt)
            return winner
        
        # Simple implementation: return the first proposal
        # In a real implementation, implement voting logic
        return list(proposals.values())[0]


class ParallelStep(Step):
    """Agents work on different aspects simultaneously."""
    
    def __init__(self, agents: List[AgentWrapper], task_splitter: Optional[Callable] = None):
        """Initialize parallel step.
        
        Args:
            agents: List of agents to work in parallel
            task_splitter: Optional function to split task into subtasks
        """
        self.agents = agents
        self.task_splitter = task_splitter
    
    async def execute(self, task: str, context: Context) -> Dict[str, Any]:
        """Execute agents in parallel."""
        if self.task_splitter:
            subtasks = self.task_splitter(task, len(self.agents))
        else:
            # Default: same task for all agents
            subtasks = [task] * len(self.agents)
        
        # Execute all agents in parallel
        tasks = []
        for agent, subtask in zip(self.agents, subtasks):
            prompt = f"{subtask}\n\n{context.to_prompt_context()}"
            tasks.append(agent.work_on(prompt))
        
        results = await asyncio.gather(*tasks)
        
        return {
            "parallel_results": {
                agent.name: result for agent, result in zip(self.agents, results)
            },
            "execution_time": "parallel"
        }


class SplitStep(Step):
    """Dynamically split work across multiple agent instances."""
    
    def __init__(
        self,
        agent_template: Agent,
        min_agents: int = 2,
        max_agents: int = 10,
        split_strategy: str = "auto"
    ):
        """Initialize split step.
        
        Args:
            agent_template: Template agent to clone
            min_agents: Minimum number of agents
            max_agents: Maximum number of agents
            split_strategy: How to determine split (auto, fixed, adaptive)
        """
        self.agent_template = agent_template
        self.min_agents = min_agents
        self.max_agents = max_agents
        self.split_strategy = split_strategy
    
    async def execute(self, task: str, context: Context) -> Dict[str, Any]:
        """Execute with dynamically created agents."""
        # Determine number of agents needed
        num_agents = self._determine_agent_count(task, context)
        
        # Create agent wrappers
        agents = []
        for i in range(num_agents):
            # In real implementation, properly clone the agent
            wrapper = AgentWrapper(
                agent=self.agent_template,
                name=f"split_agent_{i}"
            )
            agents.append(wrapper)
        
        # Split the work
        subtasks = self._split_task(task, num_agents)
        
        # Execute in parallel
        tasks = []
        for agent, subtask in zip(agents, subtasks):
            prompt = f"{subtask}\n\n{context.to_prompt_context()}"
            tasks.append(agent.work_on(prompt))
        
        results = await asyncio.gather(*tasks)
        
        return {
            "split_results": results,
            "num_agents": num_agents,
            "strategy": self.split_strategy
        }
    
    def _determine_agent_count(self, task: str, context: Context) -> int:
        """Determine how many agents to create."""
        if self.split_strategy == "fixed":
            return self.min_agents
        
        # Simple heuristic based on task length
        # In real implementation, use more sophisticated analysis
        task_complexity = len(task.split())
        num_agents = min(max(task_complexity // 50, self.min_agents), self.max_agents)
        return num_agents
    
    def _split_task(self, task: str, num_agents: int) -> List[str]:
        """Split task into subtasks."""
        # Simple implementation: duplicate task
        # In real implementation, intelligently split the task
        return [f"Part {i+1}/{num_agents}: {task}" for i in range(num_agents)]