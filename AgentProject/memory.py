"""对话记忆: 多轮上下文 + 简单的长期记忆。

* 短期记忆: 最近若干轮对话, 每次请求都带给大模型, 让它知道"刚才聊了什么";
* 长期记忆: 键值对(比如用户的名字、常问的城市), 存到 ``data/memory.json``,
  重启程序也还在。
"""

import json
import os

from config import MEMORY_FILE


class Memory:
    """保存对话历史和少量长期事实。"""

    def __init__(self, path=None, max_turns=20):
        self.path = path or MEMORY_FILE
        self.max_turns = max_turns
        self.turns = []
        self.facts = {}
        self.load()

    # ---------------------------------------------------------- 读写文件
    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            return
        if not isinstance(data, dict):
            return
        turns = data.get("turns")
        if isinstance(turns, list):
            self.turns = turns[-self.max_turns * 2:]
        facts = data.get("facts")
        if isinstance(facts, dict):
            self.facts = facts

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        try:
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump(
                    {"turns": self.turns, "facts": self.facts},
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
        except OSError:
            # 记忆写不进去不应该让一次正常的对话崩掉
            pass

    # ---------------------------------------------------------- 短期记忆
    def add(self, role, content):
        """追加一轮对话, 只保留最近 max_turns 轮。"""
        self.turns.append({"role": role, "content": content})
        limit = max(2, self.max_turns * 2)
        if len(self.turns) > limit:
            self.turns = self.turns[-limit:]

    def history(self):
        """给大模型用的历史消息(不含本次用户输入)。"""
        return [dict(turn) for turn in self.turns]

    # ---------------------------------------------------------- 长期记忆
    def remember(self, key, value):
        self.facts[key] = value
        self.save()

    def recall(self):
        return dict(self.facts)

    def forget_all(self):
        self.turns = []
        self.facts = {}
        self.save()
