"""MCP integration using Strands SDK's built-in MCP support."""
from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from mcp import MCPClient as MCPClientType
else:
    MCPClientType = object
try:
    from mcp import StdioServerParameters, stdio_client
    from strands.tools.mcp import MCPClient  # type: ignore[import-not-found]
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MCPClient = None  # type: ignore[assignment,misc]
from konseho.mcp.config import MCPConfigManager
logger = logging.getLogger(__name__)


class StrandsMCPManager:
    """Manage MCP servers using Strands' built-in MCP support."""

    def __init__(self, config_path: (str | None)=None):
        """Initialize MCP manager.

        Args:
            config_path: Path to mcp.json file. If None, auto-discovers.
        """
        if not MCP_AVAILABLE:
            logger.warning(
                "MCP support not available. Install 'mcp' package to enable MCP tools."
                )
            self.clients: dict[str, object] = {}
            self.config_manager: MCPConfigManager | None = None
            return
        self.config_manager = MCPConfigManager(config_path)
        self.clients = {}

    def connect_server(self, server_name: str) -> object | None:
        """Connect to an MCP server.

        Args:
            server_name: Name of the server from mcp.json

        Returns:
            MCPClient instance if successful, None otherwise
        """
        if not MCP_AVAILABLE:
            return None
        if server_name in self.clients:
            return self.clients[server_name]
        if self.config_manager:
            server_config = self.config_manager.get_server(server_name)
        else:
            server_config = None
        if not server_config or not self.config_manager:
            logger.error(f'No configuration found for server: {server_name}')
            return None
        try:
            env = os.environ.copy()
            for key, value in server_config.env.items():
                if value.startswith('${') and value.endswith('}'):
                    var_name = value[2:-1]
                    env[key] = os.environ.get(var_name, '')
                else:
                    env[key] = value
            server_params = StdioServerParameters(command=server_config.
                command, args=server_config.args, env=env)
            client = MCPClient(lambda : stdio_client(server_params))
            client.__enter__()
            self.clients[server_name] = client
            logger.info(f'Connected to MCP server: {server_name}')
            return client
        except Exception as e:
            logger.error(f'Failed to connect to MCP server {server_name}: {e}')
            return None

    def get_tools(self, server_name: str) -> list[object]:
        """Get tools from a specific MCP server.

        Args:
            server_name: Name of the server

        Returns:
            List of tools from the server
        """
        if not MCP_AVAILABLE:
            return []
        client = self.connect_server(server_name)
        if not client:
            return []
        try:
            tools = client.list_tools_sync()  # type: ignore[attr-defined]
            logger.info(f'Retrieved {len(tools)} tools from {server_name}')
            return list(tools) if hasattr(tools, '__iter__') else []
        except Exception as e:
            logger.error(f'Failed to get tools from {server_name}: {e}')
            return []

    def get_search_tool(self, server_name: str | None = None) -> object | None:
        """Get a search tool from MCP servers.

        Args:
            server_name: Specific server to get tool from. If None, searches all.

        Returns:
            Search tool function if found
        """
        if not MCP_AVAILABLE:
            return None
        if server_name:
            tools = self.get_tools(server_name)
            logger.info(
                f'Looking for search tool in {len(tools)} tools from {server_name}'
                )
            for tool in tools:
                tool_name = getattr(tool, '__name__', str(tool))
                logger.info(f'Checking tool: {tool_name}')
                if hasattr(tool, '__name__'):
                    if 'search' in tool.__name__.lower(
                        ) or 'brave' in tool.__name__.lower():
                        logger.info(
                            f'Found search tool by name: {tool.__name__}')
                        return tool  # type: ignore[return-value]
                if callable(tool):
                    doc = getattr(tool, '__doc__', '')
                    if doc and 'search' in doc.lower():
                        logger.info('Found search tool by docstring')
                        return tool  # type: ignore[return-value]
                if server_name == 'brave-search' and tools.index(tool) == 0:
                    logger.info(
                        'Using first tool from brave-search as search tool')
                    return tool  # type: ignore[return-value]
            return None
        search_servers = ['brave-search', 'tavily', 'serper', 'web-search']
        if not self.config_manager:
            return None
        servers = self.config_manager.list_servers()
        for server in servers:
            if any(search in server.lower() for search in search_servers):
                tools = self.get_tools(server)
                for tool in tools:
                    if hasattr(tool, '__name__'
                        ) and 'search' in tool.__name__.lower():
                        logger.info(
                            f'Found search tool in {server}: {tool.__name__}')
                        return tool  # type: ignore[return-value]
        return None

    def disconnect_all(self) -> None:
        """Disconnect all MCP clients."""
        for server_name, client in self.clients.items():
            try:
                client.__exit__(None, None, None)  # type: ignore[attr-defined]
                logger.info(f'Disconnected from MCP server: {server_name}')
            except Exception as e:
                logger.error(f'Error disconnecting from {server_name}: {e}')
        self.clients.clear()

    def __enter__(self) -> 'StrandsMCPManager':
        """Context manager support."""
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> None:
        """Cleanup on exit."""
        self.disconnect_all()


def get_mcp_search_provider() -> object | None:
    """Get a search provider from available MCP servers.

    This is a convenience function that:
    1. Connects to MCP servers configured in mcp.json
    2. Finds a search tool (brave-search, tavily, etc.)
    3. Returns it wrapped as a search provider

    Returns:
        SearchProvider if found, None otherwise
    """
    if not MCP_AVAILABLE:
        logger.warning('MCP not available - using mock provider')
        return None
    from konseho.tools.mcp_search_adapter import MCPSearchProvider
    try:
        manager = StrandsMCPManager()
        if search_tool := manager.get_search_tool():
            tool_name = getattr(search_tool, '__name__', 'search').lower()
            if 'brave' in tool_name:
                provider_name = 'brave-search'
            elif 'tavily' in tool_name:
                provider_name = 'tavily'
            else:
                provider_name = 'mcp-search'
            return MCPSearchProvider(search_tool, provider_name)  # type: ignore[arg-type]
    except Exception as e:
        logger.error(f'Failed to get MCP search provider: {e}')
    return None
