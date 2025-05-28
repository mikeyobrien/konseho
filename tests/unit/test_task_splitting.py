"""Unit tests for task splitting in SplitStep."""

from unittest.mock import patch

import pytest

from konseho.agents.base import AgentWrapper
from konseho.core.context import Context
from konseho.core.steps import SplitStep
from tests.fixtures import MockStrandsAgent


class TestTaskSplitting:
    """Tests for intelligent task splitting in SplitStep."""

    def test_determine_agent_count_fixed(self):
        """Test fixed agent count strategy."""
        agent_template = MockStrandsAgent("template")
        step = SplitStep(
            agent_template=agent_template,
            min_agents=3,
            max_agents=10,
            split_strategy="fixed",
        )

        # Should always return min_agents for fixed strategy
        assert step._determine_agent_count("short task", Context()) == 3
        assert step._determine_agent_count("very long task " * 100, Context()) == 3

    def test_determine_agent_count_auto(self):
        """Test automatic agent count based on task complexity."""
        agent_template = MockStrandsAgent("template")
        step = SplitStep(
            agent_template=agent_template,
            min_agents=2,
            max_agents=8,
            split_strategy="auto",
        )

        # Short task should use minimum agents
        short_task = "Fix the bug"
        assert step._determine_agent_count(short_task, Context()) == 2

        # Medium task should scale up
        medium_task = " ".join(["word"] * 150)  # 150 words
        count = step._determine_agent_count(medium_task, Context())
        assert 2 < count < 8

        # Long task should hit maximum
        long_task = " ".join(["word"] * 500)  # 500 words
        assert step._determine_agent_count(long_task, Context()) == 8

    def test_split_task_by_lines(self):
        """Test splitting multi-line tasks."""
        agent_template = MockStrandsAgent("template")
        step = SplitStep(agent_template=agent_template)

        task = """1. Implement user authentication
2. Add database models
3. Create API endpoints
4. Write unit tests"""

        subtasks = step._split_task(task, 4)

        assert len(subtasks) == 4
        assert "user authentication" in subtasks[0]
        assert "database models" in subtasks[1]
        assert "API endpoints" in subtasks[2]
        assert "unit tests" in subtasks[3]

    def test_split_task_by_sentences(self):
        """Test splitting tasks by sentences."""
        agent_template = MockStrandsAgent("template")
        step = SplitStep(agent_template=agent_template)

        task = "First, analyze the codebase. Then identify performance bottlenecks. Finally, implement optimizations."

        subtasks = step._split_task(task, 3)

        assert len(subtasks) == 3
        assert "analyze the codebase" in subtasks[0]
        assert "identify performance bottlenecks" in subtasks[1]
        assert "implement optimizations" in subtasks[2]

    def test_split_task_by_components(self):
        """Test splitting tasks that mention different components."""
        agent_template = MockStrandsAgent("template")
        step = SplitStep(agent_template=agent_template)

        task = "Fix the frontend React components, optimize the backend API, and update the database schema"

        subtasks = step._split_task(task, 3)

        assert len(subtasks) == 3
        assert any("frontend" in st and "React" in st for st in subtasks)
        assert any("backend" in st and "API" in st for st in subtasks)
        assert any("database" in st and "schema" in st for st in subtasks)

    def test_split_task_code_analysis(self):
        """Test splitting code analysis tasks by file patterns."""
        agent_template = MockStrandsAgent("template")
        step = SplitStep(agent_template=agent_template)

        task = "Review all Python files in src/, test files in tests/, and documentation in docs/"

        subtasks = step._split_task(task, 3)

        assert len(subtasks) == 3
        assert any("Python files" in st and "src/" in st for st in subtasks)
        assert any("test files" in st and "tests/" in st for st in subtasks)
        assert any("documentation" in st and "docs/" in st for st in subtasks)

    def test_split_task_uneven_distribution(self):
        """Test handling tasks that don't split evenly."""
        agent_template = MockStrandsAgent("template")
        step = SplitStep(agent_template=agent_template)

        task = "Task 1. Task 2. Task 3. Task 4. Task 5."

        # Split among 3 agents
        subtasks = step._split_task(task, 3)

        assert len(subtasks) == 3
        # Should distribute 5 tasks among 3 agents: 2, 2, 1
        task_counts = [st.count("Task") for st in subtasks]
        assert sorted(task_counts) == [1, 2, 2]

    def test_split_task_with_context(self):
        """Test task splitting considers context for better distribution."""
        agent_template = MockStrandsAgent("template")
        step = SplitStep(agent_template=agent_template)

        # Add context that might influence splitting
        context = Context(
            {
                "project_structure": {
                    "frontend": ["React", "TypeScript"],
                    "backend": ["Python", "FastAPI"],
                    "database": ["PostgreSQL"],
                }
            }
        )

        task = "Refactor the entire application architecture"

        # Should split based on project structure in context
        subtasks = step._split_task_with_context(task, 3, context)

        assert len(subtasks) == 3
        assert any("frontend" in st.lower() for st in subtasks)
        assert any("backend" in st.lower() for st in subtasks)
        assert any("database" in st.lower() for st in subtasks)

    @pytest.mark.asyncio
    async def test_split_step_execution(self):
        """Test full SplitStep execution with task splitting."""
        agent_template = MockStrandsAgent("template")
        step = SplitStep(
            agent_template=agent_template,
            min_agents=2,
            max_agents=4,
            split_strategy="auto",
        )

        task = "Part 1: Do this. Part 2: Do that. Part 3: Do another."
        context = Context()

        # Mock agent creation
        with patch.object(step, "_create_agent_clones") as mock_create:
            mock_agents = [
                AgentWrapper(MockStrandsAgent(f"agent_{i}", f"Result {i}"))
                for i in range(3)
            ]
            mock_create.return_value = mock_agents

            result = await step.execute(task, context)

            assert result["num_agents"] == 3
            assert len(result["split_results"]) == 3
            assert all(f"Result {i}" in result["split_results"] for i in range(3))
            assert result["strategy"] == "auto"

            # Verify each agent got a different part
            mock_create.assert_called_once_with(3)

    def test_split_task_fallback(self):
        """Test fallback when intelligent splitting fails."""
        agent_template = MockStrandsAgent("template")
        step = SplitStep(agent_template=agent_template)

        # Single word task that's hard to split
        task = "Debug"

        subtasks = step._split_task(task, 3)

        assert len(subtasks) == 3
        # Should fall back to distributing the same task
        assert all("Debug" in st for st in subtasks)
        # But with different agent assignments
        assert all(f"Agent {i+1}" in subtasks[i] for i in range(3))
