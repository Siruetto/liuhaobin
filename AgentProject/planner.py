"""规划器: 把"用户说的一句话"变成"调用哪些工具、怎么回答"。

这里有两种实现, 对外接口一样:

* ``LLMPlanner``    —— 调大模型, 由模型通过 function calling 自己决定用哪个工具;
* ``OfflinePlanner``—— 没有 API Key 时用正则把常见说法映射到工具, 保证离线也能演示。

两者都返回 ``{"text": 回复, "actions": [工具调用记录]}``, 前端和命令行都能直接展示。
"""

import json
import re

import llm
from tools import ToolError

MAX_TOOL_ROUNDS = 6

SYSTEM_PROMPT = """你是一个中文办公助理, 能调用工具帮用户做事。

规则:
1. 能算的用 calculator; 涉及待办用 todo_*; 读写文件用 file_*; 问天气用 weather; 问时间用 current_time。
2. 需要工具就直接调用, 不要假装自己算过。
3. 拿到工具结果后, 用简短的中文回答, 不要重复工具的原始返回格式。
4. 用户只是在聊天、问你能做什么时, 直接回答, 不要乱调工具。
5. 不确定城市或文件路径时, 先问清楚再调用。
"""

HELP_TEXT = """我能做这些事:
1. 算数: "帮我算一下 (3+5)*2"
2. 待办: "记一下 买牛奶" / "看看待办" / "完成第 2 条"
3. 文件: "把 hello 写到 a.txt" / "读一下 a.txt" / "有哪些文件"
4. 天气: "北京天气怎么样"
5. 时间: "现在几点"
6. 记忆: "我叫刘浩彬" / "我叫什么"
没有配置大模型时, 我只认上面这些固定说法; 配置了 API Key 就可以随便聊。"""


class BasePlanner:
    def __init__(self, toolbox):
        self.toolbox = toolbox

    def respond(self, text, memory):
        """返回 {"text": 回复, "actions": [...]}。"""
        raise NotImplementedError

    @staticmethod
    def _pack(result, ok=True, tool=None, arguments=None):
        action = {"tool": tool, "arguments": arguments or {}, "ok": ok, "result": result}
        return {"text": result, "actions": [action]}


class LLMPlanner(BasePlanner):
    """让大模型自己决定调用哪些工具。"""

    def respond(self, text, memory):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(memory.history())
        messages.append({"role": "user", "content": text})
        actions = []

        for _round in range(MAX_TOOL_ROUNDS):
            try:
                message = llm.chat(messages, tools=self.toolbox.schemas())
            except llm.LLMError as error:
                return {"text": "调用大模型失败: {}".format(error), "actions": actions}

            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                reply = (message.get("content") or "").strip() or "(模型没有返回内容)"
                return {"text": reply, "actions": actions}

            messages.append(message)
            for call in tool_calls:
                function = call.get("function") or {}
                name = function.get("name") or ""
                try:
                    arguments = json.loads(function.get("arguments") or "{}")
                except ValueError:
                    arguments = {}
                result, ok = self._run(name, arguments)
                actions.append(
                    {"tool": name, "arguments": arguments, "ok": ok, "result": result}
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id", ""),
                        "content": result,
                    }
                )

        return {
            "text": "这条指令要调用的工具太多了, 我先停下。可以把问题拆小一点再说一次。",
            "actions": actions,
        }

    def _run(self, name, arguments):
        try:
            return self.toolbox.call(name, arguments), True
        except ToolError as error:
            return "工具出错: {}".format(error), False


class OfflinePlanner(BasePlanner):
    """不依赖大模型: 用正则把常见说法映射到工具调用。"""

    def __init__(self, toolbox):
        super().__init__(toolbox)
        self.last_intent = None

    # ------------------------------------------------------------ 入口
    def respond(self, text, memory):
        message = (text or "").strip()
        if not message:
            return {"text": "你想让我做什么? 说\"帮助\"可以看我会什么。", "actions": []}
        for handler in (
            self._about_me,
            self._help,
            self._time,
            self._weather,
            self._todo_add,
            self._todo_done,
            self._todo_list,
            self._file_write,
            self._file_read,
            self._file_list,
            self._calculate,
        ):
            result = handler(message, memory)
            if result is not None:
                return result
        return self._fallback()

    # ------------------------------------------------------------ 小工具
    def _act(self, name, arguments, intent, memory=None, note=None):
        try:
            result = self.toolbox.call(name, arguments)
            ok = True
        except ToolError as error:
            result = "工具出错: {}".format(error)
            ok = False
        self.last_intent = intent
        if memory is not None and note:
            memory.remember(note[0], note[1])
        return self._pack(result, ok=ok, tool=name, arguments=arguments)

    # ------------------------------------------------------------ 规则
    def _about_me(self, message, memory):
        if re.search(r"我叫什么|我的名字", message):
            name = memory.recall().get("name")
            reply = "你叫{}。".format(name) if name else "你还没告诉过我名字。"
            return {"text": reply, "actions": []}
        match = re.search(r"我叫\s*([^\s,，。!！?？]{1,20})", message)
        if match:
            name = match.group(1)
            memory.remember("name", name)
            return {"text": "记住了, 你叫{}。".format(name), "actions": []}
        return None

    def _help(self, message, memory):
        if re.search(r"帮助|你能做什么|会做什么|会什么|help|功能", message, re.I):
            return {"text": HELP_TEXT, "actions": []}
        return None

    def _time(self, message, memory):
        if re.search(r"几点|什么时间|现在时间|日期|几号|星期几|\bnow\b|\btime\b", message, re.I):
            return self._act("current_time", {}, "time")
        return None

    def _weather(self, message, memory):
        match = re.search(r"([\u4e00-\u9fa5]{2,8}?)(?:市|区|县)?的?天气", message)
        if match:
            city = self._clean_city(match.group(1))
            self.last_intent = "weather"
            return self._act("weather", {"city": city}, "weather")
        if self.last_intent == "weather":
            follow = re.search(r"^(?:那|还有)?\s*([\u4e00-\u9fa5]{2,8}?)(?:呢|怎么样|如何)?[?？]?$", message)
            if follow and follow.group(1) not in ("天气",):
                return self._act("weather", {"city": follow.group(1)}, "weather")
        return None

    @staticmethod
    def _clean_city(text):
        """把"帮我查一下北京"这类前后缀去掉, 只留下城市名。"""
        filler = re.compile(
            r"^(?:帮我|请|麻烦|我想知道)?(?:查一下|查询|查查|查|看看)?(?:一下)?(?:今天|明天|现在)?(?:的)?"
        )
        cleaned = filler.sub("", text).strip().rstrip("的")
        return cleaned or text

    def _calculate(self, message, memory):
        match = re.search(
            r"(?:帮我)?(?:计算|算一下|算算|算)\s*(.+?)(?:等于多少|是多少|等于|=)?[?？]?$",
            message,
        )
        if match is None:
            match = re.search(r"^(.+?)(?:等于多少|是多少|等于几)[?？]?$", message)
        expression = match.group(1) if match else None
        if expression is None and re.match(r"^[\d\s+\-*/%().]+$", message):
            expression = message
        if not expression:
            return None
        return self._act("calculator", {"expression": expression.strip()}, "calc")

    def _todo_add(self, message, memory):
        match = re.search(
            r"(?:记一下|记下|帮我记|添加待办|加个待办|提醒我|todo\s*add)[:：]?\s*(.+)$",
            message,
            re.I,
        )
        if not match:
            return None
        return self._act("todo_add", {"text": match.group(1).strip()}, "todo")

    def _todo_done(self, message, memory):
        match = re.search(r"(?:完成|做完|搞定)\s*(?:第)?\s*(\d+)\s*(?:条|个)?", message) or re.search(
            r"第\s*(\d+)\s*(?:条|个)?\s*(?:完成|做完)", message
        )
        if not match:
            return None
        return self._act("todo_done", {"index": int(match.group(1))}, "todo")

    def _todo_list(self, message, memory):
        if re.search(r"待办|任务列表|清单|还有什么事|todo\s*list", message, re.I):
            return self._act("todo_list", {}, "todo")
        return None

    def _file_write(self, message, memory):
        match = re.search(r"把(.+?)(?:写|保存)(?:到|进|成)\s*([\w./\\-]+\.\w+)", message)
        if match:
            return self._act(
                "file_write",
                {"path": match.group(2), "content": match.group(1).strip()},
                "file",
            )
        match = re.search(
            r"(?:创建|新建|写入|写到|保存到)\s*(?:文件)?\s*([\w./\\-]+\.\w+)\s*(?:内容|写入|为)?[:：]?\s*(.*)$",
            message,
        )
        if match:
            return self._act(
                "file_write",
                {"path": match.group(1), "content": match.group(2).strip()},
                "file",
            )
        return None

    def _file_read(self, message, memory):
        match = re.search(
            r"(?:读取?|打开|看一下|看看|瞧瞧)\s*(?:一下)?\s*(?:文件)?\s*([\w./\\-]+\.\w+)",
            message,
        )
        if not match:
            return None
        return self._act("file_read", {"path": match.group(1)}, "file")

    def _file_list(self, message, memory):
        if re.search(r"有哪些文件|列出文件|文件列表|workspace.*文件|^ls$", message, re.I):
            return self._act("file_list", {}, "file")
        return None

    def _fallback(self):
        return {
            "text": "这句话我还不太会处理。\n" + HELP_TEXT,
            "actions": [],
        }
