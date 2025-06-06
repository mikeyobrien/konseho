"""MCP server management and tool discovery."""

import logging
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from konseho.mcp.config import MCPConfigManager, MCPServerConfig
from konseho.tools.mcp_adapter import MCPToolAdapter

logger = logging.getLogger(__name__)


@dataclass
class MCPServerInstance:
    """Running MCP server instance."""

    name: str
    config: MCPServerConfig
    process: subprocess.Popen | None = None
    tools: dict[str, Callable] = None

    def __post_init__(self):
        if self.tools is None:
            self.tools = {}


class MCPServerManager:
    """Manage MCP servers and their tools."""

    def __init__(self, config_manager: MCPConfigManager | None = None):
        """Initialize MCP server manager.

        Args:
            config_manager: Configuration manager. If None, creates default.
        """
        self.config_manager = config_manager or MCPConfigManager()
        self.servers: dict[str, MCPServerInstance] = {}
        self._tool_registry: dict[str, str] = {}  # tool_name -> server_name mapping

    async def start_server(self, name: str) -> bool:
        """Start an MCP server by name.

        Args:
            name: Server name from configuration

        Returns:
            True if server started successfully
        """
        config = self.config_manager.get_server(name)
        if not config:
            logger.error(f"No configuration found for server: {name}")
            return False

        if not config.enabled:
            logger.info(f"Server {name} is disabled in configuration")
            return False

        # Check if already running
        if name in self.servers and self.servers[name].process:
            logger.info(f"Server {name} is already running")
            return True

        try:
            # Prepare environment
            env = os.environ.copy()
            for key, value in config.env.items():
                # Expand environment variables
                if value.startswith("${") and value.endswith("}"):
                    var_name = value[2:-1]
                    env[key] = os.environ.get(var_name, "")
                else:
                    env[key] = value

            # Start the server process
            cmd = [config.command] + config.args
            logger.info(f"Starting MCP server {name}: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Create server instance
            instance = MCPServerInstance(name, config, process)
            self.servers[name] = instance

            # Discover tools from the server
            await self._discover_tools(instance)

            logger.info(f"Started MCP server {name} with {len(instance.tools)} tools")
            return True

        except Exception as e:
            logger.error(f"Failed to start MCP server {name}: {e}")
            return False

    async def stop_server(self, name: str) -> bool:
        """Stop an MCP server.

        Args:
            name: Server name

        Returns:
            True if server stopped successfully
        """
        if name not in self.servers:
            logger.info(f"Server {name} is not running")
            return True

        instance = self.servers[name]
        if instance.process:
            try:
                instance.process.terminate()
                instance.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                instance.process.kill()

            logger.info(f"Stopped MCP server {name}")

        # Remove from registry
        del self.servers[name]

        # Remove tools from registry
        self._tool_registry = {
            k: v for k, v in self._tool_registry.items() if v != name
        }

        return True

    async def start_all_enabled(self):
        """Start all enabled servers from configuration."""
        enabled = self.config_manager.get_enabled_servers()

        for name in enabled:
            await self.start_server(name)

    async def stop_all(self):
        """Stop all running servers."""
        server_names = list(self.servers.keys())

        for name in server_names:
            await self.stop_server(name)

    def get_tool(self, tool_name: str) -> Callable | None:
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

        return self.servers[server_name].tools.get(tool_name)

    def get_tools_for_server(self, server_name: str) -> dict[str, Callable]:
        """Get all tools from a specific server.

        Args:
            server_name: Name of the server

        Returns:
            Dictionary of tool_name -> tool_function
        """
        if server_name not in self.servers:
            return {}

        return self.servers[server_name].tools.copy()

    def get_all_tools(self) -> dict[str, Callable]:
        """Get all available tools from all running servers.

        Returns:
            Dictionary of tool_name -> tool_function
        """
        all_tools = {}

        for server in self.servers.values():
            all_tools.update(server.tools)

        return all_tools

    def list_tools(self) -> list[dict[str, str]]:
        """List all available tools with metadata.

        Returns:
            List of tool information dictionaries
        """
        tools = []

        for server_name, server in self.servers.items():
            for tool_name, tool_func in server.tools.items():
                tools.append(
                    {
                        "name": tool_name,
                        "server": server_name,
                        "description": (
                            getattr(tool_func, "__doc__", "").strip().split("\n")[0]
                            if hasattr(tool_func, "__doc__")
                            else ""
                        ),
                        "enabled": server.config.enabled,
                    }
                )

        return tools

    async def _discover_tools(self, instance: MCPServerInstance):
        """Discover tools from an MCP server.

        This is a simplified version. In practice, this would:
        1. Communicate with the MCP server
        2. Request available tools
        3. Create wrapped tool functions
        """
        # For now, simulate tool discovery based on server type
        # In a real implementation, this would query the MCP server

        mock_tools = self._get_mock_tools(instance.name)

        for tool_name, tool_func in mock_tools.items():
            # Wrap with MCP adapter
            wrapped_tool = MCPToolAdapter(tool_func, tool_name)
            instance.tools[tool_name] = wrapped_tool
            self._tool_registry[tool_name] = instance.name

    def _get_mock_tools(self, server_name: str) -> dict[str, Callable]:
        """Get mock tools for demonstration.

        In practice, these would be discovered from the MCP server.
        """
        if "filesystem" in server_name:
            return {
                "read_file": lambda path: f"Contents of {path}",
                "write_file": lambda path, content: f"Wrote to {path}",
                "list_directory": lambda path="": f"Files in {path}",
            }
        elif "github" in server_name:
            return {
                "search_repos": lambda query: f"Repos matching {query}",
                "get_repo": lambda repo: f"Info about {repo}",
                "create_issue": lambda repo, title, body: f"Created issue in {repo}",
            }
        elif "search" in server_name:
            return {
                "web_search": lambda query, count=10: f"Search results for {query}",
            }
        else:
            return {
                f"{server_name}_tool": lambda *args, **kwargs: f"Tool from {server_name}",
            }


class MCPToolSelector:
    """Select and configure tools for agents at runtime."""

    def __init__(self, server_manager: MCPServerManager):
        """Initialize tool selector.

        Args:
            server_manager: MCP server manager instance
        """
        self.server_manager = server_manager

    def select_tools(
        self,
        tool_names: list[str] | None = None,
        servers: list[str] | None = None,
        tags: list[str] | None = None,
        preset: str | None = None,
        exclude_tools: list[str] | None = None,
        exclude_servers: list[str] | None = None,
    ) -> list[Callable]:
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
        # Handle presets first
        if preset:
            preset_config = self._get_preset_config(preset)
            if preset_config:
                tool_names = preset_config.get("tools", tool_names)
                servers = preset_config.get("servers", servers)
                tags = preset_config.get("tags", tags)
        selected_tools = []
        all_tools = self.server_manager.get_all_tools()

        for tool_name, tool_func in all_tools.items():
            # Check if tool should be included
            if tool_names and tool_name not in tool_names:
                continue

            if exclude_tools and tool_name in exclude_tools:
                continue

            # Check server filters
            server_name = self.server_manager._tool_registry.get(tool_name)

            if servers and server_name not in servers:
                continue

            if exclude_servers and server_name in exclude_servers:
                continue

            # Check tags (if implemented in tool metadata)
            if tags:
                # For now, skip tag filtering as it's not implemented
                # In a real implementation, tools would have metadata with tags
                pass

            selected_tools.append(tool_func)

        return selected_tools

    def _get_preset_config(self, preset: str) -> dict[str, Any] | None:
        """Get preset configuration.

        Args:
            preset: Preset name

        Returns:
            Preset configuration or None
        """
        presets = {
            "coder": {
                "tools": ["file_read", "file_write", "code_edit", "shell_run"],
                "tags": ["file", "code", "shell"],
            },
            "researcher": {
                "tools": ["web_search", "http_get", "file_read", "file_write"],
                "tags": ["web", "search", "http"],
            },
            "analyst": {
                "tools": ["file_read", "file_write", "data_process", "calculate"],
                "tags": ["data", "analysis", "file"],
            },
            "communicator": {
                "tools": ["send_message", "send_email", "notify"],
                "tags": ["messaging", "communication"],
            },
        }
        return presets.get(preset)

    def create_tool_preset(self, name: str, **selection_kwargs) -> "ToolPreset":
        """Create a reusable tool selection preset.

        Args:
            name: Preset name
            **selection_kwargs: Arguments for select_tools()

        Returns:
            ToolPreset instance
        """
        return ToolPreset(name, self, **selection_kwargs)


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

    def get_tools(self) -> list[Callable]:
        """Get tools based on this preset."""
        return self.selector.select_tools(
            tool_names=self.tool_names,
            servers=self.servers,
            tags=self.tags,
            exclude_tools=self.exclude_tools,
            exclude_servers=self.exclude_servers,
        )
