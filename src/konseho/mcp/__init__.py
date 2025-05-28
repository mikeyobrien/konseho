"""MCP (Model Context Protocol) integration for Konseho."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any, Dict, List, Optional

from konseho.mcp.config import MCPConfigManager, MCPServerConfig
from konseho.mcp.server import MCPServerManager, MCPToolSelector, ToolPreset

logger = logging.getLogger(__name__)


class MCP:
    """High-level interface for MCP integration."""

    def __init__(self, config_path: str | None = None):
        """Initialize MCP integration.

        Args:
            config_path: Path to mcp.json file (optional)
        """
        self.config_manager = MCPConfigManager(config_path)
        self.server_manager = MCPServerManager(self.config_manager)
        self.tool_selector = MCPToolSelector(self.server_manager)
        self._loop = None

    def _ensure_loop(self):
        """Ensure event loop exists for async operations."""
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

    def start_server(self, name: str) -> bool:
        """Start a specific MCP server.

        Args:
            name: Server name from mcp.json

        Returns:
            True if successful
        """
        self._ensure_loop()
        return self._loop.run_until_complete(self.server_manager.start_server(name))

    def start_all(self) -> dict[str, bool]:
        """Start all enabled MCP servers.

        Returns:
            Dictionary of server_name -> success status
        """
        self._ensure_loop()
        self._loop.run_until_complete(self.server_manager.start_all_enabled())

        return {
            name: bool(server.process)
            for name, server in self.server_manager.servers.items()
        }

    def stop_server(self, name: str) -> bool:
        """Stop a specific MCP server.

        Args:
            name: Server name

        Returns:
            True if successful
        """
        self._ensure_loop()
        return self._loop.run_until_complete(self.server_manager.stop_server(name))

    def stop_all(self):
        """Stop all running MCP servers."""
        self._ensure_loop()
        self._loop.run_until_complete(self.server_manager.stop_all())

    def get_tools(
        self,
        tools: list[str] | None = None,
        servers: list[str] | None = None,
        exclude_tools: list[str] | None = None,
        exclude_servers: list[str] | None = None,
    ) -> list[Callable]:
        """Get tools with filtering.

        Args:
            tools: Specific tool names to include
            servers: Only include tools from these servers
            exclude_tools: Tool names to exclude
            exclude_servers: Server names to exclude

        Returns:
            List of tool functions ready for use in agents
        """
        return self.tool_selector.select_tools(
            tool_names=tools,
            server_names=servers,
            exclude_tools=exclude_tools,
            exclude_servers=exclude_servers,
        )

    def create_preset(self, name: str, **kwargs) -> ToolPreset:
        """Create a reusable tool selection preset.

        Args:
            name: Preset name
            **kwargs: Selection criteria (tools, servers, etc.)

        Returns:
            ToolPreset instance

        Example:
            # Create presets for different agent types
            research_preset = mcp.create_preset(
                "research",
                servers=["brave-search", "github"]
            )

            file_preset = mcp.create_preset(
                "files",
                servers=["filesystem"],
                exclude_tools=["delete_file"]
            )
        """
        return self.tool_selector.create_tool_preset(name, **kwargs)

    def list_servers(self) -> list[dict[str, Any]]:
        """List all configured servers with status.

        Returns:
            List of server information
        """
        servers = []

        for name, config in self.config_manager.servers.items():
            running = name in self.server_manager.servers
            servers.append(
                {
                    "name": name,
                    "enabled": config.enabled,
                    "running": running,
                    "command": config.command,
                    "tools": (
                        len(self.server_manager.get_tools_for_server(name))
                        if running
                        else 0
                    ),
                }
            )

        return servers

    def list_tools(self) -> list[dict[str, str]]:
        """List all available tools.

        Returns:
            List of tool information
        """
        return self.server_manager.list_tools()

    def add_server(
        self,
        name: str,
        command: str,
        args: list[str] = None,
        env: dict[str, str] = None,
        enabled: bool = True,
    ):
        """Add a new MCP server configuration.

        Args:
            name: Server name
            command: Command to run
            args: Command arguments
            env: Environment variables
            enabled: Whether server is enabled
        """
        config = MCPServerConfig(
            command=command, args=args or [], env=env or {}, enabled=enabled
        )

        self.config_manager.add_server(name, config)
        logger.info(f"Added MCP server configuration: {name}")

    def save_config(self):
        """Save current configuration to mcp.json."""
        self.config_manager.save_config()

    def __enter__(self):
        """Context manager entry - start all servers."""
        self.start_all()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop all servers."""
        self.stop_all()


# Convenience functions
def load_mcp_tools(
    config_path: str | None = None,
    servers: list[str] | None = None,
    tools: list[str] | None = None,
) -> list[Callable]:
    """Quick function to load MCP tools.

    Args:
        config_path: Path to mcp.json
        servers: Specific servers to start
        tools: Specific tools to return

    Returns:
        List of tool functions

    Example:
        # Get all tools from filesystem server
        tools = load_mcp_tools(servers=["filesystem"])

        # Get specific tools
        tools = load_mcp_tools(tools=["read_file", "write_file"])
    """
    mcp = MCP(config_path)

    # Start servers
    if servers:
        for server in servers:
            mcp.start_server(server)
    else:
        mcp.start_all()

    # Get tools
    return mcp.get_tools(tools=tools, servers=servers)
