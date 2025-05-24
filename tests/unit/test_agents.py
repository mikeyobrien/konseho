"""Unit tests for Agent wrappers."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from konseho import AgentWrapper, HumanAgent
from tests.fixtures import MockStrandsAgent


class TestAgentWrapper:
    """Tests for AgentWrapper class."""
    
    def test_agent_wrapper_initialization(self):
        """Test agent wrapper initialization."""
        mock_agent = MockStrandsAgent("test_agent")
        
        # Without name
        wrapper = AgentWrapper(mock_agent)
        assert wrapper.agent is mock_agent
        assert wrapper.name.startswith("agent_")
        
        # With name
        wrapper = AgentWrapper(mock_agent, name="custom_name")
        assert wrapper.name == "custom_name"
    
    @pytest.mark.asyncio
    async def test_agent_work_on_basic(self):
        """Test agent work_on method."""
        mock_agent = MockStrandsAgent("test", "Test response")
        wrapper = AgentWrapper(mock_agent, name="test_wrapper")
        
        result = await wrapper.work_on("Test task")
        
        assert result == "Test response (call 1)"
        assert mock_agent.call_count == 1
        assert mock_agent.call_history[0] == "Test task"
    
    @pytest.mark.asyncio
    async def test_agent_work_on_multiple_calls(self):
        """Test agent maintains call history."""
        mock_agent = MockStrandsAgent("test", "Response")
        wrapper = AgentWrapper(mock_agent)
        
        # Multiple calls
        result1 = await wrapper.work_on("Task 1")
        result2 = await wrapper.work_on("Task 2")
        result3 = await wrapper.work_on("Task 3")
        
        assert mock_agent.call_count == 3
        assert len(wrapper._history) == 3
        
        # Check history
        assert wrapper._history[0]["task"] == "Task 1"
        assert wrapper._history[0]["response"] == "Response (call 1)"
        assert wrapper._history[2]["task"] == "Task 3"
        assert wrapper._history[2]["response"] == "Response (call 3)"
    
    @pytest.mark.asyncio
    async def test_agent_async_execution(self):
        """Test agent runs in async executor."""
        # Create agent with delay to test async
        mock_agent = MockStrandsAgent("test", "Response", delay=0.1)
        wrapper = AgentWrapper(mock_agent)
        
        # Should not block
        start = asyncio.get_event_loop().time()
        task = asyncio.create_task(wrapper.work_on("Task"))
        
        # Can do other things while waiting
        await asyncio.sleep(0.05)
        
        result = await task
        duration = asyncio.get_event_loop().time() - start
        
        assert result == "Response (call 1)"
        assert duration >= 0.1  # Should take at least the delay time
    
    @pytest.mark.asyncio
    async def test_agent_result_extraction(self):
        """Test different result format handling."""
        # Test with result object
        mock_agent = MockStrandsAgent("test", "Message content")
        wrapper = AgentWrapper(mock_agent)
        
        result = await wrapper.work_on("Task")
        assert result == "Message content (call 1)"
        
        # Test with string result (mock returning string directly)
        class StringAgent:
            def __call__(self, prompt):
                return "Direct string response"
        
        wrapper2 = AgentWrapper(StringAgent())
        result2 = await wrapper2.work_on("Task")
        assert result2 == "Direct string response"
    
    def test_agent_get_history(self):
        """Test getting agent history."""
        mock_agent = MockStrandsAgent("test")
        wrapper = AgentWrapper(mock_agent)
        
        # Initially empty
        assert wrapper.get_history() == []
        
        # Add some history
        asyncio.run(wrapper.work_on("Task 1"))
        asyncio.run(wrapper.work_on("Task 2"))
        
        history = wrapper.get_history()
        assert len(history) == 2
        assert history[0]["task"] == "Task 1"
        assert history[1]["task"] == "Task 2"
        
        # Verify it's a copy
        history.append({"fake": "entry"})
        assert len(wrapper.get_history()) == 2  # Original unchanged


class TestHumanAgent:
    """Tests for HumanAgent class."""
    
    def test_human_agent_initialization(self):
        """Test human agent initialization."""
        # Default initialization
        agent = HumanAgent()
        assert agent.name == "human"
        assert agent.input_handler is not None
        
        # Custom name
        agent = HumanAgent(name="alice")
        assert agent.name == "alice"
        
        # Custom input handler
        handler = lambda prompt: "custom response"
        agent = HumanAgent(input_handler=handler)
        assert agent.input_handler == handler
    
    @pytest.mark.asyncio
    async def test_human_agent_with_custom_handler(self):
        """Test human agent with custom input handler."""
        responses = ["Response 1", "Response 2"]
        call_count = 0
        
        def custom_handler(prompt: str) -> str:
            nonlocal call_count
            response = responses[call_count]
            call_count += 1
            return response
        
        agent = HumanAgent(input_handler=custom_handler)
        
        result1 = await agent.work_on("Task 1")
        result2 = await agent.work_on("Task 2")
        
        assert result1 == "Response 1"
        assert result2 == "Response 2"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_human_agent_history(self):
        """Test human agent maintains history."""
        agent = HumanAgent(input_handler=lambda p: f"Response to: {p}")
        
        await agent.work_on("Task 1")
        await agent.work_on("Task 2")
        
        history = agent.get_history()
        assert len(history) == 2
        assert history[0]["task"] == "Task 1"
        assert history[0]["response"] == "Response to: Task 1"
    
    @pytest.mark.asyncio
    async def test_human_agent_async_execution(self):
        """Test human agent runs input handler in executor."""
        # Simulate slow input
        def slow_handler(prompt: str) -> str:
            import time
            time.sleep(0.1)
            return "Response"
        
        agent = HumanAgent(input_handler=slow_handler)
        
        # Should not block event loop
        start = asyncio.get_event_loop().time()
        result = await agent.work_on("Task")
        duration = asyncio.get_event_loop().time() - start
        
        assert result == "Response"
        assert duration >= 0.1
    
    @patch('builtins.input', return_value="User input response")
    @patch('builtins.print')
    def test_human_agent_default_handler(self, mock_print, mock_input):
        """Test default console input handler."""
        agent = HumanAgent()
        
        # Use default handler
        result = agent._default_input_handler("Test task")
        
        # Check prompts were printed
        mock_print.assert_called()
        call_args = [call[0][0] for call in mock_print.call_args_list]
        assert any("Human Input Required" in str(arg) for arg in call_args)
        assert any("Test task" in str(arg) for arg in call_args)
        
        # Check input was called and result returned
        mock_input.assert_called_once_with("Your response: ")
        assert result == "User input response"
    
    def test_human_agent_has_required_methods(self):
        """Test human agent has required interface methods."""
        agent = HumanAgent()
        
        assert hasattr(agent, 'work_on')
        assert hasattr(agent, 'get_history')
        assert asyncio.iscoroutinefunction(agent.work_on)