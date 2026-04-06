#!/usr/bin/env python3
"""
HTTP-to-stdio MCP Bridge v3 - Simple User ID from Config
Allows Claude (stdio) to communicate with HTTP MCP server
Uses user_id from config for memory isolation
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict

import aiohttp
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

class HTTPMCPBridge:
    def __init__(self, http_server_url: str = "http://localhost:8000", user_id: str = None):
        self.http_url = http_server_url
        self.user_id = user_id or os.getenv("BRIDGE_USER_ID", "guest")
        self.server = Server("http-mcp-bridge-v3")
        self.session: aiohttp.ClientSession = None
        self._setup_handlers()
        
        logger.info(f"🎯 Bridge initialized for user: {self.user_id}")
        logger.info(f"🔗 Agent ID will be: user_{self.user_id}")

    def get_agent_id(self) -> str:
        """Generate agent_id based on configured user_id"""
        return f"user_{self.user_id}"

    async def start_session(self):
        """Start HTTP session"""
        self.session = aiohttp.ClientSession()

    async def stop_session(self):
        """Stop HTTP session"""
        if self.session:
            await self.session.close()

    async def send_jsonrpc(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send JSON-RPC request to HTTP server"""
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }
        
        logger.info(f"[{self.user_id}] Sending: {request_data}")
        
        try:
            async with self.session.post(
                self.http_url,
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                logger.info(f"[{self.user_id}] Received: {result}")
                return result
        except Exception as e:
            logger.error(f"[{self.user_id}] HTTP request failed: {e}")
            raise

    def _setup_handlers(self):
        """Setup MCP server handlers that forward to HTTP"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """Forward tools/list to HTTP server"""
            try:
                response = await self.send_jsonrpc("tools/list")
                if "result" in response and "tools" in response["result"]:
                    tools = []
                    for tool_data in response["result"]["tools"]:
                        tools.append(types.Tool(
                            name=tool_data["name"],
                            description=tool_data["description"],
                            inputSchema=tool_data["inputSchema"]
                        ))
                    return tools
                return []
            except Exception as e:
                logger.error(f"[{self.user_id}] Error listing tools: {e}")
                return []

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Forward tools/call to HTTP server with configured user agent_id"""
            try:
                # Always use configured user's agent_id
                agent_id = self.get_agent_id()
                arguments["agent_id"] = agent_id
                
                logger.info(f"[{self.user_id}] 🎯 Tool '{name}' using agent_id: {agent_id}")
                logger.info(f"[{self.user_id}] 📝 Arguments: {arguments}")
                
                response = await self.send_jsonrpc("tools/call", {
                    "name": name,
                    "arguments": arguments
                })
                
                if "result" in response and "content" in response["result"]:
                    content_list = []
                    for content_item in response["result"]["content"]:
                        content_list.append(types.TextContent(
                            type="text",
                            text=content_item["text"]
                        ))
                    return content_list
                else:
                    error_msg = response.get("error", {}).get("message", "Unknown error")
                    return [types.TextContent(type="text", text=f"Error: {error_msg}")]
                    
            except Exception as e:
                logger.error(f"[{self.user_id}] Error calling tool {name}: {e}")
                return [types.TextContent(type="text", text=f"Error calling tool {name}: {str(e)}")]

    async def run(self):
        """Run the bridge"""
        await self.start_session()
        
        try:
            logger.info(f"🚀 Starting HTTP Bridge v3 for user: {self.user_id}")
            logger.info(f"🔗 Connecting to: {self.http_url}")
            logger.info(f"🎯 Agent ID: {self.get_agent_id()}")
            
            # Test connection to HTTP server
            await self.send_jsonrpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": f"http-bridge-v3-{self.user_id}", "version": "3.0.0"}
            })
            logger.info(f"✅ [{self.user_id}] Successfully connected to HTTP server")
            
            # Run the stdio MCP server
            async with stdio_server() as (read_stream, write_stream):
                from mcp.server.lowlevel import NotificationOptions
                
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=f"http-mcp-bridge-v3-{self.user_id}",
                        server_version="3.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(
                                tools_changed=False,
                                prompts_changed=False,
                                resources_changed=False
                            ),
                            experimental_capabilities={},
                        ),
                    ),
                )
        finally:
            await self.stop_session()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="HTTP-to-stdio MCP Bridge v3")
    parser.add_argument("--http-url", default="http://localhost:8000", 
                       help="URL of the HTTP MCP server")
    parser.add_argument("--user-id", 
                       help="User ID for memory isolation")
    
    args = parser.parse_args()
    
    bridge = HTTPMCPBridge(args.http_url, args.user_id)
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())
