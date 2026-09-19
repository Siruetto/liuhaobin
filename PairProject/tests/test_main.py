"""命令行入口的集成测试。"""

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
        self.previous_cwd = os.getcwd()
        os.chdir(self.tmpdir)  # 程序把结果写在当前目录, 所以换到临时目录里跑

    def tearDown(self):
        os.chdir(self.previous_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main.main(argv)
        return code, out.getvalue(), err.getvalue()

    def _lines(self, name):
        with open(os.path.join(self.tmpdir, name), encoding="utf-8") as handle:
            return handle.read().splitlines()

    def test_generate_writes_exercises_and_answers(self):
        code, message, _ = self._run(["-n", "5", "-r", "10"])
        self.assertEqual(0, code)
        self.assertIn("Exercises.txt", message)
        exercises = self._lines("Exercises.txt")
        answers = self._lines("Answers.txt")
        self.assertEqual(5, len(exercises))
        self.assertEqual(5, len(answers))
        self.assertTrue(exercises[0].startswith("1. "))
        self.assertTrue(exercises[0].endswith(" ="))
        self.assertTrue(answers[0].startswith("1. "))

    def test_missing_range_prints_help(self):
        code, _, err = self._run(["-n", "5"])
        self.assertEqual(2, code)
        self.assertIn("参数错误", err)
        self.assertIn("-r", err)
        self.assertIn("示例", err)

    def test_missing_count_prints_help(self):
        code, _, err = self._run(["-r", "10"])
        self.assertEqual(2, code)
        self.assertIn("-n", err)

    def test_grading_end_to_end(self):
        self._run(["-n", "10", "-r", "10"])
        answers = self._lines("Answers.txt")
        answers[1] = "2. 1/1234567"  # 故意把第 2 题写错
        with open(os.path.join(self.tmpdir, "Answers.txt"), "w", encoding="utf-8") as handle:
            handle.write("\n".join(answers) + "\n")

        code, _, _ = self._run(["-e", "Exercises.txt", "-a", "Answers.txt"])
        self.assertEqual(0, code)
        grade_lines = self._lines("Grade.txt")
        self.assertEqual("Correct: 9 (1, 3, 4, 5, 6, 7, 8, 9, 10)", grade_lines[0])
        self.assertEqual("Wrong: 1 (2)", grade_lines[1])

    def test_grade_mode_rejects_generate_options(self):
        code, _, err = self._run(["-n", "5", "-e", "a.txt", "-a", "b.txt"])
        self.assertEqual(2, code)
        self.assertIn("批改", err)

    def test_help_exits_with_zero(self):
        with self.assertRaises(SystemExit) as context:
            main.main(["-h"])
        self.assertEqual(0, context.exception.code)

    def test_missing_input_file_reports_error(self):
        code, _, err = self._run(["-e", "no_such_file.txt", "-a", "no_such_file.txt"])
        self.assertEqual(1, code)
        self.assertIn("错误", err)
