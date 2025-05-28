"""Tests for parallel tool injection in agents."""

from konseho.agents.base import AgentWrapper
from konseho.tools.parallel import ParallelExecutor


class MockStrandsAgent:
    """Mock Strands agent for testing."""

    def __init__(self, name: str = "test_agent"):
        self.name = name
        self.tools = []
        self.call_count = 0

    def __call__(self, task: str) -> str:
        self.call_count += 1
        return f"Response to: {task}"


class TestAgentParallelTools:
    """Test parallel tool injection in AgentWrapper."""

    def test_parallel_tool_is_injected(self):
        """Test that parallel tool is automatically added to agent."""
        mock_agent = MockStrandsAgent()
        initial_tools_count = len(mock_agent.tools)

        wrapper = AgentWrapper(mock_agent)

        # Check that parallel tool was added
        assert len(mock_agent.tools) == initial_tools_count + 1

        # Find the parallel tool
        parallel_tool = None
        for tool in mock_agent.tools:
            if hasattr(tool, "__name__") and tool.__name__ == "parallel":
                parallel_tool = tool
                break

        assert parallel_tool is not None
        assert hasattr(parallel_tool, "__doc__")
        assert "parallel" in parallel_tool.__doc__.lower()

    def test_parallel_tool_functionality(self):
        """Test that the injected parallel tool works correctly."""

        # Create mock tools
        def mock_file_read(path: str) -> str:
            return f"Content of {path}"

        mock_file_read.__name__ = "file_read"

        def mock_process(data: str) -> str:
            return f"Processed: {data}"

        mock_process.__name__ = "process"

        # Create agent with tools
        mock_agent = MockStrandsAgent()
        mock_agent.tools = [mock_file_read, mock_process]

        wrapper = AgentWrapper(mock_agent)

        # Find the parallel tool
        parallel_tool = None
        for tool in mock_agent.tools:
            if hasattr(tool, "__name__") and tool.__name__ == "parallel":
                parallel_tool = tool
                break

        # Test parallel execution
        results = parallel_tool(
            tool_name="file_read",
            args_list=[
                {"path": "file1.txt"},
                {"path": "file2.txt"},
                {"path": "file3.txt"},
            ],
        )

        assert len(results) == 3
        assert results[0] == "Content of file1.txt"
        assert results[1] == "Content of file2.txt"
        assert results[2] == "Content of file3.txt"

    def test_parallel_tool_with_unknown_tool(self):
        """Test parallel tool handles unknown tool names gracefully."""
        mock_agent = MockStrandsAgent()
        wrapper = AgentWrapper(mock_agent)

        # Find the parallel tool
        parallel_tool = next(
            tool
            for tool in mock_agent.tools
            if hasattr(tool, "__name__") and tool.__name__ == "parallel"
        )

        results = parallel_tool(tool_name="unknown_tool", args_list=[{"arg": "value"}])

        assert len(results) == 1
        assert "Error:" in results[0] and "not found" in results[0]

    def test_parallel_tool_preserves_existing_tools(self):
        """Test that existing tools are preserved when adding parallel."""

        def existing_tool(x: int) -> int:
            return x * 2

        existing_tool.__name__ = "double"

        mock_agent = MockStrandsAgent()
        mock_agent.tools = [existing_tool]

        wrapper = AgentWrapper(mock_agent)

        # Check that both tools exist
        assert len(mock_agent.tools) == 2

        # Original tool still works
        assert existing_tool(5) == 10

        # Can find both tools
        tool_names = [t.__name__ for t in mock_agent.tools if hasattr(t, "__name__")]
        assert "double" in tool_names
        assert "parallel" in tool_names

    def test_parallel_tool_deduplication(self):
        """Test that parallel tool deduplicates work."""
        call_count = 0

        def counting_tool(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"processed: {value}"

        counting_tool.__name__ = "counting_tool"

        mock_agent = MockStrandsAgent()
        mock_agent.tools = [counting_tool]

        wrapper = AgentWrapper(mock_agent)
        parallel_tool = next(
            tool
            for tool in mock_agent.tools
            if hasattr(tool, "__name__") and tool.__name__ == "parallel"
        )

        # Execute with duplicates
        results = parallel_tool(
            tool_name="counting_tool",
            args_list=[
                {"value": "a"},
                {"value": "b"},
                {"value": "a"},  # duplicate
                {"value": "b"},  # duplicate
            ],
        )

        assert len(results) == 4
        assert call_count == 2  # Only unique values processed
        assert results[0] == results[2]  # Same result for 'a'
        assert results[1] == results[3]  # Same result for 'b'

    def test_wrapper_has_parallel_executor(self):
        """Test that wrapper has its own ParallelExecutor instance."""
        mock_agent = MockStrandsAgent()
        wrapper = AgentWrapper(mock_agent)

        assert hasattr(wrapper, "_parallel_executor")
        assert isinstance(wrapper._parallel_executor, ParallelExecutor)
