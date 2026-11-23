"""在离线规划器上增加提醒意图, 其他意图继续复用上一版能力。"""

import datetime
import re

from bootstrap import ensure_agent_project_on_path

ensure_agent_project_on_path()

from planner import OfflinePlanner  # noqa: E402
from tools import ToolError  # noqa: E402


TIME_PATTERN = (
    r"(?P<period>上午|中午|下午|晚上)?\s*"
    r"(?P<hour>\d{1,2})(?:[:：](?P<minute>\d{1,2})"
    r"|点(?:(?P<minute_after>\d{1,2})分?|(?P<half>半))?)"
)
DATE_PATTERN = r"(?P<date>今天|明天|后天|(?:周|星期)[一二三四五六日天])?"


class ReminderParser:
    """解析本项目第一阶段支持的常见提醒说法。"""

    def parse(self, text, now=None):
        message = (text or "").strip()
        current = now or datetime.datetime.now()

        match = re.match(
            r"^(?:请|帮我)?每\s*(?P<minutes>\d+)\s*(?:分钟|分)\s*"
            r"(?:提醒我?)?\s*(?P<content>.+)$",
            message,
        )
        if match:
            content = self._clean_content(match.group("content"))
            if not content:
                return None
            return {
                "content": content,
                "remind_at": current + datetime.timedelta(minutes=int(match.group("minutes"))),
                "repeat_type": "interval",
                "repeat_interval": int(match.group("minutes")),
            }

        match = re.match(
            r"^(?:请|帮我)?(?:每天|每日)\s*" + TIME_PATTERN
            + r"\s*(?:提醒我?)?\s*(?P<content>.+)$",
            message,
        )
        if match:
            content = self._clean_content(match.group("content"))
            if not content:
                return None
            remind_at = self._build_time(current.date(), match)
            if remind_at <= current:
                remind_at += datetime.timedelta(days=1)
            return {
                "content": content,
                "remind_at": remind_at,
                "repeat_type": "daily",
                "repeat_interval": 0,
            }

        match = re.match(
            r"^(?:请|帮我)?(?:提醒我?|别忘了|记得)\s*"
            + DATE_PATTERN
            + r"\s*"
            + TIME_PATTERN
            + r"\s*(?P<content>.+)$",
            message,
        )
        if match:
            content = self._clean_content(match.group("content"))
            if not content:
                return None
            day = self._resolve_date(match.group("date"), current)
            remind_at = self._build_time(day, match)
            if match.group("date") is None and remind_at <= current:
                remind_at += datetime.timedelta(days=1)
            if match.group("date") not in (None, "今天") and remind_at <= current:
                remind_at += datetime.timedelta(days=7)
            return {
                "content": content,
                "remind_at": remind_at,
                "repeat_type": "once",
                "repeat_interval": 0,
            }
        return None

    @staticmethod
    def _clean_content(value):
        return re.sub(r"^(?:提醒我?|叫我)\s*", "", value).strip(" ，,：:-")

    @staticmethod
    def _resolve_date(value, current):
        if value == "明天":
            return current.date() + datetime.timedelta(days=1)
        if value == "后天":
            return current.date() + datetime.timedelta(days=2)
        if value and value.startswith(("周", "星期")):
            label = value[-1].replace("天", "日")
            target = "一二三四五六日".index(label)
            delta = (target - current.weekday()) % 7
            return current.date() + datetime.timedelta(days=delta)
        return current.date()

    @staticmethod
    def _build_time(day, match):
        hour = int(match.group("hour"))
        minute_text = (
            match.group("minute")
            or match.group("minute_after")
            or ("30" if match.group("half") else "0")
        )
        minute = int(minute_text)
        period = match.group("period")
        if period in ("下午", "晚上") and hour < 12:
            hour += 12
        if period == "中午" and hour < 11:
            hour += 12
        return datetime.datetime.combine(day, datetime.time(hour, minute))


class ReminderPlanner:
    """优先识别提醒命令, 其余输入交给上一版离线规划器。"""

    def __init__(self, toolbox, clock=None):
        self.toolbox = toolbox
        self.clock = clock or datetime.datetime.now
        self.base = OfflinePlanner(toolbox)
        self.parser = ReminderParser()

    def respond(self, text, memory):
        message = (text or "").strip()

        match = re.search(r"(?:查看|看看|列出)?提醒(?:列表|清单)?", message)
        if match and re.search(r"查看|看看|列出|待办|列表|清单", message):
            return self._call("reminder_list", {}, memory)

        match = re.search(r"(?:完成|取消)\s*(?:第)?\s*(\d+)\s*(?:条)?提醒", message)
        if match:
            return self._call(
                "reminder_done", {"reminder_id": int(match.group(1))}, memory
            )

        match = re.search(
            r"(?:把)?\s*(?:第)?\s*(\d+)\s*条?提醒.*(?:推迟|延后)\s*(\d+)\s*分钟",
            message,
        )
        if match:
            return self._call(
                "reminder_snooze",
                {"reminder_id": int(match.group(1)), "minutes": int(match.group(2))},
                memory,
            )

        if re.search(r"课表|有什么课|上什么课", message):
            day = "today"
            if "明天" in message:
                day = "tomorrow"
            else:
                weekday = re.search(r"(?:周|星期)[一二三四五六日天]", message)
                if weekday:
                    day = weekday.group(0)
            return self._call("schedule_query", {"day": day}, memory)

        spec = self.parser.parse(message, now=self.clock())
        if spec:
            arguments = {
                "content": spec["content"],
                "remind_at": spec["remind_at"].strftime("%Y-%m-%d %H:%M"),
                "repeat_type": spec["repeat_type"],
                "repeat_interval": spec["repeat_interval"],
            }
            return self._call("reminder_add", arguments, memory)

        if re.search(r"提醒|每天|每日|每\s*\d+\s*(?:分钟|分)", message):
            return {
                "text": "请带上时间，例如：提醒我 明天 22:00 交软工作业。",
                "actions": [],
            }
        return self.base.respond(message, memory)

    def _call(self, name, arguments, memory):
        try:
            result = self.toolbox.call(name, arguments)
            ok = True
        except ToolError as error:
            result = "工具出错: {}".format(error)
            ok = False
        return {
            "text": result,
            "actions": [
                {"tool": name, "arguments": arguments, "ok": ok, "result": result}
            ],
        }
