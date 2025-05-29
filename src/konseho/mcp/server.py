"""MCP server management and tool discovery."""
from __future__ import annotations

import logging
import os
import subprocess
from collections.abc import Callable
from typing import Protocol, Any
from konseho.protocols import JSON


class ToolFunction(Protocol):
    """Protocol for MCP tool functions."""
    def __call__(self, *args: object, **kwargs: object) -> object:
        ...
from dataclasses import dataclass
from konseho.mcp.config import MCPConfigManager, MCPServerConfig
from konseho.tools.mcp_adapter import MCPToolAdapter
logger = logging.getLogger(__name__)


@dataclass
class MCPServerInstance:
    """Running MCP server instance."""
    name: str
    config: MCPServerConfig
    process: subprocess.Popen[str] | None = None
    tools: dict[str, ToolFunction] | None = None

    def __post_init__(self) -> None:
        if self.tools is None:
            self.tools = {}


class MCPServerManager:
    """Manage MCP servers and their tools."""

    def __init__(self, config_manager: (MCPConfigManager | None)=None):
        """Initialize MCP server manager.

        Args:
            config_manager: Configuration manager. If None, creates default.
        """
        self.config_manager = config_manager or MCPConfigManager()
        self.servers: dict[str, MCPServerInstance] = {}
        self._tool_registry: dict[str, str] = {}

    async def start_server(self, name: str) ->bool:
        """Start an MCP server by name.

        Args:
            name: Server name from configuration

        Returns:
            True if server started successfully
        """
        config = self.config_manager.get_server(name)
        if not config:
            logger.error(f'No configuration found for server: {name}')
            return False
        if not config.enabled:
            logger.info(f'Server {name} is disabled in configuration')
            return False
        if name in self.servers and self.servers[name].process:
            logger.info(f'Server {name} is already running')
            return True
        try:
            env = os.environ.copy()
            for key, value in config.env.items():
                if value.startswith('${') and value.endswith('}'):
                    var_name = value[2:-1]
                    env[key] = os.environ.get(var_name, '')
                else:
                    env[key] = value
            cmd = [config.command] + config.args
            logger.info(f"Starting MCP server {name}: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True)
            instance = MCPServerInstance(name, config, process)
            self.servers[name] = instance
            await self._discover_tools(instance)
            logger.info(
                f'Started MCP server {name} with {len(instance.tools) if instance.tools else 0} tools')
            return True
        except Exception as e:
            logger.error(f'Failed to start MCP server {name}: {e}')
            return False

    async def stop_server(self, name: str) ->bool:
        """Stop an MCP server.

        Args:
            name: Server name

        Returns:
            True if server stopped successfully
        """
        if name not in self.servers:
            logger.info(f'Server {name} is not running')
            return True
        instance = self.servers[name]
        if instance.process:
            try:
                instance.process.terminate()
                instance.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                instance.process.kill()
            logger.info(f'Stopped MCP server {name}')
        del self.servers[name]
        self._tool_registry = {k: v for k, v in self._tool_registry.items() if
            v != name}
        return True

    async def start_all_enabled(self) -> None:
        """Start all enabled servers from configuration."""
        enabled = self.config_manager.get_enabled_servers()
        for name in enabled:
            await self.start_server(name)

    async def stop_all(self) -> None:
        """Stop all running servers."""
        server_names = list(self.servers.keys())
        for name in server_names:
            await self.stop_server(name)

    def get_tool(self, tool_name: str) ->(ToolFunction | None):
        """Get a specific tool by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool function if found, None otherwise
        """
        server_name = self._tool_registry.get(tool_name)
        if not server_name:
            return None
        if server_name not in self.servers:
            return None
        tools = self.servers[server_name].tools
        if tools is None:
            return None
        return tools.get(tool_name)

    def get_tools_for_server(self, server_name: str) ->dict[str, ToolFunction]:
        """Get all tools from a specific server.

        Args:
            server_name: Name of the server

        Returns:
            Dictionary of tool_name -> tool_function
        """
        if server_name not in self.servers:
            return {}
        tools = self.servers[server_name].tools
        if tools is None:
            return {}
        return tools.copy()

    def get_all_tools(self) ->dict[str, ToolFunction]:
        """Get all available tools from all running servers.

        Returns:
            Dictionary of tool_name -> tool_function
        """
        all_tools: dict[str, ToolFunction] = {}
        for server in self.servers.values():
            if server.tools is not None:
                all_tools.update(server.tools)
        return all_tools

    def list_tools(self) ->list[dict[str, str | bool]]:
        """List all available tools with metadata.

        Returns:
            List of tool information dictionaries
        """
        tools = []
        for server_name, server in self.servers.items():
            if server.tools is not None:
                for tool_name, tool_func in server.tools.items():
                    tools.append({'name': tool_name, 'server': server_name,
                        'description': getattr(tool_func, '__doc__', '').strip(
                        ).split('\n')[0] if hasattr(tool_func, '__doc__') else
                        '', 'enabled': server.config.enabled})
        return tools

    async def _discover_tools(self, instance: MCPServerInstance) -> None:
        """Discover tools from an MCP server.

        This is a simplified version. In practice, this would:
        1. Communicate with the MCP server
        2. Request available tools
        3. Create wrapped tool functions
        """
        mock_tools = self._get_mock_tools(instance.name)
        for tool_name, tool_func in mock_tools.items():
            wrapped_tool = MCPToolAdapter(tool_func, tool_name)
            if instance.tools is not None:
                instance.tools[tool_name] = wrapped_tool
            self._tool_registry[tool_name] = instance.name

    def _get_mock_tools(self, server_name: str) ->dict[str, ToolFunction]:
        """Get mock tools for demonstration.

        In practice, these would be discovered from the MCP server.
        """
        # Create proper functions that match ToolFunction protocol
        def read_file(*args: object, **kwargs: object) -> object:
            path = args[0] if args else kwargs.get('path', '')
            return f'Contents of {path}'
        
        def write_file(*args: object, **kwargs: object) -> object:
            path = args[0] if args else kwargs.get('path', '')
            content = args[1] if len(args) > 1 else kwargs.get('content', '')
            return f'Wrote to {path}'
        
        def list_directory(*args: object, **kwargs: object) -> object:
            path = args[0] if args else kwargs.get('path', '')
            return f'Files in {path}'
        
        def search_repos(*args: object, **kwargs: object) -> object:
            query = args[0] if args else kwargs.get('query', '')
            return f'Repos matching {query}'
        
        def get_repo(*args: object, **kwargs: object) -> object:
            repo = args[0] if args else kwargs.get('repo', '')
            return f'Info about {repo}'
        
        def create_issue(*args: object, **kwargs: object) -> object:
            repo = args[0] if args else kwargs.get('repo', '')
            title = args[1] if len(args) > 1 else kwargs.get('title', '')
            body = args[2] if len(args) > 2 else kwargs.get('body', '')
            return f'Created issue in {repo}'
        
        def web_search(*args: object, **kwargs: object) -> object:
            query = args[0] if args else kwargs.get('query', '')
            count = kwargs.get('count', 10)
            return f'Search results for {query}'
        
        def generic_tool(*args: object, **kwargs: object) -> object:
            return f'Tool from {server_name}'
        
        if 'filesystem' in server_name:
            return {'read_file': read_file,
                'write_file': write_file,
                'list_directory': list_directory}
        elif 'github' in server_name:
            return {'search_repos': search_repos,
                'get_repo': get_repo,
                'create_issue': create_issue}
        elif 'search' in server_name:
            return {'web_search': web_search}
        else:
            return {f'{server_name}_tool': generic_tool}


class MCPToolSelector:
    """Select and configure tools for agents at runtime."""

    def __init__(self, server_manager: MCPServerManager):
        """Initialize tool selector.

        Args:
            server_manager: MCP server manager instance
        """
        self.server_manager = server_manager

    def select_tools(self, tool_names: (list[str] | None)=None, servers: (
        list[str] | None)=None, tags: (list[str] | None)=None, preset: (str |
        None)=None, exclude_tools: (list[str] | None)=None, exclude_servers:
        (list[str] | None)=None) -> list[ToolFunction]:
        """Select tools based on criteria.

        Args:
            tool_names: Specific tools to include (None = all)
            servers: Only tools from these servers (None = all)
            tags: Only tools with these tags (None = all)
            preset: Use a preset configuration
            exclude_tools: Tools to exclude
            exclude_servers: Servers to exclude

        Returns:
            List of selected tool functions
        """
        if preset:
            if preset_config := self._get_preset_config(preset):
                preset_tools = preset_config.get('tools')
                if isinstance(preset_tools, list):
                    tool_names = preset_tools
                preset_servers = preset_config.get('servers')
                if isinstance(preset_servers, list):
                    servers = preset_servers
                preset_tags = preset_config.get('tags')
                if isinstance(preset_tags, list):
                    tags = preset_tags
        selected_tools = []
        all_tools = self.server_manager.get_all_tools()
        for tool_name, tool_func in all_tools.items():
            if tool_names and tool_name not in tool_names:
                continue
            if exclude_tools and tool_name in exclude_tools:
                continue
            server_name = self.server_manager._tool_registry.get(tool_name)
            if servers and server_name not in servers:
                continue
            if exclude_servers and server_name in exclude_servers:
                continue
            if tags:
                pass
            selected_tools.append(tool_func)
        return selected_tools

    def _get_preset_config(self, preset: str) ->(dict[str, object] | None):
        """Get preset configuration.

        Args:
            preset: Preset name

        Returns:
            Preset configuration or None
        """
        presets: dict[str, dict[str, object]] = {'coder': {'tools': ['file_read', 'file_write',
            'code_edit', 'shell_run'], 'tags': ['file', 'code', 'shell']},
            'researcher': {'tools': ['web_search', 'http_get', 'file_read',
            'file_write'], 'tags': ['web', 'search', 'http']}, 'analyst': {
            'tools': ['file_read', 'file_write', 'data_process',
            'calculate'], 'tags': ['data', 'analysis', 'file']},
            'communicator': {'tools': ['send_message', 'send_email',
            'notify'], 'tags': ['messaging', 'communication']}}
        preset_config = presets.get(preset)
        return preset_config if preset_config else None

    def create_tool_preset(self, name: str, **selection_kwargs: object) ->'ToolPreset':
        """Create a reusable tool selection preset.

        Args:
            name: Preset name
            **selection_kwargs: Arguments for select_tools()

        Returns:
            ToolPreset instance
        """
        # Extract specific kwargs
        tool_names = selection_kwargs.get('tool_names')
        if isinstance(tool_names, list):
            tool_names_list: list[str] | None = tool_names
        else:
            tool_names_list = None
            
        servers = selection_kwargs.get('servers')
        if isinstance(servers, list):
            servers_list: list[str] | None = servers
        else:
            servers_list = None
            
        tags = selection_kwargs.get('tags')
        if isinstance(tags, list):
            tags_list: list[str] | None = tags
        else:
            tags_list = None
            
        exclude_tools = selection_kwargs.get('exclude_tools')
        if isinstance(exclude_tools, list):
            exclude_tools_list: list[str] | None = exclude_tools
        else:
            exclude_tools_list = None
            
        exclude_servers = selection_kwargs.get('exclude_servers')
        if isinstance(exclude_servers, list):
            exclude_servers_list: list[str] | None = exclude_servers
        else:
            exclude_servers_list = None
            
        return ToolPreset(
            name, 
            self, 
            tool_names=tool_names_list,
            servers=servers_list,
            tags=tags_list,
            exclude_tools=exclude_tools_list,
            exclude_servers=exclude_servers_list
        )


@dataclass
class ToolPreset:
    """Reusable tool selection configuration."""
    name: str
    selector: MCPToolSelector
    tool_names: list[str] | None = None
    servers: list[str] | None = None
    tags: list[str] | None = None
    exclude_tools: list[str] | None = None
    exclude_servers: list[str] | None = None

    def get_tools(self) ->list[ToolFunction]:
        """Get tools based on this preset."""
        return self.selector.select_tools(tool_names=self.tool_names,
            servers=self.servers, tags=self.tags, exclude_tools=self.
            exclude_tools, exclude_servers=self.exclude_servers)
