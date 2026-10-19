# 办公小助手（能说会做的智能体）

一个可以用自然语言指挥的办公助理：**能聊天**，也能**真的动手做事**——
算数、记待办、读写文件、查天气、看时间。工具通过本地调用，
也可以走 **MCP（Model Context Protocol）** 子进程。

## 快速开始（不需要 API Key）

```bash
python agent.py "帮我算一下 (3+5)*2"
python agent.py "记一下 周五前交周报"
python agent.py "看看待办"
python agent.py "把 会议改到周三 写到 notes/todo.md"
python agent.py "现在几点"
```

不带参数就是交互式对话：

```bash
python agent.py
```

默认情况下：**配置了 API Key 就用大模型，没配置就自动用离线规则模式**，
所以拷到任何一台装了 Python 的机器上都能直接演示。

## 大模型模式

用任意兼容 OpenAI `chat/completions` 的服务，通过环境变量配置：

```bash
# Windows PowerShell
$env:AGENT_API_KEY="sk-xxx"
$env:AGENT_BASE_URL="https://api.openai.com/v1"        # 可选
$env:AGENT_MODEL="gpt-4o-mini"                          # 可选
python agent.py
```

阿里云百炼的兼容模式：

```bash
$env:AGENT_API_KEY="sk-xxx"
$env:AGENT_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:AGENT_MODEL="qwen-plus"
python agent.py "帮我看看北京天气，然后记一下明天带伞"
```

大模型模式走的是 **function calling**：模型自己决定调用哪个工具、传什么参数，
拿到工具结果后再组织成自然语言回答。

## MCP 模式

工具也可以通过 MCP 协议交给子进程执行：

```bash
python agent.py --mcp "现在几点"
```

`mcp_server.py` 实现了 MCP 的核心方法（`initialize` / `tools/list` / `tools/call`），
用 stdio 传 JSON-RPC，一行一条消息。任何 MCP 客户端都可以接进来。

## 网页界面

```bash
python web_ui.py --port 8000
```

浏览器打开 <http://127.0.0.1:8000>，左侧聊天、右侧可以看到每次调用了哪个工具。

## 工具一览

| 工具 | 作用 | 例子 |
| --- | --- | --- |
| `calculator` | 安全计算四则运算（ast 解析，不用 eval） | “帮我算一下 (3+5)*2” |
| `todo_add` / `todo_list` / `todo_done` | 待办清单，落盘保存 | “记一下 买牛奶” |
| `file_write` / `file_read` / `file_list` | 读写 `workspace/` 里的文件（挡住 `../` 和绝对路径） | “把 hello 写到 a.txt” |
| `weather` | 查实时天气（Open-Meteo，无需 Key，需要联网） | “北京天气怎么样” |
| `current_time` | 当前日期时间 | “现在几点” |

## 目录结构

```
agent-project/
├── agent.py          命令行入口（交互 / 单条 / --mcp / --offline）
├── agent_core.py     智能体主体：选规划器、维护记忆
├── planner.py        两种规划器：大模型 function calling / 离线规则
├── llm.py            OpenAI 兼容的 Chat Completions 客户端（标准库）
├── tools.py          工具实现 + JSON Schema
├── memory.py         多轮对话记忆 + 长期记忆（落盘）
├── mcp_server.py     MCP stdio 服务端
├── mcp_client.py     MCP 客户端（把工具放到子进程里执行）
├── web_ui.py         网页界面（标准库 http.server）
├── config.py         路径与运行配置
├── tests/            51 个单元测试
├── workspace/        文件工具能碰到的唯一目录
└── data/             待办和记忆的落盘位置
```

## 运行测试

```bash
python -m unittest discover -s tests -t . -v
```

51 个用例，覆盖工具、规划器意图识别、MCP 协议、智能体端到端，不需要联网。

## 几个安全上的考虑

* 计算器不用 `eval`，用 `ast` 白名单，只允许数字和四则运算；
* 文件工具只能操作 `workspace/`，`../` 和绝对路径都会被拒绝；
* 工具出错不会让程序崩，统一变成一句人话返回；
* 记忆写不进磁盘时只影响记忆，不影响对话。
