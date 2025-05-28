"""Components for debate step functionality using composition."""

import asyncio
import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from konseho.protocols import IAgent


@dataclass
class ProposalFormat:
    """Configuration for proposal formatting."""

    max_length: int = 500
    include_reasoning: bool = True
    structured_format: bool = False


@dataclass
class StandardFormat(ProposalFormat):
    """Standard proposal format."""

    pass


class ProposalCollector:
    """Collects proposals from agents in a standardized way."""

    def __init__(self, format_config: ProposalFormat | None = None):
        """Initialize proposal collector.

        Args:
            format_config: Configuration for proposal formatting
        """
        self.format_config = format_config or StandardFormat()

    async def collect(
        self,
        agents: list[IAgent],
        task: str,
        moderator: IAgent | None = None,
    ) -> dict[str, str]:
        """Collect proposals from all agents.

        Args:
            agents: List of agents to collect proposals from
            task: The task to propose solutions for
            moderator: Optional moderator to provide guidance

        Returns:
            Dictionary mapping agent names to their proposals
        """
        # Build prompt with current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = f"Current date and time: {current_time}\n\nTask: {task}"

        if moderator:
            # Get moderator guidance first
            guidance_prompt = (
                f"{prompt}\n\nProvide guidance for agents working on this task."
            )
            guidance = await moderator.work_on(guidance_prompt)
            prompt = f"{prompt}\n\nModerator guidance: {guidance}"

        # Collect proposals in parallel
        proposal_tasks = []
        for agent in agents:
            agent_prompt = self._format_proposal_prompt(prompt, agent)
            proposal_tasks.append(self._get_proposal(agent, agent_prompt))

        proposals = await asyncio.gather(*proposal_tasks)

        # Return as dictionary
        return {
            agent.name: proposal
            for agent, proposal in zip(agents, proposals, strict=True)
        }

    def _format_proposal_prompt(self, base_prompt: str, agent: IAgent) -> str:
        """Format the proposal prompt for an agent.

        Args:
            base_prompt: Base prompt with task
            agent: The agent to format for

        Returns:
            Formatted prompt
        """
        prompt_parts = [base_prompt]

        if self.format_config.structured_format:
            prompt_parts.append(
                "\nProvide your proposal in the following format:\n"
                "Solution: [Your solution]\n"
                "Reasoning: [Why this solution works]\n"
                "Challenges: [Potential challenges]"
            )
        else:
            prompt_parts.append("\nProvide your proposal for solving this task.")

        if self.format_config.include_reasoning:
            prompt_parts.append("Include your reasoning.")

        return "\n".join(prompt_parts)

    async def _get_proposal(self, agent: IAgent, prompt: str) -> str:
        """Get a proposal from an agent.

        Args:
            agent: The agent to get proposal from
            prompt: The prompt to send

        Returns:
            The agent's proposal as a string
        """
        result = await agent.work_on(prompt)

        # Ensure we return a string
        if isinstance(result, dict):
            if "message" in result:
                return str(result["message"])
            elif "content" in result:
                return str(result["content"])
            else:
                return str(result)

        return str(result)


class VotingStrategy(ABC):
    """Abstract base for voting strategies."""

    @abstractmethod
    async def select_winner(
        self,
        agents: list[IAgent],
        proposals: dict[str, str],
    ) -> tuple[str, dict[str, Any]]:
        """Select a winning proposal.

        Args:
            agents: List of voting agents
            proposals: Dictionary of proposals to vote on

        Returns:
            Tuple of (winning proposal, voting metadata)
        """
        pass


class MajorityVoting(VotingStrategy):
    """Simple majority voting strategy."""

    def __init__(self, allow_self_voting: bool = True):
        """Initialize majority voting.

        Args:
            allow_self_voting: Whether agents can vote for their own proposals
        """
        self.allow_self_voting = allow_self_voting

    async def select_winner(
        self,
        agents: list[IAgent],
        proposals: dict[str, str],
    ) -> tuple[str, dict[str, Any]]:
        """Select winner by majority vote.

        Args:
            agents: List of voting agents
            proposals: Dictionary of proposals to vote on

        Returns:
            Tuple of (winning proposal, voting metadata)
        """
        votes, abstentions = await self._collect_votes(agents, proposals)
        result = self._count_votes(votes, proposals, abstentions)
        return result["winner"], result

    async def _collect_votes(
        self,
        agents: list[IAgent],
        proposals: dict[str, str],
    ) -> tuple[dict[str, str], int]:
        """Collect votes from all agents."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build voting prompt
        voting_prompt = (
            f"Current date and time: {current_time}\n\n"
            f"Vote for the best proposal. Reply with 'I vote for: [agent name]' "
            f"or 'I abstain from voting'\n\n"
        )

        for name, proposal in proposals.items():
            if len(proposal) > 200:
                voting_prompt += f"{name}: {proposal[:200]}...\n\n"
            else:
                voting_prompt += f"{name}: {proposal}\n\n"

        # Collect votes in parallel
        vote_tasks = []
        for agent in agents:
            vote_tasks.append(agent.work_on(voting_prompt))

        vote_responses = await asyncio.gather(*vote_tasks)

        # Extract votes
        votes = {}
        abstentions = 0

        for agent, response in zip(agents, vote_responses, strict=True):
            # Skip self-voting if not allowed
            if not self.allow_self_voting and agent.name in proposals:
                # Check if agent voted for themselves
                vote = self._extract_vote(response, proposals)
                if vote == proposals[agent.name]:
                    abstentions += 1
                    continue

            vote = self._extract_vote(response, proposals)
            if vote == "ABSTAIN":
                abstentions += 1
            elif vote:
                votes[agent.name] = vote

        return votes, abstentions

    def _extract_vote(self, response: str, proposals: dict[str, str]) -> str | None:
        """Extract vote from agent response."""
        if not isinstance(response, str):
            response = str(response)

        # Check for abstention
        if "abstain" in response.lower():
            return "ABSTAIN"

        # Look for "I vote for: X" pattern
        vote_match = re.search(r"I vote for:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
        if vote_match:
            voted_text = vote_match.group(1).strip()
            # Match to proposal by agent name
            for name in proposals:
                if name.lower() in voted_text.lower():
                    return proposals[name]

        return None

    def _count_votes(
        self,
        votes: dict[str, str],
        proposals: dict[str, str],
        abstentions: int,
    ) -> dict[str, Any]:
        """Count votes and determine winner."""
        vote_counts = Counter(votes.values())

        # Initialize vote tracking by agent name
        proposal_votes = dict.fromkeys(proposals.keys(), 0)

        # Count votes
        for _voter, voted_content in votes.items():
            for prop_name, prop_content in proposals.items():
                if str(prop_content) == str(voted_content):
                    proposal_votes[prop_name] += 1
                    break

        if not vote_counts:
            # No valid votes, return first proposal
            return {
                "winner": list(proposals.values())[0],
                "votes": proposal_votes,
                "abstentions": abstentions,
                "total_votes": 0,
            }

        # Get winner(s)
        max_votes = max(vote_counts.values())
        winners = [prop for prop, count in vote_counts.items() if count == max_votes]

        metadata = {
            "votes": proposal_votes,
            "abstentions": abstentions,
            "total_votes": sum(proposal_votes.values()),
        }

        if len(winners) > 1:
            # Tie - use first proposal
            metadata["tie"] = True
            metadata["tie_resolution"] = "first_proposal"
            metadata["winner"] = winners[0]
        else:
            metadata["winner"] = winners[0]

        return metadata


class WeightedVoting(VotingStrategy):
    """Voting strategy with agent expertise weighting."""

    def __init__(self, weights: dict[str, float] | None = None):
        """Initialize weighted voting.

        Args:
            weights: Optional dictionary of agent name to weight mappings
        """
        self.weights = weights or {}

    async def select_winner(
        self,
        agents: list[IAgent],
        proposals: dict[str, str],
    ) -> tuple[str, dict[str, Any]]:
        """Select winner by weighted vote.

        Args:
            agents: List of voting agents
            proposals: Dictionary of proposals to vote on

        Returns:
            Tuple of (winning proposal, voting metadata)
        """
        # Collect votes (reuse majority voting logic)
        majority_voter = MajorityVoting()
        votes, abstentions = await majority_voter._collect_votes(agents, proposals)

        # Count with weights
        weighted_scores = dict.fromkeys(proposals.keys(), 0.0)

        for agent in agents:
            if agent.name in votes:
                # Get weight for this agent
                weight = self.weights.get(agent.name, 1.0)
                voted_content = votes[agent.name]

                # Find which proposal was voted for
                for prop_name, prop_content in proposals.items():
                    if str(prop_content) == str(voted_content):
                        weighted_scores[prop_name] += weight
                        break

        # Find winner
        winner_name = max(weighted_scores.items(), key=lambda x: x[1])[0]
        winner = proposals[winner_name]

        return winner, {
            "winner": winner,
            "weighted_scores": weighted_scores,
            "abstentions": abstentions,
        }


class VotingSystem:
    """Manages the voting process with different strategies."""

    def __init__(self, strategy: VotingStrategy | None = None):
        """Initialize voting system.

        Args:
            strategy: The voting strategy to use
        """
        self.strategy = strategy or MajorityVoting()
        self.last_vote_details: dict[str, Any] = {}

    async def select_winner(
        self,
        agents: list[IAgent],
        proposals: dict[str, str],
    ) -> str:
        """Select the winning proposal.

        Args:
            agents: List of voting agents
            proposals: Dictionary of proposals to vote on

        Returns:
            The winning proposal
        """
        winner, details = await self.strategy.select_winner(agents, proposals)
        self.last_vote_details = details
        return winner

