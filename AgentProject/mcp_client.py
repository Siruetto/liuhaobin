"""MCP 客户端: 把 ``mcp_server.py`` 当作子进程, 通过 stdio 调用工具。

对上层来说它和 ``tools.LocalToolBox`` 一样, 都有 ``schemas()`` 和 ``call()``,
所以规划器不需要知道工具到底是在本进程里跑的, 还是在 MCP 服务里跑的。
"""

import json
import os
import subprocess
import sys

from config import PROJECT_ROOT
from tools import ToolError

SERVER_SCRIPT = os.path.join(PROJECT_ROOT, "mcp_server.py")


class MCPToolBox:
    """通过 MCP 协议调用工具。"""

    def __init__(self, command=None):
        self.process = subprocess.Popen(
            command or [sys.executable, SERVER_SCRIPT],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._next_id = 0
        self._tools = None
        self.initialize()

    # ------------------------------------------------------------ 协议
    def _send(self, payload):
        line = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        try:
            self.process.stdin.write(line)
            self.process.stdin.flush()
        except (OSError, ValueError):
            raise ToolError("MCP 服务进程已经退出")

    def _request(self, method, params=None):
        self._next_id += 1
        payload = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)
        response_line = self.process.stdout.readline()
        if not response_line:
            stderr = b""
            try:
                stderr = self.process.stderr.read(500)
            except OSError:
                pass
            raise ToolError(
                "MCP 服务没有响应: {}".format(stderr.decode("utf-8", "replace").strip())
            )
        response = json.loads(response_line.decode("utf-8"))
        if "error" in response:
            raise ToolError(str(response["error"].get("message", "MCP 调用失败")))
        return response.get("result") or {}

    def _notify(self, method, params=None):
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    def initialize(self):
        """握手, 并发送 initialized 通知。"""
        self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "office-agent", "version": "1.0.0"},
            },
        )
        self._notify("notifications/initialized")

    # ------------------------------------------------------------ 工具接口
    def list_tools(self):
        if self._tools is None:
            self._tools = self._request("tools/list").get("tools", [])
        return self._tools

    def schemas(self):
        """转成大模型 function calling 需要的格式。"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema") or {"type": "object", "properties": {}},
                },
            }
            for tool in self.list_tools()
        ]

    def call(self, name, arguments=None):
        result = self._request("tools/call", {"name": name, "arguments": arguments or {}})
        texts = [
            item.get("text", "")
            for item in result.get("content", [])
            if item.get("type") == "text"
        ]
        text = "\n".join(texts).strip()
        if result.get("isError"):
            raise ToolError(text or "工具执行失败")
        return text

    def close(self):
        try:
            self.process.stdin.close()
        except OSError:
            pass
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
