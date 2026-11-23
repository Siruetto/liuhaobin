"""在上一版工具注册表上增加提醒工具。"""

from bootstrap import ensure_agent_project_on_path

ensure_agent_project_on_path()

from schedule import query_schedule  # noqa: E402
from tools import LocalToolBox, ToolError  # noqa: E402


EXTRA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "schedule_query",
            "description": "查询今天、明天或指定星期的课程表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "string",
                        "description": "today、tomorrow 或 周一/周二等",
                    }
                },
                "required": [],
            },
        },
    }
]


class ReminderToolBox:
    """原有九个工具加课表查询共十个; 提醒是核心服务, 不膨胀工具数。"""

    def __init__(self, scheduler, base=None):
        self.scheduler = scheduler
        self.base = base or LocalToolBox()

    def schemas(self):
        return self.base.schemas() + EXTRA_TOOLS

    def mcp_schemas(self):
        return [
            {
                "name": item["function"]["name"],
                "description": item["function"]["description"],
                "inputSchema": item["function"]["parameters"],
            }
            for item in EXTRA_TOOLS
        ]

    def call(self, name, arguments=None):
        arguments = arguments or {}
        try:
            if name == "reminder_add":
                reminder = self.scheduler.add(
                    arguments.get("content"),
                    arguments.get("remind_at"),
                    arguments.get("repeat_type", "once"),
                    arguments.get("repeat_interval", 0),
                )
                return "已记下提醒 #{}: {}（{}，{}）".format(
                    reminder["reminder_id"],
                    reminder["content"],
                    reminder["remind_at"],
                    reminder["repeat_type"],
                )
            if name == "reminder_list":
                return self._list_text()
            if name == "reminder_done":
                reminder_id = int(arguments["reminder_id"])
                if not self.scheduler.mark_done(reminder_id):
                    raise ToolError("没有找到提醒 #{}".format(reminder_id))
                return "提醒 #{} 已标记完成。".format(reminder_id)
            if name == "reminder_snooze":
                reminder_id = int(arguments["reminder_id"])
                minutes = int(arguments.get("minutes", 10))
                reminder = self.scheduler.snooze(reminder_id, minutes)
                if reminder is None:
                    raise ToolError("没有找到提醒 #{}".format(reminder_id))
                return "提醒 #{} 已推迟到 {}。".format(
                    reminder_id, reminder["remind_at"]
                )
            if name == "schedule_query":
                return query_schedule(arguments.get("day", "today"))
        except (KeyError, TypeError, ValueError) as error:
            raise ToolError("提醒参数不正确: {}".format(error))
        return self.base.call(name, arguments)

    def _list_text(self):
        reminders = self.scheduler.list("pending")
        if not reminders:
            return "提醒列表是空的。"
        lines = ["未完成提醒:"]
        for item in reminders:
            lines.append(
                "#{} {} [{} / {}]".format(
                    item["reminder_id"],
                    item["content"],
                    item["remind_at"],
                    item["repeat_type"],
                )
            )
        return "\n".join(lines)
