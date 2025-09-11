#!/usr/bin/env python
"""
MCP Server implementation for the Wolf, Goat, Cabbage puzzle.

This server provides Model Context Protocol (MCP) tools that allow AI agents
to interact with the puzzle environment through standardized MCP interfaces.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Literal

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
)
from puzzle_environment import PuzzleEnvironment


class PuzzleMCPServer:
    """
    MCP Server that provides puzzle-solving tools through the Model Context Protocol.
    
    This server wraps the PuzzleEnvironment class and exposes its functionality
    as MCP tools that can be used by AI agents.
    """
    
    def __init__(self):
        self.puzzle_env = PuzzleEnvironment()
        self._tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register all available MCP tools with their schemas."""
        return {
            "get_current_state": {
                "description": "Získá aktuální stav hádanky – kdo je na kterém břehu a kde je loďka.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "move_across_river": {
                "description": "Pokusí se převézt pasažéra na druhý břeh.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "passenger": {
                            "type": "string",
                            "enum": ["wolf", "goat", "cabbage", "nothing"],
                            "description": "Koho převézt. Možnosti jsou 'wolf', 'goat', 'cabbage' nebo 'nothing' (převozník jede sám)."
                        }
                    },
                    "required": ["passenger"]
                }
            },
            "check_if_solved": {
                "description": "Zkontroluje, zda byla hádanka úspěšně vyřešena.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "reset_puzzle": {
                "description": "Resetuje hádanku do počátečního stavu.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools in MCP format."""
        tools = []
        for name, config in self._tools.items():
            tools.append({
                "name": name,
                "description": config["description"],
                "inputSchema": config["inputSchema"]
            })
        return tools
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call and return the result in MCP format.
        
        Args:
            name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Dict containing the tool result in MCP format
        """
        if name not in self._tools:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Unknown tool '{name}'"
                    }
                ],
                "isError": True
            }
        
        try:
            if name == "get_current_state":
                result = self._get_current_state()
            elif name == "move_across_river":
                result = self._move_across_river(arguments.get("passenger"))
            elif name == "check_if_solved":
                result = self._check_if_solved()
            elif name == "reset_puzzle":
                result = self._reset_puzzle()
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: Tool '{name}' not implemented"
                        }
                    ],
                    "isError": True
                }
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": result
                    }
                ]
            }
            
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error executing tool '{name}': {str(e)}"
                    }
                ],
                "isError": True
            }
    
    def _get_current_state(self) -> str:
        """Get the current state of the puzzle."""
        print("--- MCP nástroj 'get_current_state' byl zavolán. ---")
        return self.puzzle_env.get_state_description()
    
    def _move_across_river(self, passenger: str) -> str:
        """Move a passenger across the river."""
        if not passenger:
            raise ValueError("Parameter 'passenger' is required")
        
        print(f"--- MCP nástroj 'move_across_river' byl zavolán s pasažérem: '{passenger}' ---")
        
        passenger = passenger.lower()
        if passenger not in ["wolf", "goat", "cabbage", "nothing"]:
            raise ValueError(f"Invalid passenger '{passenger}'. Must be one of: wolf, goat, cabbage, nothing")
        
        success, message = self.puzzle_env.attempt_move(passenger)
        
        if success:
            response = {
                "status": "úspěch",
                "popis": message,
                "novy_stav": self.puzzle_env.get_state_description(),
            }
        else:
            response = {"status": "chyba", "duvod": message}
        
        return json.dumps(response, ensure_ascii=False)
    
    def _check_if_solved(self) -> str:
        """Check if the puzzle is solved."""
        print("--- MCP nástroj 'check_if_solved' byl zavolán. ---")
        
        if self.puzzle_env.is_solved():
            return "Potvrzeno. Hádanka je skutečně vyřešena. Nyní můžeš napsat finální zprávu."
        else:
            current_state = self.puzzle_env.get_state_description()
            return f"Negativní. Hádanka ještě není vyřešena. Pokračuj v práci. Aktuální stav je:\n{current_state}"
    
    def _reset_puzzle(self) -> str:
        """Reset the puzzle to initial state."""
        print("--- MCP nástroj 'reset_puzzle' byl zavolán. ---")
        self.puzzle_env = PuzzleEnvironment()
        return f"Hádanka byla resetována do počátečního stavu:\n{self.puzzle_env.get_state_description()}"


def create_mcp_server() -> PuzzleMCPServer:
    """Factory function to create a new MCP server instance."""
    return PuzzleMCPServer()


def setup_mcp_server():
    """Setup and configure the MCP server with handlers."""
    # Global puzzle server instance
    puzzle_server = None

    # Create MCP server instance
    mcp_server = Server("puzzle-solver")

    @mcp_server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """List available tools."""
        nonlocal puzzle_server
        if puzzle_server is None:
            puzzle_server = create_mcp_server()
        
        tools = puzzle_server.get_tools()
        mcp_tools = []
        
        for tool in tools:
            mcp_tools.append(
                Tool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["inputSchema"]
                )
            )
        
        return mcp_tools

    @mcp_server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls."""
        nonlocal puzzle_server
        if puzzle_server is None:
            puzzle_server = create_mcp_server()
        
        result = puzzle_server.call_tool(name, arguments)
        
        # Convert result to MCP format
        if result.get("isError", False):
            # For errors, we'll still return as TextContent but the client can handle appropriately
            return [TextContent(type="text", text=result["content"][0]["text"])]
        else:
            return [TextContent(type="text", text=result["content"][0]["text"])]
    
    return mcp_server

async def main():
    """Run the MCP server."""
    # Setup the MCP server only when running as main
    mcp_server = setup_mcp_server()
    
    # Log server startup to stderr so it doesn't interfere with MCP protocol
    print("Wolf, Goat, Cabbage MCP Server starting...", file=sys.stderr)
    print("Available tools: get_current_state, move_across_river, check_if_solved, reset_puzzle", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="puzzle-solver",
                server_version="1.0.0",
                capabilities=mcp_server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())