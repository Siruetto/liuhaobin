"""智能体的端到端测试(离线模式, 不需要 API Key)。"""

import os
import shutil
import tempfile
import unittest
from unittest import mock

import tools
from agent_core import Agent
from memory import Memory
from tools import LocalToolBox


class AgentTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.workspace = os.path.join(self.tmp, "workspace")
        os.makedirs(self.workspace)
        self.memory_path = os.path.join(self.tmp, "memory.json")
        self._patches = [
            mock.patch.object(tools, "WORKSPACE_DIR", self.workspace),
            mock.patch.object(tools, "TODO_FILE", os.path.join(self.tmp, "todos.json")),
        ]
        for patch in self._patches:
            patch.start()
        self.agent = Agent(
            toolbox=LocalToolBox(), memory=Memory(path=self.memory_path), offline=True
        )

    def tearDown(self):
        for patch in self._patches:
            patch.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_calculator_end_to_end(self):
        reply = self.agent.chat("帮我算一下 (2+3)*4")
        self.assertEqual("20", reply["text"])
        self.assertEqual("calculator", reply["actions"][0]["tool"])

    def test_todo_round_trip(self):
        self.agent.chat("记一下 交作业")
        self.assertIn("交作业", self.agent.chat("看看待办")["text"])

    def test_history_grows(self):
        self.agent.chat("现在几点")
        self.agent.chat("你能做什么")
        history = self.agent.history()
        self.assertEqual(4, len(history))
        self.assertEqual("user", history[0]["role"])
        self.assertEqual("assistant", history[1]["role"])

    def test_facts_are_persisted_to_disk(self):
        self.agent.chat("我叫刘浩彬")
        reloaded = Memory(path=self.memory_path)
        self.assertEqual("刘浩彬", reloaded.recall().get("name"))

    def test_reset_clears_everything(self):
        self.agent.chat("记一下 临时任务")
        self.agent.reset()
        self.assertEqual([], self.agent.history())
        self.assertEqual({}, self.agent.memory.recall())

    def test_mode_is_offline(self):
        self.assertEqual("offline", self.agent.mode)
