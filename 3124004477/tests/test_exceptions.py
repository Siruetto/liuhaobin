"""异常处理专项测试: 五种自定义异常各对应一个可构造的失败场景。

与博客"计算模块部分异常处理说明"一节一一对应。
"""

import contextlib
import io
import os
import shutil
import tempfile
import unittest
from unittest import mock

import main
import textio
from errors import (
    ArgumentError,
    DecodeError,
    InputFileError,
    OutputFileError,
    PlagiarismError,
)


class ExceptionTest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.original = self._write("orig.txt", "今天是星期天，天气晴，今天晚上我要去看电影。")
        self.copied = self._write("orig_add.txt", "今天是周天，天气晴朗，我晚上要去看电影。")
        self.answer = os.path.join(self.tmpdir, "ans.txt")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write(self, name, text, encoding="utf-8"):
        path = os.path.join(self.tmpdir, name)
        with open(path, "w", encoding=encoding) as handle:
            handle.write(text)
        return path

    def _run(self, argv):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main.main(argv)
        return code, stderr.getvalue()

    def test_argument_error_scenario_too_few_parameters(self):
        """场景: 只传了 2 个参数。期望: 退出码 2 并在 stderr 给出用法。"""
        code, message = self._run([self.original, self.copied])
        self.assertEqual(ArgumentError.exit_code, code)
        self.assertIn("python main.py", message)

    def test_input_file_error_scenario_original_path_is_a_directory(self):
        """场景: 原文路径指向了一个目录。期望: 退出码 3 并回显路径。"""
        code, message = self._run([self.tmpdir, self.copied, self.answer])
        self.assertEqual(InputFileError.exit_code, code)
        self.assertIn(self.tmpdir, message)

    def test_decode_error_scenario_binary_file(self):
        """场景: 原文是二进制文件, 两种编码都解不开。期望: 退出码 4。"""
        binary = os.path.join(self.tmpdir, "orig.bin")
        with open(binary, "wb") as handle:
            handle.write(b"\xff\xfe\xff\xff")
        code, message = self._run([binary, self.copied, self.answer])
        self.assertEqual(DecodeError.exit_code, code)
        self.assertIn("编码", message)

    def test_output_file_error_scenario_answer_directory_missing(self):
        """场景: 答案文件的父目录不存在。期望: 退出码 5。"""
        missing = os.path.join(self.tmpdir, "no_such_dir", "ans.txt")
        code, message = self._run([self.original, self.copied, missing])
        self.assertEqual(OutputFileError.exit_code, code)
        self.assertIn("答案文件", message)

    def test_input_file_error_scenario_open_fails(self):
        """场景: 文件存在但操作系统拒绝打开(权限/占用)。期望: InputFileError。"""
        with mock.patch("builtins.open", side_effect=OSError(13, "Permission denied")):
            with self.assertRaises(InputFileError):
                textio.read_text(self.original)

    def test_unexpected_error_is_swallowed_by_fallback(self):
        """场景: 预想不到的错误(类型传错)。期望: 兜底分支返回 1, 不抛调用栈。"""
        code, message = self._run([None, self.copied, self.answer])
        self.assertEqual(1, code)
        self.assertIn("未知错误", message)

    def test_every_exception_carries_its_own_exit_code(self):
        """五种异常的退出码必须互不相同, 便于脚本区分失败原因。"""
        codes = [
            ArgumentError.exit_code,
            InputFileError.exit_code,
            DecodeError.exit_code,
            OutputFileError.exit_code,
        ]
        self.assertEqual(len(codes), len(set(codes)))
        for error in (ArgumentError, InputFileError, DecodeError, OutputFileError):
            self.assertTrue(issubclass(error, PlagiarismError))


if __name__ == "__main__":
    unittest.main()
