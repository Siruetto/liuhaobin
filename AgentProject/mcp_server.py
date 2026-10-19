"""MCP 工具服务: 用 stdio 上的 JSON-RPC 把 tools.py 暴露出去。

实现的是 MCP(2024-11-05) 里最核心的三个方法:

* ``initialize``   —— 握手, 告诉客户端支持 tools;
* ``tools/list``   —— 列出所有工具及其 inputSchema;
* ``tools/call``   —— 调用一个工具, 返回 text 内容。

传输格式按 MCP 的 stdio 约定: 一行一条 JSON-RPC 消息, UTF-8 编码。
可以直接用任何 MCP 客户端接进来, 也可以被 ``mcp_client.py`` 调用。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools import TOOLS_BY_NAME, ToolError, mcp_tool_schemas  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "agent-tools", "version": "1.0.0"}


def handle(request):
    """处理一条 JSON-RPC 请求, 返回响应字典(通知则返回 None)。"""
    if not isinstance(request, dict):
        return _error(None, -32600, "Invalid Request")

    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params") or {}

    if request_id is None:
        # 通知(notifications/initialized 等)不需要回复
        return None

    if method == "initialize":
        return _result(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        )
    if method == "tools/list":
        return _result(request_id, {"tools": mcp_tool_schemas()})
    if method == "tools/call":
        return _call_tool(request_id, params)
    if method == "ping":
        return _result(request_id, {})
    return _error(request_id, -32601, "Method not found: {}".format(method))


def _call_tool(request_id, params):
    name = params.get("name")
    arguments = params.get("arguments") or {}
    tool = TOOLS_BY_NAME.get(name)
    if tool is None:
        return _result(
            request_id,
            {"content": [{"type": "text", "text": "未知工具: {}".format(name)}], "isError": True},
        )
    try:
        text = tool["handler"](**arguments)
        return _result(request_id, {"content": [{"type": "text", "text": text}], "isError": False})
    except ToolError as error:
        return _result(
            request_id,
            {"content": [{"type": "text", "text": str(error)}], "isError": True},
        )
    except TypeError as error:
        return _result(
            request_id,
            {"content": [{"type": "text", "text": "参数不对: {}".format(error)}], "isError": True},
        )


def _result(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def main():
    """从 stdin 逐行读请求, 往 stdout 逐行写响应。"""
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            response = _error(None, -32700, "Parse error")
        else:
            response = handle(request)
        if response is not None:
            sys.stdout.buffer.write(
                (json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8")
            )
            sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
