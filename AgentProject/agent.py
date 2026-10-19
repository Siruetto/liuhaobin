"""命令行入口: 交互式对话, 或者执行一条指令。

用法::

    python agent.py                          # 交互式对话
    python agent.py "帮我算一下 (3+5)*2"      # 只执行一条
    python agent.py --offline                # 强制用离线规则(不需要 API Key)
    python agent.py --mcp                    # 工具通过 MCP 子进程调用
    python agent.py --reset                  # 清空记忆
"""

import argparse
import sys

from agent_core import Agent
from tools import LocalToolBox


def build_parser():
    parser = argparse.ArgumentParser(
        description="能说会做的办公小助手(支持大模型与离线两种模式)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python agent.py \"帮我算一下 (3+5)*2\"\n"
            "  python agent.py \"记一下 买牛奶\"\n"
            "  python agent.py --offline \"北京天气怎么样\"\n"
            "  python agent.py --mcp \"现在几点\"\n"
        ),
    )
    parser.add_argument("message", nargs="*", help="要执行的一句话; 不给就进入交互模式")
    parser.add_argument("--offline", action="store_true", help="强制使用离线规则规划器")
    parser.add_argument("--llm", action="store_true", help="强制使用大模型(需要 API Key)")
    parser.add_argument("--mcp", action="store_true", help="工具通过 MCP 子进程调用")
    parser.add_argument("--reset", action="store_true", help="清空对话记忆后再开始")
    parser.add_argument("--show-actions", action="store_true", help="显示每一步调用了什么工具")
    return parser


def _print_actions(reply):
    for action in reply.get("actions", []):
        flag = "ok" if action.get("ok") else "失败"
        print("  [工具] {}({}) -> {}".format(action.get("tool"), action.get("arguments"), flag))


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.offline and args.llm:
        print("参数错误: --offline 和 --llm 不能同时给", file=sys.stderr)
        return 2

    toolbox = None
    if args.mcp:
        from mcp_client import MCPToolBox

        try:
            toolbox = MCPToolBox()
        except OSError as error:
            print("启动 MCP 服务失败: {}".format(error), file=sys.stderr)
            return 1
    else:
        toolbox = LocalToolBox()

    agent = Agent(toolbox=toolbox, offline=True if args.offline else (False if args.llm else None))
    if args.reset:
        agent.reset()
        print("记忆已清空。")

    if args.message:
        reply = agent.chat(" ".join(args.message))
        print(reply["text"])
        if args.show_actions:
            _print_actions(reply)
        return 0

    print("办公小助手已启动 (模式: {}, 工具: {})".format(
        "离线规则" if agent.mode == "offline" else "大模型",
        "MCP" if args.mcp else "本地",
    ))
    print("输入 exit 退出, 说\"帮助\"看能做什么。")
    while True:
        try:
            text = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text.lower() in ("exit", "quit", "退出"):
            break
        reply = agent.chat(text)
        print("助手> {}".format(reply["text"]))
        if args.show_actions:
            _print_actions(reply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
