"""Tests for MCP configuration management."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from konseho.mcp import MCP
from konseho.mcp.config import MCPConfigManager
from konseho.mcp.server import MCPServerManager, MCPToolSelector


class TestMCPConfigManager:
    """Test MCP configuration management."""

    def test_load_config_from_file(self):
        """Test loading configuration from mcp.json file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp.json"
            config_data = {
                "mcpServers": {
                    "filesystem": {
                        "command": "npx",
                        "args": [
                            "-y",
                            "@modelcontextprotocol/server-filesystem",
                            "/tmp",
                        ],
                    },
                    "github": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-github"],
                        "env": {"GITHUB_TOKEN": "test-token"},
                    },
                }
            }

            with open(config_path, "w") as f:
                json.dump(config_data, f)

            manager = MCPConfigManager(config_path)

            assert "filesystem" in manager.servers
            assert "github" in manager.servers
            assert manager.servers["filesystem"].command == "npx"
            assert manager.servers["github"].env["GITHUB_TOKEN"] == "test-token"

    def test_empty_config(self):
        """Test handling empty configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp.json"
            with open(config_path, "w") as f:
                json.dump({}, f)

            manager = MCPConfigManager(config_path)
            assert manager.servers == {}

    def test_missing_config_file(self):
        """Test handling missing configuration file."""
        manager = MCPConfigManager("/nonexistent/path/mcp.json")
        assert manager.servers == {}

    def test_invalid_json(self):
        """Test handling invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp.json"
            with open(config_path, "w") as f:
                f.write("invalid json{")

            manager = MCPConfigManager(config_path)
            assert manager.servers == {}

    def test_get_server_config(self):
        """Test getting specific server configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp.json"
            config_data = {
                "mcpServers": {
                    "test-server": {"command": "test-cmd", "args": ["arg1", "arg2"]}
                }
            }

            with open(config_path, "w") as f:
                json.dump(config_data, f)

            manager = MCPConfigManager(config_path)
            config = manager.get_server("test-server")

            assert config.command == "test-cmd"
            assert config.args == ["arg1", "arg2"]

            # Test missing server
            assert manager.get_server("nonexistent") is None


class TestMCPServerManager:
    """Test MCP server lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_server(self):
        """Test starting an MCP server."""
        config_manager = Mock()
        mock_server_config = Mock()
        mock_server_config.command = "test-cmd"
        mock_server_config.args = ["arg1"]
        mock_server_config.env = {"TEST": "value"}
        config_manager.get_server.return_value = mock_server_config

        manager = MCPServerManager(config_manager)

        # Mock subprocess.Popen for server process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running

        with patch("subprocess.Popen", return_value=mock_process):
            success = await manager.start_server("test-server")

            assert success
            assert "test-server" in manager.servers
            assert manager.servers["test-server"].process == mock_process
            # Should have mock tools based on server name
            assert len(manager.servers["test-server"].tools) > 0

    @pytest.mark.asyncio
    async def test_start_nonexistent_server(self):
        """Test starting a server that doesn't exist in config."""
        config_manager = Mock()
        config_manager.get_server.return_value = None

        manager = MCPServerManager(config_manager)
        success = await manager.start_server("nonexistent")

        assert not success
        assert "nonexistent" not in manager.servers

    @pytest.mark.asyncio
    async def test_stop_server(self):
        """Test stopping an MCP server."""
        config_manager = Mock()
        manager = MCPServerManager(config_manager)

        # Add a mock server instance
        mock_process = Mock()
        mock_instance = Mock()
        mock_instance.process = mock_process
        mock_instance.tools = {"tool1": lambda: "test"}
        manager.servers["test-server"] = mock_instance
        manager._tool_registry["tool1"] = "test-server"

        success = await manager.stop_server("test-server")

        assert success
        mock_process.terminate.assert_called_once()
        assert "test-server" not in manager.servers
        assert "tool1" not in manager._tool_registry

    @pytest.mark.asyncio
    async def test_get_tools(self):
        """Test getting tools from a server."""
        config_manager = Mock()
        manager = MCPServerManager(config_manager)

        # Mock server instances
        instance1 = Mock()
        instance1.tools = {"tool1": lambda: "1", "tool2": lambda: "2"}
        manager.servers["server1"] = instance1

        instance2 = Mock()
        instance2.tools = {"tool3": lambda: "3"}
        manager.servers["server2"] = instance2

        # Get all tools
        all_tools = manager.get_all_tools()
        assert len(all_tools) == 3

        # Get tools from specific server
        server1_tools = manager.get_tools_for_server("server1")
        assert len(server1_tools) == 2

        # Get nonexistent server
        none_tools = manager.get_tools_for_server("nonexistent")
        assert len(none_tools) == 0


class TestMCPToolSelector:
    """Test MCP tool selection functionality."""

    def test_select_by_name(self):
        """Test selecting tools by name."""
        server_manager = Mock()

        # Mock tools
        mock_tools = {
            "file_read": lambda: "read",
            "file_write": lambda: "write",
            "web_search": lambda: "search",
        }
        server_manager.get_all_tools.return_value = mock_tools
        server_manager._tool_registry = {
            "file_read": "filesystem",
            "file_write": "filesystem",
            "web_search": "search-server",
        }

        selector = MCPToolSelector(server_manager)

        # Select specific tools
        tools = selector.select_tools(tool_names=["file_read", "web_search"])
        assert len(tools) == 2
        assert all(callable(tool) for tool in tools)

    def test_select_by_server(self):
        """Test selecting tools by server."""
        server_manager = Mock()

        # Mock tools with server mappings
        mock_tools = {
            "file_read": lambda: "read",
            "file_write": lambda: "write",
            "create_issue": lambda: "issue",
        }
        server_manager.get_all_tools.return_value = mock_tools
        server_manager._tool_registry = {
            "file_read": "filesystem",
            "file_write": "filesystem",
            "create_issue": "github",
        }

        selector = MCPToolSelector(server_manager)

        # Select from specific servers
        tools = selector.select_tools(servers=["filesystem"])
        assert len(tools) == 2

    def test_exclude_tools(self):
        """Test excluding specific tools."""
        server_manager = Mock()

        # Mock tools
        mock_tools = {
            "file_read": lambda: "read",
            "file_write": lambda: "write",
            "file_delete": lambda: "delete",
        }
        server_manager.get_all_tools.return_value = mock_tools
        server_manager._tool_registry = {
            "file_read": "filesystem",
            "file_write": "filesystem",
            "file_delete": "filesystem",
        }

        selector = MCPToolSelector(server_manager)

        # Exclude dangerous tools
        tools = selector.select_tools(exclude_tools=["file_delete"])
        assert len(tools) == 2
        tool_funcs = list(mock_tools.values())
        assert mock_tools["file_delete"] not in tools

    def test_create_preset(self):
        """Test creating and using tool presets."""
        server_manager = Mock()

        # Mock tools
        mock_tools = {
            "file_read": lambda: "read",
            "file_write": lambda: "write",
            "code_edit": lambda: "edit",
            "web_search": lambda: "search",
        }
        server_manager.get_all_tools.return_value = mock_tools
        server_manager._tool_registry = {
            "file_read": "filesystem",
            "file_write": "filesystem",
            "code_edit": "code-server",
            "web_search": "search-server",
        }

        selector = MCPToolSelector(server_manager)

        # Create coder preset
        coder_preset = selector.create_tool_preset(
            "coder", tool_names=["file_read", "file_write", "code_edit"]
        )

        # Use preset
        tools = coder_preset.get_tools()
        assert len(tools) == 3


class TestMCPHighLevel:
    """Test high-level MCP interface."""

    @pytest.mark.asyncio
    async def test_mcp_get_tools(self):
        """Test getting tools through MCP interface."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp.json"
            config_data = {
                "mcpServers": {"test-server": {"command": "test-cmd", "args": []}}
            }

            with open(config_path, "w") as f:
                json.dump(config_data, f)

            mcp = MCP(config_path)

            # Mock server manager
            mock_get_tools = AsyncMock()
            mock_get_tools.return_value = [
                {"name": "test_tool", "description": "Test tool"}
            ]
            mcp.server_manager.get_tools = mock_get_tools

            # Mock tool selector
            mock_select = AsyncMock()
            mock_select.return_value = [lambda: "test"]
            mcp.tool_selector.select_tools = mock_select

            # Get tools
            tools = await mcp.get_tools(tools=["test_tool"])

            assert len(tools) == 1
            assert callable(tools[0])

    def test_mcp_start_servers(self):
        """Test starting servers through MCP interface."""
        mcp = MCP()

        # Mock the event loop and server manager directly
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(return_value=True)
        mcp._loop = mock_loop

        # Start servers individually since start_servers doesn't exist
        result1 = mcp.start_server("server1")
        result2 = mcp.start_server("server2")

        assert result1 is True
        assert result2 is True
        assert mock_loop.run_until_complete.call_count == 2

    @pytest.mark.asyncio
    async def test_mcp_with_filters(self):
        """Test using MCP with various filters."""
        mcp = MCP()

        # Mock tool selector
        mock_select = Mock()
        mock_select.return_value = [lambda: "file_tool", lambda: "code_tool"]
        mcp.tool_selector.select_tools = mock_select

        # Get tools with multiple filters
        tools = await mcp.get_tools(
            tools=["file_read", "file_write"], servers=["filesystem"]
        )

        mock_select.assert_called_once_with(
            tool_names=["file_read", "file_write"],
            servers=["filesystem"],
            tags=None,
            preset=None,
        )
        assert len(tools) == 2
