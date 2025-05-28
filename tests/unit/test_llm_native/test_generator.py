"""Tests for LLM council generator."""
import json
from unittest.mock import Mock, AsyncMock, patch

import pytest

from konseho.dynamic.llm_native.generator import (
    LLMCouncilGenerator,
    GENERATOR_PROMPT,
    EXAMPLE_COUNCILS
)
from konseho.dynamic.llm_native.schemas import CouncilSpec, StepType


class TestLLMCouncilGenerator:
    """Test LLM council generation."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model for testing."""
        model = Mock()
        model.work_on = AsyncMock()
        return model

    @pytest.fixture
    def generator(self, mock_model):
        """Create a generator with mock model."""
        return LLMCouncilGenerator(model=mock_model)

    @pytest.mark.asyncio
    async def test_simple_query_generation(self, generator, mock_model):
        """Test generating council for simple query."""
        # Mock response
        mock_response = {
            "name": "CodeReviewCouncil",
            "description": "Reviews code for quality",
            "agents": [
                {
                    "id": "reviewer",
                    "prompt": "You review code for bugs and issues",
                    "temperature": 0.3
                },
                {
                    "id": "architect",
                    "prompt": "You review code architecture",
                    "temperature": 0.4
                }
            ],
            "steps": [
                {
                    "type": "parallel",
                    "agents": ["reviewer", "architect"],
                    "task_template": "Review {input} for your area of expertise"
                },
                {
                    "type": "synthesize",
                    "agents": ["reviewer"],
                    "task_template": "Summarize all findings from {context}"
                }
            ]
        }
        mock_model.work_on.return_value = json.dumps(mock_response)

        # Generate council
        spec = await generator.generate_council_spec("Review this Python code for issues")
        
        # Verify
        assert isinstance(spec, CouncilSpec)
        assert spec.name == "CodeReviewCouncil"
        assert len(spec.agents) == 2
        assert len(spec.steps) == 2
        assert spec.steps[0].type == StepType.PARALLEL

    @pytest.mark.asyncio
    async def test_complex_query_generation(self, generator, mock_model):
        """Test generating council for complex query."""
        mock_response = {
            "name": "SecurityAuditCouncil",
            "description": "Comprehensive security audit",
            "agents": [
                {
                    "id": "vuln_scanner",
                    "prompt": "Scan for security vulnerabilities",
                    "model": "claude-3-sonnet",
                    "temperature": 0.2,
                    "tools": ["read_file", "search_code"]
                },
                {
                    "id": "crypto_analyst",
                    "prompt": "Analyze cryptographic implementations",
                    "temperature": 0.1,
                    "tools": ["read_file"]
                },
                {
                    "id": "reporter",
                    "prompt": "Create security reports",
                    "temperature": 0.5
                }
            ],
            "steps": [
                {
                    "type": "parallel",
                    "agents": ["vuln_scanner", "crypto_analyst"],
                    "task_template": "Analyze {input} for security issues"
                },
                {
                    "type": "debate",
                    "agents": ["vuln_scanner", "crypto_analyst"],
                    "task_template": "Discuss findings and prioritize",
                    "config": {"rounds": 2}
                },
                {
                    "type": "synthesize",
                    "agents": ["reporter"],
                    "task_template": "Create comprehensive report"
                }
            ]
        }
        mock_model.work_on.return_value = json.dumps(mock_response)

        spec = await generator.generate_council_spec(
            "Perform a comprehensive security audit of my authentication system"
        )
        
        assert spec.name == "SecurityAuditCouncil"
        assert len(spec.agents) == 3
        assert spec.agents[0].tools == ["read_file", "search_code"]
        assert spec.steps[1].type == StepType.DEBATE
        assert spec.steps[1].config["rounds"] == 2

    @pytest.mark.asyncio
    async def test_retry_on_invalid_json(self, generator, mock_model):
        """Test retry logic when model returns invalid JSON."""
        # First attempt: invalid JSON
        mock_model.work_on.side_effect = [
            "This is not valid JSON",
            json.dumps({
                "name": "SimpleCouncil",
                "agents": [{"id": "agent1", "prompt": "Test agent"}],
                "steps": [{"type": "parallel", "agents": ["agent1"]}]
            })
        ]

        spec = await generator.generate_council_spec("Test query")
        
        # Should have called model twice
        assert mock_model.work_on.call_count == 2
        assert spec.name == "SimpleCouncil"

    @pytest.mark.asyncio
    async def test_validation_error_retry(self, generator, mock_model):
        """Test retry when council spec is invalid."""
        # First attempt: references undefined agent
        invalid_response = {
            "name": "InvalidCouncil",
            "agents": [{"id": "agent1", "prompt": "Test"}],
            "steps": [{"type": "parallel", "agents": ["agent1", "undefined_agent"]}]
        }
        
        # Second attempt: valid
        valid_response = {
            "name": "ValidCouncil",
            "agents": [{"id": "agent1", "prompt": "Test"}],
            "steps": [{"type": "parallel", "agents": ["agent1"]}]
        }
        
        mock_model.work_on.side_effect = [
            json.dumps(invalid_response),
            json.dumps(valid_response)
        ]

        spec = await generator.generate_council_spec("Test query")
        
        assert mock_model.work_on.call_count == 2
        assert spec.name == "ValidCouncil"

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, generator, mock_model):
        """Test behavior when max retries exceeded."""
        mock_model.work_on.return_value = "Invalid JSON every time"
        
        with pytest.raises(ValueError) as exc:
            await generator.generate_council_spec("Test query")
        
        assert "Failed to generate valid council" in str(exc.value)
        assert mock_model.work_on.call_count == 3  # max retries

    def test_prompt_includes_examples(self):
        """Test that prompt includes examples."""
        assert "EXAMPLES:" in GENERATOR_PROMPT
        assert len(EXAMPLE_COUNCILS) > 0
        assert "council" in EXAMPLE_COUNCILS[0]
        assert "agents" in EXAMPLE_COUNCILS[0]["council"]

    @pytest.mark.asyncio
    async def test_custom_tools_included(self, mock_model):
        """Test that custom tools are included in prompt."""
        # Create generator with custom tools
        custom_tools = ["custom_analyzer", "custom_search"]
        generator = LLMCouncilGenerator(model=mock_model, available_tools=custom_tools)
        
        mock_model.work_on.return_value = json.dumps({
            "name": "TestCouncil",
            "agents": [{"id": "test", "prompt": "Test"}],
            "steps": []
        })
        
        await generator.generate_council_spec("Test")
        
        # Check that tools were included in prompt
        call_args = mock_model.work_on.call_args[0][0]
        assert "custom_analyzer" in call_args
        assert "custom_search" in call_args

    @pytest.mark.asyncio
    async def test_markdown_response_handling(self, generator, mock_model):
        """Test handling responses wrapped in markdown."""
        mock_model.work_on.return_value = """
        Here's the council specification:
        
        ```json
        {
            "name": "TestCouncil",
            "agents": [{"id": "test", "prompt": "Test agent"}],
            "steps": [{"type": "parallel", "agents": ["test"]}]
        }
        ```
        
        This council will help with testing.
        """
        
        spec = await generator.generate_council_spec("Test")
        assert spec.name == "TestCouncil"