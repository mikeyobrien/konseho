"""Tests for LLM-native council schemas."""
import pytest
from pydantic import ValidationError

from konseho.dynamic.llm_native.schemas import (
    AgentSpec,
    StepSpec,
    CouncilSpec,
    StepType,
    ModelChoice
)


class TestAgentSpec:
    """Test agent specification schema."""

    def test_minimal_agent_spec(self):
        """Test creating agent with minimal required fields."""
        agent = AgentSpec(
            id="reviewer",
            prompt="You review code for quality issues."
        )
        assert agent.id == "reviewer"
        assert agent.prompt == "You review code for quality issues."
        assert agent.model == "claude-3-haiku"  # default
        assert agent.temperature == 0.7  # default
        assert agent.tools == []  # default

    def test_full_agent_spec(self):
        """Test creating agent with all fields."""
        agent = AgentSpec(
            id="security_expert",
            prompt="You are a security expert focusing on vulnerabilities.",
            model="claude-3-sonnet",
            temperature=0.3,
            tools=["read_file", "search_code", "web_search"]
        )
        assert agent.id == "security_expert"
        assert agent.model == "claude-3-sonnet"
        assert agent.temperature == 0.3
        assert agent.tools == ["read_file", "search_code", "web_search"]

    def test_invalid_temperature(self):
        """Test temperature validation."""
        with pytest.raises(ValidationError) as exc:
            AgentSpec(
                id="test",
                prompt="test",
                temperature=1.5  # Must be between 0 and 1
            )
        assert "temperature" in str(exc.value)

    def test_invalid_model(self):
        """Test model validation."""
        with pytest.raises(ValidationError) as exc:
            AgentSpec(
                id="test",
                prompt="test",
                model="invalid-model"
            )
        assert "model" in str(exc.value)


class TestStepSpec:
    """Test step specification schema."""

    def test_minimal_step_spec(self):
        """Test creating step with minimal fields."""
        step = StepSpec(
            type=StepType.PARALLEL,
            agents=["reviewer", "analyzer"]
        )
        assert step.type == StepType.PARALLEL
        assert step.agents == ["reviewer", "analyzer"]
        assert step.task_template == "{input}"  # default
        assert step.config == {}  # default

    def test_debate_step_spec(self):
        """Test creating debate step with config."""
        step = StepSpec(
            type=StepType.DEBATE,
            agents=["expert1", "expert2"],
            task_template="Debate the best approach for {input}",
            config={"rounds": 3, "voting_strategy": "weighted"}
        )
        assert step.type == StepType.DEBATE
        assert step.config["rounds"] == 3
        assert step.config["voting_strategy"] == "weighted"

    def test_synthesize_step_spec(self):
        """Test synthesize step with single agent."""
        step = StepSpec(
            type=StepType.SYNTHESIZE,
            agents=["summarizer"],
            task_template="Create a summary based on {context}"
        )
        assert step.type == StepType.SYNTHESIZE
        assert len(step.agents) == 1

    def test_invalid_step_type(self):
        """Test step type validation."""
        with pytest.raises(ValidationError):
            StepSpec(
                type="invalid_type",
                agents=["test"]
            )


class TestCouncilSpec:
    """Test complete council specification."""

    def test_minimal_council_spec(self):
        """Test creating council with minimal configuration."""
        council = CouncilSpec(
            name="SimpleCouncil",
            agents=[
                AgentSpec(id="agent1", prompt="First agent"),
                AgentSpec(id="agent2", prompt="Second agent")
            ],
            steps=[
                StepSpec(type=StepType.PARALLEL, agents=["agent1", "agent2"])
            ]
        )
        assert council.name == "SimpleCouncil"
        assert len(council.agents) == 2
        assert len(council.steps) == 1

    def test_council_agent_reference_validation(self):
        """Test that steps can only reference defined agents."""
        with pytest.raises(ValidationError) as exc:
            CouncilSpec(
                name="InvalidCouncil",
                agents=[
                    AgentSpec(id="agent1", prompt="First agent")
                ],
                steps=[
                    StepSpec(type=StepType.PARALLEL, agents=["agent1", "undefined_agent"])
                ]
            )
        assert "undefined_agent" in str(exc.value)

    def test_complex_council_spec(self):
        """Test creating complex council with multiple steps."""
        council = CouncilSpec(
            name="SecurityReviewCouncil",
            description="Reviews code for security vulnerabilities",
            agents=[
                AgentSpec(
                    id="vuln_scanner",
                    prompt="Scan for security vulnerabilities",
                    model="claude-3-sonnet",
                    temperature=0.2,
                    tools=["read_file", "search_code"]
                ),
                AgentSpec(
                    id="architect",
                    prompt="Review architecture for security",
                    temperature=0.3
                ),
                AgentSpec(
                    id="reporter",
                    prompt="Create security reports",
                    temperature=0.5
                )
            ],
            steps=[
                StepSpec(
                    type=StepType.PARALLEL,
                    agents=["vuln_scanner", "architect"],
                    task_template="Analyze {input} for security issues"
                ),
                StepSpec(
                    type=StepType.DEBATE,
                    agents=["vuln_scanner", "architect"],
                    task_template="Discuss findings and prioritize",
                    config={"rounds": 2}
                ),
                StepSpec(
                    type=StepType.SYNTHESIZE,
                    agents=["reporter"],
                    task_template="Create report from {context}"
                )
            ]
        )
        assert council.name == "SecurityReviewCouncil"
        assert len(council.agents) == 3
        assert len(council.steps) == 3
        assert council.steps[1].config["rounds"] == 2

    def test_duplicate_agent_ids(self):
        """Test that agent IDs must be unique."""
        with pytest.raises(ValidationError) as exc:
            CouncilSpec(
                name="DuplicateCouncil",
                agents=[
                    AgentSpec(id="agent1", prompt="First"),
                    AgentSpec(id="agent1", prompt="Duplicate")
                ],
                steps=[]
            )
        assert "duplicate" in str(exc.value).lower()


class TestJSONExtraction:
    """Test JSON extraction utilities."""

    def test_extract_json_from_clean_response(self):
        """Test extracting JSON from clean response."""
        from konseho.dynamic.llm_native.schemas import extract_json_from_response
        
        response = '{"key": "value"}'
        result = extract_json_from_response(response)
        assert result == {"key": "value"}

    def test_extract_json_from_markdown(self):
        """Test extracting JSON from markdown code block."""
        from konseho.dynamic.llm_native.schemas import extract_json_from_response
        
        response = '''Here's the JSON:
```json
{"key": "value"}
```'''
        result = extract_json_from_response(response)
        assert result == {"key": "value"}

    def test_extract_json_with_explanation(self):
        """Test extracting JSON with surrounding text."""
        from konseho.dynamic.llm_native.schemas import extract_json_from_response
        
        response = '''I'll create a council for you.
        
        {"name": "TestCouncil", "agents": []}
        
        This council will help with testing.'''
        result = extract_json_from_response(response)
        assert result["name"] == "TestCouncil"

    def test_extract_json_failure(self):
        """Test handling invalid JSON."""
        from konseho.dynamic.llm_native.schemas import extract_json_from_response
        
        response = "This is not JSON at all"
        with pytest.raises(ValueError) as exc:
            extract_json_from_response(response)
        assert "No valid JSON found" in str(exc.value)