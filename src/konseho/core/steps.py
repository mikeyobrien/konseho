"""Step implementations for different agent coordination patterns."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Tuple
import asyncio
import logging
import re
import random
from collections import Counter

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
    
    async def _collect_votes(self, proposals: Dict[str, str]) -> Tuple[Dict[str, str], int]:
        """Collect votes from all agents."""
        voting_prompt = "Vote for the best proposal. Reply with 'I vote for: [proposal name]' or 'I abstain from voting'\n\n"
        for name, proposal in proposals.items():
            # Handle proposals that might be shorter than 200 chars
            if len(proposal) > 200:
                voting_prompt += f"{name}: {proposal[:200]}...\n\n"
            else:
                voting_prompt += f"{name}: {proposal}\n\n"
        
        vote_tasks = []
        for agent in self.agents:
            vote_tasks.append(agent.work_on(voting_prompt))
        
        vote_responses = await asyncio.gather(*vote_tasks)
        
        votes = {}
        abstentions = 0
        
        for agent, response in zip(self.agents, vote_responses):
            vote = self._extract_vote(response, proposals)
            if vote == "ABSTAIN":
                abstentions += 1
            elif vote:
                votes[agent.name] = vote
        
        return votes, abstentions
    
    def _extract_vote(self, response: str, proposals: Dict[str, str]) -> Optional[str]:
        """Extract vote from agent response."""
        # Ensure response is a string
        if not isinstance(response, str):
            response = str(response)
        
        # Check for abstention
        if "abstain" in response.lower():
            return "ABSTAIN"
        
        # Look for "I vote for: X" pattern
        vote_match = re.search(r"I vote for:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
        if vote_match:
            voted_text = vote_match.group(1).strip()
            # Match to proposal
            for name, proposal in proposals.items():
                # Ensure proposal is a string
                proposal_str = str(proposal) if not isinstance(proposal, str) else proposal
                if name.lower() in voted_text.lower() or voted_text.lower() in proposal_str.lower():
                    return proposal
        
        return None
    
    def _count_majority_votes(self, votes: Dict[str, str], proposals: Dict[str, str], abstentions: int) -> Dict[str, Any]:
        """Count votes and determine winner by majority."""
        vote_counts = Counter(votes.values())
        
        # Initialize all proposals with 0 votes
        # Use proposal names as keys instead of proposal content to avoid unhashable dict issues
        proposal_votes = {name: 0 for name in proposals.keys()}
        
        # Count votes by matching proposal content
        for voter, voted_content in votes.items():
            for prop_name, prop_content in proposals.items():
                if str(prop_content) == str(voted_content):
                    proposal_votes[prop_name] += 1
                    break
        
        if not vote_counts:
            # No valid votes, return first proposal
            return {
                "winner": list(proposals.values())[0],
                "votes": proposal_votes,
                "abstentions": abstentions
            }
        
        # Get top voted proposals
        max_votes = max(vote_counts.values())
        winners = [prop for prop, count in vote_counts.items() if count == max_votes]
        
        if len(winners) > 1:
            # Tie - use first proposal as tiebreaker
            return {
                "winner": winners[0],
                "votes": proposal_votes,
                "abstentions": abstentions,
                "tie": True,
                "tie_resolution": "first_proposal"
            }
        
        return {
            "winner": winners[0],
            "votes": proposal_votes,
            "abstentions": abstentions
        }
    
    def _count_weighted_votes(self, votes: Dict[str, str], proposals: Dict[str, str]) -> Dict[str, Any]:
        """Count votes with agent expertise weighting."""
        # Use proposal names as keys to avoid unhashable dict issues
        weighted_scores = {name: 0.0 for name in proposals.keys()}
        
        for agent in self.agents:
            if agent.name in votes:
                # Get expertise level (default to 0.5 if not set)
                expertise = getattr(agent, 'expertise_level', 0.5)
                voted_content = votes[agent.name]
                
                # Find which proposal was voted for
                for prop_name, prop_content in proposals.items():
                    if str(prop_content) == str(voted_content):
                        weighted_scores[prop_name] += expertise
                        break
        
        # Find winner by name, then get the actual proposal content
        winner_name = max(weighted_scores.items(), key=lambda x: x[1])[0]
        winner = proposals[winner_name]
        
        return {
            "winner": winner,
            "weighted_scores": weighted_scores
        }
    
    def _extract_selection(self, response: str, proposals: Dict[str, str]) -> str:
        """Extract selected proposal from moderator response."""
        # Look for proposal mentions in response
        for name, proposal in proposals.items():
            # Check name match
            if name in response:
                return proposal
            # Check proposal content match (handle short proposals)
            if len(proposal) > 50:
                if proposal[:50] in response:
                    return proposal
            else:
                if proposal in response:
                    return proposal
        
        # Default to first proposal if unclear
        return list(proposals.values())[0]
    
    async def _check_consensus(self, proposals: List[str]) -> bool:
        """Check if all agents proposed the same solution."""
        # Simple check: all proposals are very similar
        # Handle proposals that might be shorter than 100 chars
        normalized_proposals = set()
        for prop in proposals:
            if len(prop) > 100:
                normalized_proposals.add(prop[:100])
            else:
                normalized_proposals.add(prop)
        
        if len(normalized_proposals) == 1:
            return True
        return False
    
    def _get_latest_proposals(self, all_proposals: Dict[str, str]) -> Dict[str, str]:
        """Get the most recent proposal from each agent."""
        latest = {}
        for agent in self.agents:
            # Find the highest round number for this agent
            agent_proposals = [(k, v) for k, v in all_proposals.items() if k.startswith(agent.name)]
            if agent_proposals:
                # Sort by key to get the latest
                latest[agent.name] = sorted(agent_proposals, key=lambda x: x[0])[-1][1]
        return latest
    
    async def execute(self, task: str, context: Context) -> Dict[str, Any]:
        """Execute the debate process."""
        proposals = {}
        all_proposals = []  # Track all unique proposals
        
        # Initial proposals
        proposal_tasks = []
        for agent in self.agents:
            prompt = f"{task}\n\n{context.to_prompt_context()}"
            proposal_tasks.append(self._get_proposal(agent, prompt))
        
        initial_proposals = await asyncio.gather(*proposal_tasks)
        for agent, proposal in zip(self.agents, initial_proposals):
            proposals[agent.name] = proposal
            all_proposals.append(proposal)
        
        # Debate rounds
        rounds_to_consensus = 1
        consensus_reached = False
        
        for round_num in range(self.rounds):
            debate_context = self._create_debate_prompt(proposals, round_num)
            
            debate_tasks = []
            for agent in self.agents:
                prompt = f"{debate_context}\n\nProvide your updated proposal or critique others."
                debate_tasks.append(self._get_proposal(agent, prompt))
            
            round_responses = await asyncio.gather(*debate_tasks)
            for agent, response in zip(self.agents, round_responses):
                proposals[f"{agent.name}_round_{round_num}"] = response
                all_proposals.append(response)
            
            rounds_to_consensus += 1
            
            # Check for consensus if using consensus strategy
            if self.voting_strategy == "consensus":
                if await self._check_consensus(round_responses):
                    consensus_reached = True
                    break
        
        # Vote or select winner
        winner_data = await self._select_winner(proposals, all_proposals, task, context)
        
        result = {
            "winner": winner_data["winner"],
            "proposals": proposals,
            "strategy": self.voting_strategy
        }
        
        # Add strategy-specific data
        if "votes" in winner_data:
            result["votes"] = winner_data["votes"]
        if "abstentions" in winner_data:
            result["abstentions"] = winner_data["abstentions"]
            result["total_votes"] = sum(winner_data["votes"].values())
        if "tie" in winner_data:
            result["tie"] = winner_data["tie"]
            result["tie_resolution"] = winner_data.get("tie_resolution", "first_proposal")
        if "weighted_scores" in winner_data:
            result["weighted_scores"] = winner_data["weighted_scores"]
        if "selected_by" in winner_data:
            result["selected_by"] = winner_data["selected_by"]
        if self.voting_strategy == "consensus":
            result["consensus_reached"] = consensus_reached
            result["rounds_to_consensus"] = rounds_to_consensus
        
        return result
    
    async def _get_proposal(self, agent: AgentWrapper, prompt: str) -> str:
        """Get a proposal from an agent."""
        result = await agent.work_on(prompt)
        # Ensure we return a string, not a dict
        if isinstance(result, dict):
            # If it's a dict, try to extract a message or convert to string
            if 'message' in result:
                return str(result['message'])
            elif 'content' in result:
                return str(result['content'])
            else:
                return str(result)
        return str(result)
    
    def _create_debate_prompt(self, proposals: Dict[str, str], round_num: int) -> str:
        """Create a prompt summarizing the debate so far."""
        prompt = f"Debate Round {round_num + 1}\n\nCurrent Proposals:\n"
        for name, proposal in proposals.items():
            if not name.endswith(f"_round_{round_num}"):  # Skip future rounds
                # Handle proposals that might be shorter than 500 chars
                if len(proposal) > 500:
                    prompt += f"\n{name}:\n{proposal[:500]}...\n"
                else:
                    prompt += f"\n{name}:\n{proposal}\n"
        return prompt
    
    async def _select_winner(self, proposals: Dict[str, str], all_proposals: List[str], task: str, context: Context) -> Dict[str, Any]:
        """Select the winning proposal based on voting strategy."""
        # Get original proposals only (not debate rounds)
        original_proposals = {k: v for k, v in proposals.items() if "_round_" not in k}
        
        if self.voting_strategy == "moderator" and self.moderator:
            prompt = f"Select the best proposal for: {task}\n\nProposals:\n"
            for name, proposal in original_proposals.items():
                # Handle proposals that might be shorter than 300 chars
                if len(proposal) > 300:
                    prompt += f"\n{name}: {proposal[:300]}...\n"
                else:
                    prompt += f"\n{name}: {proposal}\n"
            response = await self.moderator.work_on(prompt)
            
            # Extract selected proposal from moderator response
            winner = self._extract_selection(response, original_proposals)
            return {"winner": winner, "selected_by": "moderator"}
        
        elif self.voting_strategy in ["majority", "weighted", "consensus"]:
            # Get votes from all agents
            votes, abstentions = await self._collect_votes(original_proposals)
            
            if self.voting_strategy == "majority":
                return self._count_majority_votes(votes, original_proposals, abstentions)
            
            elif self.voting_strategy == "weighted":
                return self._count_weighted_votes(votes, original_proposals)
            
            elif self.voting_strategy == "consensus":
                # For consensus, use the most recent proposals
                latest_proposals = self._get_latest_proposals(proposals)
                if len(set(latest_proposals.values())) == 1:
                    return {"winner": list(latest_proposals.values())[0]}
                else:
                    # Fall back to majority if no consensus
                    return self._count_majority_votes(votes, original_proposals, abstentions)
        
        # Default: return first proposal
        return {"winner": list(original_proposals.values())[0]}


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
        
        # Create agent clones
        agents = self._create_agent_clones(num_agents)
        
        # Split the work, using context if available
        if hasattr(self, '_split_task_with_context'):
            subtasks = self._split_task_with_context(task, num_agents, context)
        else:
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
        """Determine how many agents to create based on task complexity."""
        if self.split_strategy == "fixed":
            return self.min_agents
        
        if self.split_strategy == "auto":
            # Calculate complexity based on various factors
            word_count = len(task.split())
            line_count = len(task.strip().split('\n'))
            sentence_count = len(re.split(r'[.!?]+', task))
            
            # Check for numbered lists or bullet points
            has_list = bool(re.search(r'^\s*[\d\-\*]', task, re.MULTILINE))
            
            # Base calculation on word count
            if word_count < 50:
                base_agents = self.min_agents
            elif word_count < 150:
                base_agents = min(3, self.max_agents)
            elif word_count < 300:
                base_agents = min(5, self.max_agents)
            else:
                base_agents = self.max_agents
            
            # Adjust based on structure
            if has_list and line_count > 1:
                # If we have a list, try to match agent count to items
                base_agents = min(max(line_count, self.min_agents), self.max_agents)
            
            return base_agents
        
        # Default: use minimum
        return self.min_agents
    
    def _split_task(self, task: str, num_agents: int) -> List[str]:
        """Intelligently split task into subtasks for each agent."""
        task = task.strip()
        
        # Try different splitting strategies in order
        
        # 1. Split numbered or bulleted lists
        list_items = re.findall(r'^\s*[\d\-\*\.]+\s*(.+)$', task, re.MULTILINE)
        if len(list_items) >= num_agents:
            return self._distribute_items(list_items, num_agents)
        
        # 2. Split by sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', task) if s.strip()]
        if len(sentences) >= num_agents:
            return self._distribute_items(sentences, num_agents)
        
        # 3. Split by conjunctions and commas (for compound tasks)
        if ', and ' in task or ' and ' in task:
            parts = re.split(r',\s*and\s*|\s+and\s+|,\s*', task)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) >= num_agents:
                return self._distribute_items(parts, num_agents)
        
        # 4. Look for component mentions (frontend, backend, etc.)
        components = self._extract_components(task)
        if len(components) >= num_agents:
            subtasks = []
            for i, comp in enumerate(components[:num_agents]):
                subtasks.append(f"Focus on {comp}: {task}")
            return subtasks
        
        # 5. Look for file/directory patterns
        paths = re.findall(r'\b\w+/\w*\b', task)
        if len(paths) >= num_agents:
            subtasks = []
            for i, path in enumerate(paths[:num_agents]):
                subtasks.append(f"Handle {path}: {task}")
            return subtasks
        
        # Fallback: assign the same task with different agent numbers
        if num_agents == 1:
            return [task]
        else:
            return [f"Agent {i+1} of {num_agents}: {task}" for i in range(num_agents)]
    
    def _distribute_items(self, items: List[str], num_agents: int) -> List[str]:
        """Distribute items among agents as evenly as possible."""
        subtasks = [[] for _ in range(num_agents)]
        
        # Distribute items round-robin style
        for i, item in enumerate(items):
            subtasks[i % num_agents].append(item)
        
        # Convert to string subtasks
        result = []
        for i, agent_items in enumerate(subtasks):
            if agent_items:
                if len(agent_items) == 1:
                    result.append(agent_items[0])
                else:
                    result.append(" ".join([f"{j+1}. {item}" for j, item in enumerate(agent_items)]))
            else:
                result.append(f"Agent {i+1}: Assist with overall task")
        
        return result
    
    def _extract_components(self, task: str) -> List[str]:
        """Extract component names from task description."""
        components = []
        
        # Common software components
        component_keywords = [
            'frontend', 'backend', 'database', 'api', 'ui', 'server',
            'client', 'mobile', 'web', 'desktop', 'service', 'infrastructure'
        ]
        
        task_lower = task.lower()
        for keyword in component_keywords:
            if keyword in task_lower:
                components.append(keyword)
        
        return components
    
    def _split_task_with_context(self, task: str, num_agents: int, context: Context) -> List[str]:
        """Split task using context information for better distribution."""
        # Check if context has project structure
        project_structure = context.get('project_structure', {})
        
        if project_structure and len(project_structure) >= num_agents:
            # Create subtasks based on project components
            subtasks = []
            components = list(project_structure.keys())[:num_agents]
            
            for component in components:
                tech_stack = project_structure[component]
                if isinstance(tech_stack, list):
                    tech_str = " and ".join(tech_stack)
                    subtasks.append(f"Handle {component} ({tech_str}): {task}")
                else:
                    subtasks.append(f"Handle {component}: {task}")
            
            return subtasks
        
        # Fall back to regular splitting
        return self._split_task(task, num_agents)
    
    def _create_agent_clones(self, num_agents: int) -> List[AgentWrapper]:
        """Create cloned agent wrappers."""
        agents = []
        for i in range(num_agents):
            # In real implementation, properly clone the agent
            wrapper = AgentWrapper(
                agent=self.agent_template,
                name=f"split_agent_{i}"
            )
            agents.append(wrapper)
        return agents