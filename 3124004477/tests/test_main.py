"""命令行入口的集成测试: 正常路径 + 四类异常 + "不碰其他文件"。"""

import contextlib
import io
import os
import shutil
import tempfile
import unittest

import main


class MainTest(unittest.TestCase):

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

    def _read_answer(self):
        with open(self.answer, "r", encoding="utf-8") as handle:
            return handle.read()

    def test_end_to_end_writes_two_decimals(self):
        code, message = self._run([self.original, self.copied, self.answer])
        self.assertEqual(0, code)
        self.assertEqual("", message)
        self.assertEqual("80.95", self._read_answer())

    def test_only_the_answer_file_is_created(self):
        self._run([self.original, self.copied, self.answer])
        self.assertEqual(
            ["ans.txt", "orig.txt", "orig_add.txt"], sorted(os.listdir(self.tmpdir))
        )

    def test_wrong_argument_count_exits_with_code_2(self):
        for argv in ([], [self.original], [self.original, self.copied], ["a", "b", "c", "d"]):
            code, message = self._run(argv)
            self.assertEqual(2, code)
            self.assertIn("用法", message)

    def test_missing_original_exits_with_code_3(self):
        code, message = self._run(
            [os.path.join(self.tmpdir, "ghost.txt"), self.copied, self.answer]
        )
        self.assertEqual(3, code)
        self.assertIn("ghost.txt", message)

    def test_missing_copied_exits_with_code_3(self):
        code, _ = self._run([self.original, os.path.join(self.tmpdir, "ghost.txt"), self.answer])
        self.assertEqual(3, code)

    def test_unwritable_answer_path_exits_with_code_5(self):
        code, message = self._run(
            [self.original, self.copied, os.path.join(self.tmpdir, "no_dir", "ans.txt")]
        )
        self.assertEqual(5, code)
        self.assertIn("答案文件", message)

    def test_gbk_input_is_supported(self):
        gbk_copied = self._write("gbk_add.txt", "今天是周天，天气晴朗，我晚上要去看电影。", "gb18030")
        code, _ = self._run([self.original, gbk_copied, self.answer])
        self.assertEqual(0, code)
        self.assertEqual("80.95", self._read_answer())

    def test_identical_files_score_one_hundred(self):
        code, _ = self._run([self.original, self.original, self.answer])
        self.assertEqual(0, code)
        self.assertEqual("100.00", self._read_answer())


if __name__ == "__main__":
    unittest.main()
