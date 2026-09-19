"""边界与错误处理的补充测试: 覆盖主干用例没走到的分支。"""

import contextlib
import io
import os
import shutil
import tempfile
import unittest
from fractions import Fraction

import main
import number_text
from expression import Expression
from records import read_answers, read_exercises


class ExpressionEdgeTest(unittest.TestCase):

    def test_unknown_operator_is_rejected(self):
        with self.assertRaises(ValueError):
            Expression.binary("^", Expression.number(1), Expression.number(2))

    def test_single_number_expression_can_be_printed(self):
        # 只含一个数的表达式(0 个运算符)也要能打印, 对应语法里的 e = n
        self.assertEqual("3/5", str(Expression.number(Fraction(3, 5))))


class NumberTextEdgeTest(unittest.TestCase):

    def test_negative_number_can_be_parsed(self):
        # 程序自己不会输出负数, 但别人交上来的答案里可能有, 解析时不能崩
        self.assertEqual(Fraction(-3, 5), number_text.parse_number("-3/5"))


class RecordEdgeTest(unittest.TestCase):

    def test_blank_lines_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exercise_path = os.path.join(tmpdir, "Exercises.txt")
            with open(exercise_path, "w", encoding="utf-8") as handle:
                handle.write("\n\n1. 1 + 2 =\n\n2. 3 × 4 =\n")
            entries = read_exercises(exercise_path)
            self.assertEqual([1, 2], [number for number, _expression in entries])

            answer_path = os.path.join(tmpdir, "Answers.txt")
            with open(answer_path, "w", encoding="utf-8") as handle:
                handle.write("1. 3\n\n2. 12\n")
            self.assertEqual(
                {1: Fraction(3), 2: Fraction(12)}, read_answers(answer_path)
            )


class CliErrorTest(unittest.TestCase):
    """命令行里几种参数错误的分支。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.previous_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.previous_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main.main(argv)
        return code, err.getvalue()

    def test_zero_count_is_rejected(self):
        code, err = self._run(["-n", "0", "-r", "10"])
        self.assertEqual(2, code)
        self.assertIn("正整数", err)

    def test_zero_range_is_rejected(self):
        code, err = self._run(["-n", "5", "-r", "0"])
        self.assertEqual(2, code)
        self.assertIn("不小于 1", err)

    def test_exercise_without_answer_is_rejected(self):
        code, err = self._run(["-e", "Exercises.txt"])
        self.assertEqual(2, code)
        self.assertIn("-a", err)

    def test_range_too_small_reports_error(self):
        # -r 1 时题目里只能出现 0, 凑不出 1000 道不重复的题
        code, err = self._run(["-n", "1000", "-r", "1"])
        self.assertEqual(1, code)
        self.assertIn("凑不齐", err)
