"""工具集: 智能体真正"会做"的部分。

每个工具都有名字、说明和 JSON Schema:

* 在大模型模式下, 它们直接作为 function calling 的工具定义;
* 在 MCP 模式下, ``mcp_server.py`` 用 ``tools/list`` 和 ``tools/call`` 把它们暴露出去。

工具统一返回给人看的字符串; 失败时抛 ``ToolError``, 由上层决定怎么展示。
"""

import ast
import json
import operator
import os
import urllib.parse
import urllib.request
from datetime import datetime

from config import TODO_FILE, WORKSPACE_DIR

MAX_EXPRESSION_LENGTH = 200
MAX_EXPONENT = 100
MAX_FILE_BYTES = 200_000

# 天气代码 -> 中文描述(Open-Meteo 的 WMO 天气代码)
WEATHER_CODES = {
    0: "晴",
    1: "多云", 2: "多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "强冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "小阵雨", 81: "阵雨", 82: "强阵雨",
    85: "小阵雪", 86: "强阵雪",
    95: "雷雨", 96: "雷雨伴冰雹", 99: "强雷雨伴冰雹",
}


class ToolError(Exception):
    """工具执行失败。消息会原样回给模型或用户。"""


# ---------------------------------------------------------------- 计算器

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def calculate(expression):
    """安全地算一个四则运算表达式。

    用 ``ast`` 解析后只允许数字和四则运算符, 不调用 ``eval``,
    所以 ``__import__("os").system(...)`` 这种输入进不来。
    """
    text = (expression or "").strip()
    if not text:
        raise ToolError("表达式不能为空")
    if len(text) > MAX_EXPRESSION_LENGTH:
        raise ToolError("表达式太长, 请控制在 {} 个字符以内".format(MAX_EXPRESSION_LENGTH))
    try:
        tree = ast.parse(text, mode="eval").body
    except SyntaxError:
        raise ToolError("表达式语法错误: {}".format(text))
    value = _eval_node(tree)
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value)


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ToolError("表达式里只能出现数字")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
            raise ToolError("指数太大了, 请控制在 {} 以内".format(MAX_EXPONENT))
        try:
            return _BINARY_OPS[type(node.op)](left, right)
        except ZeroDivisionError:
            raise ToolError("除数不能为 0")
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    raise ToolError("只支持数字和 + - * / // % ** 运算")


# ---------------------------------------------------------------- 待办清单

def _load_todos():
    if not os.path.exists(TODO_FILE):
        return []
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _save_todos(items):
    os.makedirs(os.path.dirname(TODO_FILE), exist_ok=True)
    with open(TODO_FILE, "w", encoding="utf-8") as handle:
        json.dump(items, handle, ensure_ascii=False, indent=2)


def todo_add(text):
    """把一件事加进待办清单。"""
    content = (text or "").strip()
    if not content:
        raise ToolError("待办内容不能为空")
    items = _load_todos()
    items.append({"text": content, "done": False})
    _save_todos(items)
    return "已记下第 {} 条待办: {}".format(len(items), content)


def todo_list():
    """列出待办清单。"""
    items = _load_todos()
    if not items:
        return "待办清单是空的。"
    lines = ["待办清单:"]
    for index, item in enumerate(items, start=1):
        mark = "x" if item.get("done") else " "
        lines.append("{}. [{}] {}".format(index, mark, item.get("text", "")))
    return "\n".join(lines)


def todo_done(index):
    """把第 index 条待办标记为完成(序号从 1 开始)。"""
    items = _load_todos()
    try:
        position = int(index)
    except (TypeError, ValueError):
        raise ToolError("序号必须是数字")
    if not 1 <= position <= len(items):
        raise ToolError("没有第 {} 条待办".format(position))
    items[position - 1]["done"] = True
    _save_todos(items)
    return "已完成第 {} 条: {}".format(position, items[position - 1].get("text", ""))


# ---------------------------------------------------------------- 文件

def _resolve_in_workspace(path):
    """把相对路径解析到 workspace 里, 并挡住 ../ 和绝对路径。"""
    relative = (path or "").strip()
    if not relative:
        raise ToolError("文件路径不能为空")
    if os.path.isabs(relative):
        raise ToolError("请用相对路径, 文件只能放在 workspace/ 里")
    root = os.path.realpath(WORKSPACE_DIR)
    target = os.path.realpath(os.path.join(root, relative))
    try:
        inside = os.path.commonpath([root, target]) == root
    except ValueError:  # Windows 上跨盘符
        inside = False
    if not inside:
        raise ToolError("只能操作 workspace/ 目录里的文件")
    return target


def file_write(path, content=""):
    """在 workspace/ 里写一个文本文件(不存在就创建)。"""
    target = _resolve_in_workspace(path)
    text = content if content is not None else ""
    size = len(text.encode("utf-8"))
    if size > MAX_FILE_BYTES:
        raise ToolError("内容太长(超过 {} 字节)".format(MAX_FILE_BYTES))
    parent = os.path.dirname(target)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(text)
    return "已写入 {} ({} 字节)".format(path, size)


def file_read(path):
    """读 workspace/ 里的一个文本文件。"""
    target = _resolve_in_workspace(path)
    if not os.path.isfile(target):
        raise ToolError("文件不存在: {}".format(path))
    with open(target, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read(MAX_FILE_BYTES)


def file_list():
    """列出 workspace/ 里的所有文件。"""
    root = os.path.realpath(WORKSPACE_DIR)
    found = []
    for base, _dirs, names in os.walk(root):
        for name in names:
            full = os.path.join(base, name)
            found.append(os.path.relpath(full, root).replace(os.sep, "/"))
    if not found:
        return "workspace/ 里还没有文件。"
    return "\n".join(sorted(found))


# ---------------------------------------------------------------- 天气

def _http_get_json(url, timeout=8):
    request = urllib.request.Request(url, headers={"User-Agent": "teaching-agent/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_weather(city):
    """查询某个城市当前的天气(Open-Meteo, 不需要 API Key)。"""
    name = (city or "").strip()
    if not name:
        raise ToolError("请告诉我城市名")
    try:
        geo = _http_get_json(
            "https://geocoding-api.open-meteo.com/v1/search?"
            + urllib.parse.urlencode({"name": name, "count": 1, "language": "zh", "format": "json"})
        )
    except OSError as exc:
        raise ToolError("查询天气失败(网络不可用): {}".format(exc))
    results = geo.get("results") or []
    if not results:
        raise ToolError("找不到这个城市: {}".format(name))
    place = results[0]
    try:
        data = _http_get_json(
            "https://api.open-meteo.com/v1/forecast?"
            + urllib.parse.urlencode({
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current_weather": "true",
            })
        )
    except OSError as exc:
        raise ToolError("查询天气失败(网络不可用): {}".format(exc))
    current = data.get("current_weather") or {}
    if "temperature" not in current:
        raise ToolError("天气服务返回的数据看不懂")
    code = int(current.get("weathercode", -1))
    description = WEATHER_CODES.get(code, "天气代码 {}".format(code))
    return "{} 现在 {:.1f}°C, {}, 风速 {:.1f} km/h".format(
        place.get("name", name),
        float(current["temperature"]),
        description,
        float(current.get("windspeed", 0.0)),
    )


def current_time():
    """返回当前的日期时间。"""
    now = datetime.now()
    weekday = "一二三四五六日"[now.weekday()]
    return "{} (星期{})".format(now.strftime("%Y-%m-%d %H:%M:%S"), weekday)


# ---------------------------------------------------------------- 注册表

TOOLS = [
    {
        "name": "calculator",
        "description": "计算数学表达式, 支持 + - * / // % ** 和括号。用户问算术结果时用它。",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "要计算的表达式, 例如 (3+5)*2"}
            },
            "required": ["expression"],
        },
        "handler": calculate,
    },
    {
        "name": "todo_add",
        "description": "往待办清单里添加一条待办。",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "待办内容"}},
            "required": ["text"],
        },
        "handler": todo_add,
    },
    {
        "name": "todo_list",
        "description": "查看当前所有待办及其完成状态。",
        "input_schema": {"type": "object", "properties": {}},
        "handler": todo_list,
    },
    {
        "name": "todo_done",
        "description": "把第 N 条待办标记为完成(N 从 1 开始)。",
        "input_schema": {
            "type": "object",
            "properties": {"index": {"type": "integer", "description": "待办序号, 从 1 开始"}},
            "required": ["index"],
        },
        "handler": todo_done,
    },
    {
        "name": "file_write",
        "description": "在 workspace 目录里写一个文本文件(不存在则创建)。",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "相对路径, 例如 notes/today.md"},
                "content": {"type": "string", "description": "文件内容"},
            },
            "required": ["path", "content"],
        },
        "handler": file_write,
    },
    {
        "name": "file_read",
        "description": "读取 workspace 目录里的文本文件。",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "相对路径"}},
            "required": ["path"],
        },
        "handler": file_read,
    },
    {
        "name": "file_list",
        "description": "列出 workspace 目录里的所有文件。",
        "input_schema": {"type": "object", "properties": {}},
        "handler": file_list,
    },
    {
        "name": "weather",
        "description": "查询某个城市当前的天气(需要联网)。",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名, 例如 北京"}},
            "required": ["city"],
        },
        "handler": get_weather,
    },
    {
        "name": "current_time",
        "description": "获取当前的日期和时间。",
        "input_schema": {"type": "object", "properties": {}},
        "handler": current_time,
    },
]

TOOLS_BY_NAME = {tool["name"]: tool for tool in TOOLS}


def tool_schemas():
    """给大模型 function calling 用的工具定义(去掉 Python 函数对象)。"""
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            },
        }
        for tool in TOOLS
    ]


def mcp_tool_schemas():
    """MCP ``tools/list`` 用的工具定义。"""
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": tool["input_schema"],
        }
        for tool in TOOLS
    ]


class LocalToolBox:
    """直接在本进程里调用工具。"""

    def schemas(self):
        return tool_schemas()

    def call(self, name, arguments=None):
        tool = TOOLS_BY_NAME.get(name)
        if tool is None:
            raise ToolError("未知工具: {}".format(name))
        try:
            return tool["handler"](**(arguments or {}))
        except ToolError:
            raise
        except TypeError as exc:
            raise ToolError("参数不对: {}".format(exc))
        except Exception as exc:  # 工具内部的意外错误也要变成人话
            raise ToolError("工具执行失败: {}".format(exc))
