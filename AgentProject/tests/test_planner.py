"""离线规划器的意图识别测试。"""

import os
import shutil
import tempfile
import unittest
from unittest import mock

import tools
from memory import Memory
from planner import OfflinePlanner
from tools import LocalToolBox


class OfflinePlannerTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.workspace = os.path.join(self.tmp, "workspace")
        os.makedirs(self.workspace)
        self.todo_file = os.path.join(self.tmp, "todos.json")
        self.memory = Memory(path=os.path.join(self.tmp, "memory.json"))
        self._patches = [
            mock.patch.object(tools, "WORKSPACE_DIR", self.workspace),
            mock.patch.object(tools, "TODO_FILE", self.todo_file),
        ]
        for patch in self._patches:
            patch.start()
        self.planner = OfflinePlanner(LocalToolBox())

    def tearDown(self):
        for patch in self._patches:
            patch.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ask(self, text):
        return self.planner.respond(text, self.memory)

    def test_help(self):
        self.assertIn("算数", self.ask("你能做什么")["text"])

    def test_calculator(self):
        reply = self.ask("帮我算一下 (3+5)*2")
        self.assertEqual("16", reply["text"])
        self.assertEqual("calculator", reply["actions"][0]["tool"])

    def test_bare_expression(self):
        self.assertEqual("2", self.ask("1+1 等于多少")["text"])

    def test_todo_add_then_list(self):
        self.ask("记一下 买牛奶")
        self.assertIn("买牛奶", self.ask("看看待办")["text"])

    def test_todo_done(self):
        self.ask("记一下 写作业")
        reply = self.ask("完成第 1 条")
        self.assertEqual("todo_done", reply["actions"][0]["tool"])

    def test_file_write_then_read(self):
        self.ask("把 hello 写到 a.txt")
        self.assertEqual("hello", self.ask("读一下 a.txt")["text"])

    def test_file_list(self):
        self.ask("把 x 写到 b.txt")
        self.assertIn("b.txt", self.ask("有哪些文件")["text"])

    def test_weather_uses_extracted_city(self):
        patch = mock.patch.dict(
            tools.TOOLS_BY_NAME["weather"], {"handler": lambda city: "{} 晴".format(city)}
        )
        with patch:
            reply = self.ask("帮我查一下北京的天气")
        self.assertIn("北京", reply["text"])
        self.assertEqual("北京", reply["actions"][0]["arguments"]["city"])

    def test_weather_follow_up_uses_last_topic(self):
        patch = mock.patch.dict(
            tools.TOOLS_BY_NAME["weather"], {"handler": lambda city: "{} 晴".format(city)}
        )
        with patch:
            self.ask("北京天气")
            reply = self.ask("那上海呢")
        self.assertEqual("上海", reply["actions"][0]["arguments"]["city"])

    def test_time(self):
        self.assertIn("星期", self.ask("现在几点")["text"])

    def test_name_is_remembered(self):
        self.ask("我叫刘浩彬")
        self.assertIn("刘浩彬", self.ask("我叫什么")["text"])

    def test_unknown_input_falls_back(self):
        self.assertIn("还不太会", self.ask("今天讲个笑话")["text"])
