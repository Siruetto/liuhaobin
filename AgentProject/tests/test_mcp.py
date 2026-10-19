"""MCP 服务端与客户端的测试。"""

import unittest

import mcp_server
from mcp_client import MCPToolBox


class McpServerHandleTest(unittest.TestCase):

    def test_initialize(self):
        response = mcp_server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual("2024-11-05", response["result"]["protocolVersion"])
        self.assertIn("tools", response["result"]["capabilities"])
        self.assertEqual("agent-tools", response["result"]["serverInfo"]["name"])

    def test_tools_list(self):
        response = mcp_server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = [tool["name"] for tool in response["result"]["tools"]]
        self.assertIn("calculator", names)
        self.assertIn("file_write", names)
        for tool in response["result"]["tools"]:
            self.assertIn("inputSchema", tool)

    def test_tools_call(self):
        response = mcp_server.handle(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "calculator", "arguments": {"expression": "2+3*4"}},
            }
        )
        self.assertFalse(response["result"]["isError"])
        self.assertEqual("14", response["result"]["content"][0]["text"])

    def test_unknown_tool_sets_error_flag(self):
        response = mcp_server.handle(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "nope", "arguments": {}},
            }
        )
        self.assertTrue(response["result"]["isError"])

    def test_notification_gets_no_response(self):
        self.assertIsNone(
            mcp_server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
        )

    def test_unknown_method_is_an_error(self):
        response = mcp_server.handle({"jsonrpc": "2.0", "id": 5, "method": "nope"})
        self.assertEqual(-32601, response["error"]["code"])


class McpClientTest(unittest.TestCase):

    def test_round_trip_in_subprocess(self):
        box = MCPToolBox()
        try:
            names = [tool["name"] for tool in box.list_tools()]
            self.assertIn("calculator", names)
            self.assertEqual("7", box.call("calculator", {"expression": "3+4"}))
            with self.assertRaises(Exception):
                box.call("no_such_tool", {})
        finally:
            box.close()
