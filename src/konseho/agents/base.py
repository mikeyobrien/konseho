"""Base agent wrapper for Strands agents integration."""
from __future__ import annotations

import asyncio
import copy
import sys
from io import StringIO
from typing import Any
from strands import Agent, tool
from konseho.tools.parallel import ParallelExecutor


class AgentWrapper:
    __slots__ = ()
    """Wrapper for Strands agents to work within councils."""

    def __init__(self, agent: Agent, name: (str | None)=None, **kwargs):
        """Initialize agent wrapper.

        Args:
            agent: Strands Agent instance
            name: Optional name for identification
            **kwargs: Additional attributes (e.g., expertise_level, domain)
        """
        self.agent = agent
        self.name = name or f'agent_{id(agent)}'
        self._history = []
        self.system_prompt_override = None
        self._parallel_executor = ParallelExecutor()
        self._inject_parallel_tool()
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def work_on(self, task: str, buffered: bool=True) ->str:
        """Have the agent work on a task asynchronously.

        Args:
            task: The task to work on
            buffered: Whether to buffer output to prevent interleaving

        Returns:
            The agent's response
        """
        loop = asyncio.get_running_loop()
        if not hasattr(self.__class__, '_output_locks'):
            self.__class__._output_locks = {}
        if loop not in self.__class__._output_locks:
            self.__class__._output_locks[loop] = asyncio.Lock()
        output_lock = self.__class__._output_locks[loop]
        if buffered:
            async with output_lock:
                buffer = StringIO()
                original_stdout = sys.stdout
                try:
                    sys.stdout = buffer
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, self.agent, task)
                    captured_output = buffer.getvalue()
                finally:
                    sys.stdout = original_stdout
                if captured_output:
                    print(f'\n[{self.name}]:')
                    print(captured_output, end='')
                    sys.stdout.flush()
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.agent, task)
        if hasattr(result, 'message'):
            response = result.message
        else:
            response = str(result)
        self._history.append({'task': task, 'response': response})
        return response

    def get_history(self) ->list:
        """Get the agent's task history."""
        return self._history.copy()

    def clone(self, new_name: str) ->'AgentWrapper':
        """Create a clone of this agent wrapper with a new name.

        Args:
            new_name: Name for the cloned wrapper

        Returns:
            New AgentWrapper instance with cloned agent
        """
        cloned_agent = self._clone_agent(self.agent)
        custom_attrs = {}
        for attr in dir(self):
            if not attr.startswith('_') and attr not in ['agent', 'name',
                'work_on', 'get_history', 'clone']:
                value = getattr(self, attr)
                if not callable(value):
                    custom_attrs[attr] = value
        cloned_wrapper = AgentWrapper(cloned_agent, name=new_name, **
            custom_attrs)
        if self.system_prompt_override:
            cloned_wrapper.system_prompt_override = self.system_prompt_override
        return cloned_wrapper

    def _inject_parallel_tool(self):
        """Add parallel execution tool to agent."""

        @tool
        def parallel(tool_name: str, args_list: list[dict[str, Any]]) ->list[
            Any]:
            """Execute any tool multiple times in parallel with different arguments.

            Args:
                tool_name: Name of the tool to execute
                args_list: List of argument dictionaries for each execution

            Returns:
                List of results in the same order as arguments

            Example:
                parallel("file_read", [{"path": "file1.py"}, {"path": "file2.py"}])
            """
            target_tool = None
            for t in self.agent.tools:
                if hasattr(t, '__name__') and t.__name__ == tool_name:
                    target_tool = t
                    break
            if not target_tool:
                return [f"Error: Tool '{tool_name}' not found" for _ in
                    args_list]
            return self._parallel_executor.execute_parallel(target_tool,
                args_list)
        if hasattr(self.agent, 'tools') and isinstance(self.agent.tools, list):
            self.agent.tools.append(parallel)

    def _clone_agent(self, agent: Agent) ->Agent:
        """Clone a Strands agent preserving its configuration."""
        if hasattr(agent, '__class__'
            ) and agent.__class__.__name__ == 'MockStrandsAgent':
            cloned = agent.__class__(agent.name, agent.response)
            if hasattr(agent, 'delay'):
                cloned.delay = agent.delay
            if hasattr(agent, 'config'):
                cloned.config = copy.deepcopy(agent.config)
            return cloned
        if hasattr(agent, '_mock_name') and agent.__class__.__name__ == 'Mock':
            from unittest.mock import Mock
            cloned = Mock()
            for attr in dir(agent):
                if not attr.startswith('_') and not callable(getattr(agent,
                    attr)):
                    value = getattr(agent, attr)
                    if isinstance(value, (dict, list, set)):
                        setattr(cloned, attr, copy.deepcopy(value))
                    else:
                        setattr(cloned, attr, value)
            return cloned
        try:
            config = {'name': getattr(agent, 'name', 'cloned_agent'),
                'model': getattr(agent, 'model', 'gpt-4'), 'tools': getattr
                (agent, 'tools', []), 'temperature': getattr(agent,
                'temperature', 0.7)}
            if hasattr(agent, 'system_prompt'):
                config['system_prompt'] = agent.system_prompt
            if hasattr(agent, 'config'):
                config['config'] = copy.deepcopy(agent.config)
            from konseho.agents.base import create_agent
            return create_agent(**config)
        except Exception:
            return agent


def create_agent(**config) ->Agent:
    """Create a new Strands agent with given configuration.

    Creates a real Strands agent using the provided configuration.
    """
    model = config.get('model')
    if model is None:
        from konseho.config import create_model_from_config
        model = create_model_from_config()
    elif isinstance(model, str):
        from konseho.config import ModelConfig, create_model_from_config, get_model_config
        base_config = get_model_config()
        model_config = ModelConfig(provider=base_config.provider, model_id=
            model, api_key=base_config.api_key, additional_args=base_config
            .additional_args)
        model = create_model_from_config(model_config)
    tools = config.get('tools', [])
    name = config.get('name', 'agent')
    agent_args = {'model': model, 'tools': tools, 'callback_handler':
        config.get('callback_handler')}
    from datetime import datetime
    current_datetime = datetime.now()
    date_info = (
        f"\n\nCurrent date and time: {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    if 'system_prompt' in config:
        agent_args['system_prompt'] = config['system_prompt'] + date_info
    else:
        agent_args['system_prompt'
            ] = f'You are a helpful AI assistant.{date_info}'
    agent = Agent(**agent_args)
    if hasattr(agent, 'name'):
        agent.name = name
    if 'temperature' in config and hasattr(agent, 'temperature'):
        agent.temperature = config['temperature']
    return agent
