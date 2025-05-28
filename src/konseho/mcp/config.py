"""MCP configuration management compatible with mcp.json format."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""

    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPServerConfig":
        """Create from dictionary configuration."""
        return cls(
            command=data.get("command", ""),
            args=data.get("args", []),
            env=data.get("env", {}),
            enabled=data.get("enabled", True),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "enabled": self.enabled,
        }


class MCPConfigManager:
    """Manage MCP server configurations compatible with mcp.json format."""

    def __init__(self, config_path: str | Path | None = None):
        """Initialize MCP configuration manager.

        Args:
            config_path: Path to mcp.json file. If None, searches standard locations.
        """
        self.config_path = self._find_config_path(config_path)
        self.servers: dict[str, MCPServerConfig] = {}
        self._load_config()

    def _find_config_path(self, config_path: str | Path | None = None) -> Path:
        """Find the MCP configuration file.

        Searches in order:
        1. Provided path
        2. Current directory
        3. Project root
        4. User config directory
        """
        if config_path:
            return Path(config_path)

        # Search locations (compatible with Cline/Claude Code)
        search_paths = [
            Path.cwd() / "mcp.json",
            Path.cwd() / ".mcp" / "mcp.json",
            Path.cwd() / "config" / "mcp.json",
            Path.home() / ".config" / "konseho" / "mcp.json",
            Path.home() / ".mcp" / "mcp.json",
        ]

        for path in search_paths:
            if path.exists():
                logger.info(f"Found MCP config at: {path}")
                return path

        # Default to project root
        default_path = Path.cwd() / "mcp.json"
        logger.info(f"No MCP config found, using default: {default_path}")
        return default_path

    def _load_config(self):
        """Load configuration from mcp.json file."""
        if not self.config_path.exists():
            logger.debug(f"No config file at {self.config_path}")
            return

        try:
            with open(self.config_path) as f:
                data = json.load(f)

            # Handle both formats:
            # Format 1: {"servers": {"name": {...}}}
            # Format 2: {"mcpServers": {"name": {...}}}
            servers_data = data.get("servers", data.get("mcpServers", {}))

            for name, config in servers_data.items():
                self.servers[name] = MCPServerConfig.from_dict(config)

            logger.info(f"Loaded {len(self.servers)} MCP servers from config")

        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")

    def save_config(self):
        """Save current configuration to mcp.json file."""
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Build config data
        data = {
            "mcpServers": {
                name: server.to_dict() for name, server in self.servers.items()
            }
        }

        # Write config
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved MCP config to {self.config_path}")

    def add_server(self, name: str, config: MCPServerConfig):
        """Add or update an MCP server configuration."""
        self.servers[name] = config
        logger.info(f"Added MCP server: {name}")

    def remove_server(self, name: str) -> bool:
        """Remove an MCP server configuration."""
        if name in self.servers:
            del self.servers[name]
            logger.info(f"Removed MCP server: {name}")
            return True
        return False

    def get_server(self, name: str) -> MCPServerConfig | None:
        """Get configuration for a specific server."""
        return self.servers.get(name)

    def list_servers(self) -> list[str]:
        """List all configured server names."""
        return list(self.servers.keys())

    def get_enabled_servers(self) -> dict[str, MCPServerConfig]:
        """Get all enabled server configurations."""
        return {name: config for name, config in self.servers.items() if config.enabled}


# Example mcp.json format:
"""
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"],
      "enabled": true
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      },
      "enabled": true
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      },
      "enabled": false
    }
  }
}
"""
