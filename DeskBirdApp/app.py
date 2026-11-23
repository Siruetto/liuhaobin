"""报时鸟第三阶段最小闭环入口。"""

import argparse
import os
import sys
import time

from bootstrap import APP_ROOT, ensure_agent_project_on_path

ensure_agent_project_on_path()

from agent_core import Agent  # noqa: E402
from memory import Memory  # noqa: E402
from reminder_planner import ReminderPlanner  # noqa: E402
from reminder_scheduler import ReminderScheduler  # noqa: E402
from reminder_toolbox import ReminderToolBox  # noqa: E402


DATA_DIR = os.path.join(APP_ROOT, "data")
DEFAULT_DB = os.path.join(DATA_DIR, "deskbird.db")
DEFAULT_MEMORY = os.path.join(DATA_DIR, "memory.json")
APP_VERSION = "0.1.0-alpha.1"


def create_agent(db_path=None, memory_path=None, clock=None):
    scheduler = ReminderScheduler(db_path or DEFAULT_DB)
    toolbox = ReminderToolBox(scheduler)
    memory = Memory(path=memory_path or DEFAULT_MEMORY)
    agent = Agent(toolbox=toolbox, memory=memory, offline=True)
    agent.planner = ReminderPlanner(toolbox, clock=clock)
    agent.scheduler = scheduler
    return agent


def print_notification(notification):
    print(
        "[到点提醒] #{} {}（计划 {}）".format(
            notification["id"],
            notification["content"],
            notification["scheduled_at"],
        )
    )


def build_parser():
    parser = argparse.ArgumentParser(description="报时鸟：说一句就记，到点主动提醒")
    parser.add_argument("message", nargs="*", help="要处理的一句话; 不给就进入交互模式")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite 路径")
    parser.add_argument("--tick", action="store_true", help="立即扫描一次到期提醒")
    parser.add_argument(
        "--watch", type=int, metavar="SECONDS", help="每 N 秒扫描一次到期提醒"
    )
    parser.add_argument("--show-actions", action="store_true", help="显示工具调用")
    return parser


def print_actions(reply):
    for action in reply.get("actions", []):
        print(
            "  [工具] {}({}) -> {}".format(
                action.get("tool"),
                action.get("arguments"),
                "ok" if action.get("ok") else "失败",
            )
        )


def main(argv=None):
    args = build_parser().parse_args(argv)
    agent = create_agent(db_path=args.db)

    if args.tick:
        agent.scheduler.tick(notify=print_notification)
        return 0

    if args.watch:
        print("报时鸟已开始值守，每 {} 秒扫描一次。".format(args.watch))
        try:
            while True:
                agent.scheduler.tick(notify=print_notification)
                time.sleep(max(1, args.watch))
        except KeyboardInterrupt:
            print("\n报时鸟已停止值守。")
        return 0

    if args.message:
        reply = agent.chat(" ".join(args.message))
        print(reply["text"])
        if args.show_actions:
            print_actions(reply)
        return 0

    print("报时鸟已启动（离线模式）。输入 exit 退出。")
    while True:
        try:
            text = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not text:
            continue
        if text.lower() in ("exit", "quit", "退出"):
            return 0
        reply = agent.chat(text)
        print("报时鸟> {}".format(reply["text"]))
        if args.show_actions:
            print_actions(reply)


if __name__ == "__main__":
    sys.exit(main())
