"""
MCP Server (Lightweight Python Implementation)
Provides a structured tool registry and dispatcher for the MCP tool layer.
This is a practical Python implementation — not a full MCP protocol server.
It acts as the capability boundary between analytics and the LLM layer.

Usage:
    server = MCPServer()
    result = server.call("analytics_context_tool", compared=compared, ...)
"""
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class MCPServer:
    """
    Lightweight MCP-style tool registry.
    Tools are registered by name and called with structured kwargs.
    """

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, dict] = {}
        self._register_default_tools()

    def register(self, name: str, fn: Callable, schema: Optional[dict] = None):
        """Register a tool function under a given name."""
        self._tools[name] = fn
        if schema:
            self._schemas[name] = schema
        logger.debug(f"MCP tool registered: {name}")

    def call(self, tool_name: str, **kwargs) -> Any:
        """
        Call a registered tool by name with keyword arguments.
        Returns the tool's output or raises MCPToolError.
        """
        if tool_name not in self._tools:
            raise MCPToolError(f"Unknown MCP tool: {tool_name}. Available: {list(self._tools.keys())}")
        try:
            result = self._tools[tool_name](**kwargs)
            logger.debug(f"MCP tool called: {tool_name}")
            return result
        except Exception as e:
            raise MCPToolError(f"MCP tool '{tool_name}' failed: {e}") from e

    def list_tools(self) -> list:
        """Returns list of registered tool names."""
        return list(self._tools.keys())

    def get_schema(self, tool_name: str) -> Optional[dict]:
        """Returns the schema for a tool if registered."""
        return self._schemas.get(tool_name)

    def _register_default_tools(self):
        """Register all planning intelligence tools on startup."""
        from mcp.tools import (
            analytics_context_tool,
            risk_summary_tool,
            root_cause_driver_tool,
            recommendation_tool,
            notification_tool,
            alert_trigger_tool,
        )
        self.register("analytics_context_tool", analytics_context_tool)
        self.register("risk_summary_tool", risk_summary_tool)
        self.register("root_cause_driver_tool", root_cause_driver_tool)
        self.register("recommendation_tool", recommendation_tool)
        self.register("notification_tool", notification_tool)
        self.register("alert_trigger_tool", alert_trigger_tool)


class MCPToolError(Exception):
    """Raised when an MCP tool call fails."""
    pass


# Singleton instance — import and use directly
_server_instance: Optional[MCPServer] = None


def get_server() -> MCPServer:
    """Returns the singleton MCP server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = MCPServer()
    return _server_instance
