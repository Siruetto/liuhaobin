"""批改功能的单元测试。"""

import os
import shutil
import tempfile
import unittest

from expression import parse_expression
from grading import grade
from records import write_exercises, write_grade


class GradingTest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.exercise_path = os.path.join(self.tmpdir, "Exercises.txt")
        self.answer_path = os.path.join(self.tmpdir, "Answers.txt")
        self.grade_path = os.path.join(self.tmpdir, "Grade.txt")
        problems = [
            parse_expression("1/6 + 1/8"),   # 7/24
            parse_expression("3 + 4 × 5"),   # 23
            parse_expression("1/2 + 7"),     # 15/2, 也就是 7'1/2
        ]
        write_exercises(self.exercise_path, problems)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_answers(self, texts):
        with open(self.answer_path, "w", encoding="utf-8") as handle:
            for index, text in enumerate(texts, start=1):
                handle.write("{}. {}\n".format(index, text))

    def _grade_lines(self):
        correct, wrong = grade(self.exercise_path, self.answer_path)
        write_grade(self.grade_path, correct, wrong)
        with open(self.grade_path, encoding="utf-8") as handle:
            return handle.read().splitlines()

    def test_all_correct(self):
        self._write_answers(["7/24", "23", "7'1/2"])
        correct, wrong = grade(self.exercise_path, self.answer_path)
        self.assertEqual([1, 2, 3], correct)
        self.assertEqual([], wrong)

    def test_wrong_answers_are_listed_by_number(self):
        self._write_answers(["7/24", "24", "7'1/2"])
        correct, wrong = grade(self.exercise_path, self.answer_path)
        self.assertEqual([1, 3], correct)
        self.assertEqual([2], wrong)

    def test_equivalent_answer_forms_are_accepted(self):
        # 14/48 就是 7/24, 46/2 就是 23, 15/2 就是 7'1/2
        self._write_answers(["14/48", "46/2", "15/2"])
        correct, wrong = grade(self.exercise_path, self.answer_path)
        self.assertEqual([1, 2, 3], correct)
        self.assertEqual([], wrong)

    def test_fullwidth_apostrophe_answer(self):
        # 题面用的是全角撇号, 别人交上来的答案可能就是这个写法
        self._write_answers(["7/24", "23", "7\u20191/2"])
        correct, wrong = grade(self.exercise_path, self.answer_path)
        self.assertEqual([1, 2, 3], correct)

    def test_grade_file_format(self):
        self._write_answers(["7/24", "24", "7'1/2"])
        lines = self._grade_lines()
        self.assertEqual("Correct: 2 (1, 3)", lines[0])
        self.assertEqual("Wrong: 1 (2)", lines[1])

    def test_empty_side_uses_empty_parentheses(self):
        self._write_answers(["7/24", "23", "7'1/2"])
        lines = self._grade_lines()
        self.assertEqual("Correct: 3 (1, 2, 3)", lines[0])
        self.assertEqual("Wrong: 0 ()", lines[1])

    def test_missing_answer_is_reported(self):
        self._write_answers(["7/24"])
        with self.assertRaises(ValueError):
            grade(self.exercise_path, self.answer_path)

    def test_broken_exercise_file_is_reported(self):
        with open(self.exercise_path, "w", encoding="utf-8") as handle:
            handle.write("这不是一行题目\n")
        self._write_answers(["1"])
        with self.assertRaises(ValueError):
            grade(self.exercise_path, self.answer_path)
