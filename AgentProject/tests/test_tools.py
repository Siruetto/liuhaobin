"""工具层的单元测试: 计算器、待办、文件、天气、时间。"""

import os
import shutil
import tempfile
import unittest
from unittest import mock

import tools


class ToolTestBase(unittest.TestCase):
    """每个用例都用自己的临时目录, 互不干扰。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.workspace = os.path.join(self.tmp, "workspace")
        os.makedirs(self.workspace)
        self.todo_file = os.path.join(self.tmp, "todos.json")
        self._patches = [
            mock.patch.object(tools, "WORKSPACE_DIR", self.workspace),
            mock.patch.object(tools, "TODO_FILE", self.todo_file),
        ]
        for patch in self._patches:
            patch.start()

    def tearDown(self):
        for patch in self._patches:
            patch.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)


class CalculatorTest(ToolTestBase):

    def test_basic_arithmetic(self):
        self.assertEqual("16", tools.calculate("(3+5)*2"))

    def test_operator_precedence(self):
        self.assertEqual("14", tools.calculate("2+3*4"))

    def test_division_returns_decimal(self):
        self.assertEqual("3.5", tools.calculate("7/2"))

    def test_integer_result_is_not_float(self):
        self.assertEqual("4", tools.calculate("8/2"))

    def test_rejects_division_by_zero(self):
        with self.assertRaises(tools.ToolError):
            tools.calculate("1/0")

    def test_rejects_code_injection(self):
        with self.assertRaises(tools.ToolError):
            tools.calculate('__import__("os").system("dir")')

    def test_rejects_huge_exponent(self):
        with self.assertRaises(tools.ToolError):
            tools.calculate("9**999")

    def test_rejects_empty_expression(self):
        with self.assertRaises(tools.ToolError):
            tools.calculate("   ")


class TodoTest(ToolTestBase):

    def test_add_and_list(self):
        tools.todo_add("买牛奶")
        self.assertIn("买牛奶", tools.todo_list())

    def test_done_marks_item(self):
        tools.todo_add("写作业")
        tools.todo_done(1)
        self.assertIn("[x] 写作业", tools.todo_list())

    def test_invalid_index_is_rejected(self):
        tools.todo_add("只有一条")
        with self.assertRaises(tools.ToolError):
            tools.todo_done(5)

    def test_list_is_empty_at_start(self):
        self.assertIn("空", tools.todo_list())

    def test_items_are_persisted(self):
        tools.todo_add("持久化测试")
        self.assertTrue(os.path.exists(self.todo_file))
        tools.todo_list()  # 重新读文件
        self.assertIn("持久化测试", tools.todo_list())


class FileToolTest(ToolTestBase):

    def test_write_then_read(self):
        tools.file_write("notes/a.txt", "hello")
        self.assertEqual("hello", tools.file_read("notes/a.txt"))

    def test_nested_directories_are_created(self):
        tools.file_write("a/b/c.txt", "deep")
        self.assertEqual("deep", tools.file_read("a/b/c.txt"))

    def test_list_files(self):
        tools.file_write("one.txt", "1")
        tools.file_write("sub/two.txt", "2")
        listing = tools.file_list()
        self.assertIn("one.txt", listing)
        self.assertIn("sub/two.txt", listing)

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(tools.ToolError):
            tools.file_write("../outside.txt", "x")

    def test_absolute_path_is_rejected(self):
        with self.assertRaises(tools.ToolError):
            tools.file_write(os.path.join(self.tmp, "abs.txt"), "x")

    def test_missing_file_is_reported(self):
        with self.assertRaises(tools.ToolError):
            tools.file_read("nope.txt")

    def test_empty_workspace_message(self):
        self.assertIn("还没有文件", tools.file_list())


class WeatherTest(ToolTestBase):

    def test_weather_is_formatted(self):
        def fake_get_json(url, timeout=8):
            if "geocoding" in url:
                return {"results": [{"name": "北京", "latitude": 39.9, "longitude": 116.4}]}
            return {"current_weather": {"temperature": 21.5, "windspeed": 8.0, "weathercode": 0}}

        with mock.patch.object(tools, "_http_get_json", fake_get_json):
            reply = tools.get_weather("北京")
        self.assertIn("北京", reply)
        self.assertIn("21.5", reply)
        self.assertIn("晴", reply)

    def test_unknown_city_is_reported(self):
        with mock.patch.object(tools, "_http_get_json", lambda url, timeout=8: {"results": []}):
            with self.assertRaises(tools.ToolError):
                tools.get_weather("不存在的地方")

    def test_network_error_is_a_tool_error(self):
        def boom(url, timeout=8):
            raise OSError("network down")

        with mock.patch.object(tools, "_http_get_json", boom):
            with self.assertRaises(tools.ToolError):
                tools.get_weather("北京")


class TimeTest(ToolTestBase):

    def test_current_time_has_date(self):
        self.assertIn("-", tools.current_time())
        self.assertIn("星期", tools.current_time())


class ToolBoxTest(ToolTestBase):

    def test_unknown_tool_is_rejected(self):
        with self.assertRaises(tools.ToolError):
            tools.LocalToolBox().call("no_such_tool", {})

    def test_schemas_have_expected_shape(self):
        names = set()
        for item in tools.tool_schemas():
            self.assertEqual("function", item["type"])
            self.assertIn("name", item["function"])
            self.assertIn("parameters", item["function"])
            names.add(item["function"]["name"])
        self.assertIn("calculator", names)
        self.assertIn("weather", names)
