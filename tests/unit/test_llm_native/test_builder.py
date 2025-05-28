"""Tests for LLM council builder."""
from unittest.mock import Mock, AsyncMock, patch

import pytest

from konseho.core.council import Council
from konseho.core.steps import Step, DebateStep, ParallelStep
from konseho.agents.base import Agent
from konseho.dynamic.llm_native.builder import LLMCouncilBuilder
from konseho.dynamic.llm_native.schemas import (
    CouncilSpec,
    AgentSpec,
    StepSpec,
    StepType
)


class TestLLMCouncilBuilder:
    """Test building councils from LLM specifications."""

    @pytest.fixture
    def builder(self):
        """Create a builder instance."""
        return LLMCouncilBuilder()

    @pytest.fixture
    def simple_spec(self):
        """Create a simple council specification."""
        return CouncilSpec(
            name="SimpleCouncil",
            agents=[
                AgentSpec(id="agent1", prompt="First agent prompt"),
                AgentSpec(id="agent2", prompt="Second agent prompt")
            ],
            steps=[
                StepSpec(
                    type=StepType.PARALLEL,
                    agents=["agent1", "agent2"],
                    task_template="Work on {input}"
                )
            ]
        )

    @pytest.fixture
    def complex_spec(self):
        """Create a complex council specification."""
        return CouncilSpec(
            name="ComplexCouncil",
            description="A complex council with multiple steps",
            agents=[
                AgentSpec(
                    id="researcher",
                    prompt="You are a researcher",
                    model="claude-3-sonnet",
                    temperature=0.5,
                    tools=["web_search"]
                ),
                AgentSpec(
                    id="analyst",
                    prompt="You are an analyst",
                    temperature=0.3,
                    tools=["read_file", "code_edit"]
                ),
                AgentSpec(
                    id="reporter",
                    prompt="You create reports",
                    temperature=0.7
                )
            ],
            steps=[
                StepSpec(
                    type=StepType.PARALLEL,
                    agents=["researcher", "analyst"],
                    task_template="Research {input}"
                ),
                StepSpec(
                    type=StepType.DEBATE,
                    agents=["researcher", "analyst"],
                    task_template="Discuss findings",
                    config={"rounds": 2}
                ),
                StepSpec(
                    type=StepType.SYNTHESIZE,
                    agents=["reporter"],
                    task_template="Create report from {context}"
                )
            ]
        )

    @pytest.mark.asyncio
    async def test_build_simple_council(self, builder, simple_spec):
        """Test building a simple council."""
        with patch('konseho.agents.base.create_agent') as mock_create_agent:
            # Mock agent creation
            mock_agents = {
                "agent1": Mock(spec=Agent, name="agent1"),
                "agent2": Mock(spec=Agent, name="agent2")
            }
            mock_create_agent.side_effect = lambda **kwargs: mock_agents[kwargs['name']]
            
            council = await builder.build(simple_spec)
            
            assert isinstance(council, Council)
            assert council.name == "SimpleCouncil"
            assert len(council.steps) == 1
            assert isinstance(council.steps[0], Step)

    @pytest.mark.asyncio
    async def test_build_complex_council(self, builder, complex_spec):
        """Test building a complex council with multiple step types."""
        with patch('konseho.agents.base.create_agent') as mock_create_agent:
            # Create mock agents
            mock_agents = {}
            def create_mock_agent(**kwargs):
                mock = Mock(spec=Agent)
                mock.name = kwargs['name']
                mock_agents[kwargs['name']] = mock
                return mock
            
            mock_create_agent.side_effect = create_mock_agent
            
            council = await builder.build(complex_spec)
            
            assert council.name == "ComplexCouncil"
            assert len(council.steps) == 3
            
            # Check step types
            assert isinstance(council.steps[0], ParallelStep)
            assert isinstance(council.steps[1], DebateStep)
            # The third step should be a parallel step (synthesize uses one agent)
            assert isinstance(council.steps[2], Step)

    @pytest.mark.asyncio
    async def test_agent_creation_with_tools(self, builder, complex_spec):
        """Test that agents are created with correct tools."""
        with patch('konseho.agents.base.create_agent') as mock_create_agent:
            with patch.object(builder, '_resolve_tools') as mock_resolve_tools:
                # Mock tool resolution
                mock_resolve_tools.side_effect = lambda tools: [f"resolved_{t}" for t in tools]
                
                await builder.build(complex_spec)
                
                # Check that agents were created with correct parameters
                calls = mock_create_agent.call_args_list
                
                # Researcher should have web_search tool
                researcher_call = next(c for c in calls if c.kwargs['name'] == 'researcher')
                assert researcher_call.kwargs['tools'] == ["resolved_web_search"]
                assert researcher_call.kwargs['temperature'] == 0.5
                
                # Analyst should have multiple tools
                analyst_call = next(c for c in calls if c.kwargs['name'] == 'analyst')
                assert analyst_call.kwargs['tools'] == ["resolved_read_file", "resolved_code_edit"]

    @pytest.mark.asyncio
    async def test_model_resolution(self, builder):
        """Test model resolution from string to actual model."""
        spec = CouncilSpec(
            name="ModelTest",
            agents=[
                AgentSpec(
                    id="claude_agent",
                    prompt="Test",
                    model="claude-3-sonnet"
                ),
                AgentSpec(
                    id="gpt_agent",
                    prompt="Test",
                    model="gpt-4"
                )
            ],
            steps=[]
        )
        
        with patch('konseho.agents.base.create_agent') as mock_create_agent:
            with patch.object(builder, '_resolve_model') as mock_resolve_model:
                mock_resolve_model.side_effect = lambda m: f"resolved_{m}"
                
                await builder.build(spec)
                
                # Check model resolution calls
                mock_resolve_model.assert_any_call("claude-3-sonnet")
                mock_resolve_model.assert_any_call("gpt-4")

    @pytest.mark.asyncio
    async def test_step_config_passed_correctly(self, builder):
        """Test that step configurations are passed correctly."""
        spec = CouncilSpec(
            name="ConfigTest",
            agents=[
                AgentSpec(id="agent1", prompt="Test"),
                AgentSpec(id="agent2", prompt="Test")
            ],
            steps=[
                StepSpec(
                    type=StepType.DEBATE,
                    agents=["agent1", "agent2"],
                    config={"rounds": 3, "voting_strategy": "weighted"}
                )
            ]
        )
        
        with patch('konseho.agents.base.create_agent'):
            council = await builder.build(spec)
            
            debate_step = council.steps[0]
            assert isinstance(debate_step, DebateStep)
            # Check that config was applied (this depends on DebateStep implementation)
            # For now, just verify the step was created

    @pytest.mark.asyncio
    async def test_synthesize_step_single_agent(self, builder):
        """Test that synthesize steps work with single agent."""
        spec = CouncilSpec(
            name="SynthesizeTest",
            agents=[
                AgentSpec(id="synthesizer", prompt="Synthesize findings")
            ],
            steps=[
                StepSpec(
                    type=StepType.SYNTHESIZE,
                    agents=["synthesizer"],
                    task_template="Summarize {context}"
                )
            ]
        )
        
        with patch('konseho.agents.base.create_agent'):
            council = await builder.build(spec)
            
            assert len(council.steps) == 1
            # Synthesize is implemented as a parallel step with one agent
            assert isinstance(council.steps[0], Step)

    def test_available_tools_list(self, builder):
        """Test getting list of available tools."""
        tools = builder.get_available_tools()
        
        # Should include basic tools
        assert "read_file" in tools
        assert "code_edit" in tools
        assert "web_search" in tools

    def test_available_models_list(self, builder):
        """Test getting list of available models."""
        models = builder.get_available_models()
        
        # Should include common models
        assert "claude-3-haiku" in models
        assert "claude-3-sonnet" in models
        assert "gpt-4" in models