"""智能体主体: 选规划器、维护记忆、把一次对话走完。"""

import llm
from memory import Memory
from planner import LLMPlanner, OfflinePlanner
from tools import LocalToolBox


class Agent:
    """一个最小可用的智能体。

    * ``toolbox`` 决定工具在哪里执行(本进程 / MCP 子进程);
    * ``offline`` 为 None 时自动判断: 有 API Key 用大模型, 没有就走离线规则。
    """

    def __init__(self, toolbox=None, memory=None, offline=None):
        self.toolbox = toolbox if toolbox is not None else LocalToolBox()
        self.memory = memory if memory is not None else Memory()
        if offline is None:
            offline = not llm.is_configured()
        self.mode = "offline" if offline else "llm"
        self.planner = OfflinePlanner(self.toolbox) if offline else LLMPlanner(self.toolbox)

    def chat(self, text):
        """处理一句用户输入, 返回 {"text": 回复, "actions": [...]}。"""
        reply = self.planner.respond(text, self.memory)
        self.memory.add("user", text)
        self.memory.add("assistant", reply["text"])
        self.memory.save()
        return reply

    def reset(self):
        """清空对话历史和长期记忆。"""
        self.memory.forget_all()

    def history(self):
        return self.memory.history()
