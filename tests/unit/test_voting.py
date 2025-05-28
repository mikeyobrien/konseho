"""Unit tests for voting mechanisms in DebateStep."""

from unittest.mock import AsyncMock, patch

import pytest

from konseho.agents.base import AgentWrapper
from konseho.core.context import Context
from konseho.core.steps import DebateStep
from tests.fixtures import MockStrandsAgent


class TestDebateVoting:
    """Tests for debate voting mechanisms."""

    @pytest.mark.asyncio
    async def test_majority_voting(self):
        """Test majority voting selects the most voted proposal."""
        # Create agents that will vote
        agent1 = AgentWrapper(MockStrandsAgent("agent1", "Proposal A"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2", "Proposal B"))
        agent3 = AgentWrapper(MockStrandsAgent("agent3", "Proposal C"))

        # Mock voting responses
        # Agent1 votes for Proposal A
        # Agent2 votes for Proposal A
        # Agent3 votes for Proposal B
        with (
            patch.object(agent1, "work_on", new_callable=AsyncMock) as mock1,
            patch.object(agent2, "work_on", new_callable=AsyncMock) as mock2,
            patch.object(agent3, "work_on", new_callable=AsyncMock) as mock3,
        ):

            mock1.side_effect = ["Proposal A", "I vote for: Proposal A"]
            mock2.side_effect = ["Proposal B", "I vote for: Proposal A"]
            mock3.side_effect = ["Proposal C", "I vote for: Proposal B"]

            debate = DebateStep(
                agents=[agent1, agent2, agent3],
                rounds=0,  # No debate rounds, just vote
                voting_strategy="majority",
            )

            result = await debate.execute("Test task", Context())

            assert result["winner"] == "Proposal A"
            assert result["votes"]["Proposal A"] == 2
            assert result["votes"]["Proposal B"] == 1
            assert result["votes"]["Proposal C"] == 0

    @pytest.mark.asyncio
    async def test_consensus_voting(self):
        """Test consensus voting requires all agents to agree."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2"))

        with (
            patch.object(agent1, "work_on", new_callable=AsyncMock) as mock1,
            patch.object(agent2, "work_on", new_callable=AsyncMock) as mock2,
        ):

            # First round: different proposals
            mock1.side_effect = [
                "Proposal A",
                "I vote for: Proposal A",
                "Revised Proposal A",
                "I vote for: Revised Proposal A",
            ]
            mock2.side_effect = [
                "Proposal B",
                "I vote for: Proposal B",
                "Revised Proposal A",
                "I vote for: Revised Proposal A",
            ]

            debate = DebateStep(
                agents=[agent1, agent2], rounds=1, voting_strategy="consensus"
            )

            result = await debate.execute("Test task", Context())

            # Should reach consensus on Revised Proposal A
            assert result["winner"] == "Revised Proposal A"
            assert result["consensus_reached"] == True
            assert result["rounds_to_consensus"] == 2

    @pytest.mark.asyncio
    async def test_moderator_voting(self):
        """Test moderator selects the winning proposal."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1", "Proposal A"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2", "Proposal B"))
        moderator = AgentWrapper(MockStrandsAgent("moderator"))

        with patch.object(moderator, "work_on", new_callable=AsyncMock) as mock_mod:
            mock_mod.return_value = "I select Proposal B as the best solution."

            debate = DebateStep(
                agents=[agent1, agent2],
                moderator=moderator,
                rounds=0,
                voting_strategy="moderator",
            )

            result = await debate.execute("Test task", Context())

            assert result["winner"] == "Proposal B"
            assert result["selected_by"] == "moderator"

    @pytest.mark.asyncio
    async def test_weighted_voting(self):
        """Test weighted voting based on agent expertise."""
        # Create agents with different expertise levels
        expert = AgentWrapper(MockStrandsAgent("expert"), expertise_level=0.9)
        intermediate = AgentWrapper(
            MockStrandsAgent("intermediate"), expertise_level=0.5
        )
        novice = AgentWrapper(MockStrandsAgent("novice"), expertise_level=0.2)

        with (
            patch.object(expert, "work_on", new_callable=AsyncMock) as mock1,
            patch.object(intermediate, "work_on", new_callable=AsyncMock) as mock2,
            patch.object(novice, "work_on", new_callable=AsyncMock) as mock3,
        ):

            mock1.side_effect = ["Proposal A", "I vote for: Proposal A"]
            mock2.side_effect = ["Proposal B", "I vote for: Proposal B"]
            mock3.side_effect = ["Proposal C", "I vote for: Proposal B"]

            debate = DebateStep(
                agents=[expert, intermediate, novice],
                rounds=0,
                voting_strategy="weighted",
            )

            result = await debate.execute("Test task", Context())

            # Expert vote (0.9) for A > Combined votes (0.7) for B
            assert result["winner"] == "Proposal A"
            assert result["weighted_scores"]["Proposal A"] == 0.9
            assert result["weighted_scores"]["Proposal B"] == 0.7

    @pytest.mark.asyncio
    async def test_voting_tie_resolution(self):
        """Test how ties are resolved in voting."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2"))

        with (
            patch.object(agent1, "work_on", new_callable=AsyncMock) as mock1,
            patch.object(agent2, "work_on", new_callable=AsyncMock) as mock2,
        ):

            mock1.side_effect = ["Proposal A", "I vote for: Proposal A"]
            mock2.side_effect = ["Proposal B", "I vote for: Proposal B"]

            debate = DebateStep(
                agents=[agent1, agent2], rounds=0, voting_strategy="majority"
            )

            result = await debate.execute("Test task", Context())

            # Should have a tie-breaker mechanism
            assert result["tie"] == True
            assert result["tie_resolution"] in ["random", "moderator", "first_proposal"]
            assert result["winner"] in ["Proposal A", "Proposal B"]

    @pytest.mark.asyncio
    async def test_voting_with_abstentions(self):
        """Test voting when some agents abstain."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2"))
        agent3 = AgentWrapper(MockStrandsAgent("agent3"))

        with (
            patch.object(agent1, "work_on", new_callable=AsyncMock) as mock1,
            patch.object(agent2, "work_on", new_callable=AsyncMock) as mock2,
            patch.object(agent3, "work_on", new_callable=AsyncMock) as mock3,
        ):

            mock1.side_effect = ["Proposal A", "I vote for: Proposal A"]
            mock2.side_effect = ["Proposal B", "I abstain from voting"]
            mock3.side_effect = ["Proposal C", "I vote for: Proposal A"]

            debate = DebateStep(
                agents=[agent1, agent2, agent3], rounds=0, voting_strategy="majority"
            )

            result = await debate.execute("Test task", Context())

            assert result["winner"] == "Proposal A"
            assert result["votes"]["Proposal A"] == 2
            assert result["abstentions"] == 1
            assert result["total_votes"] == 2
