"""生成器的约束与去重测试。"""

import unittest
from fractions import Fraction

from expression import DIV
from generator import DEFAULT_MAX_OPERATORS, Generator, GeneratorError, value_pool


def walk(expression):
    """按前序走一遍表达式树, 依次产出每个节点。"""
    yield expression
    if not expression.is_leaf:
        yield from walk(expression.left)
        yield from walk(expression.right)


class ValuePoolTest(unittest.TestCase):

    def test_contains_naturals_and_proper_fractions(self):
        pool = value_pool(4)
        self.assertIn(Fraction(0), pool)
        self.assertIn(Fraction(3), pool)
        self.assertIn(Fraction(1, 3), pool)
        self.assertIn(Fraction(2, 3), pool)

    def test_excludes_values_out_of_range(self):
        pool = value_pool(4)
        self.assertNotIn(Fraction(4), pool)     # 自然数要小于 4
        self.assertNotIn(Fraction(3, 4), pool)  # 分母也要小于 4
        self.assertNotIn(Fraction(4, 5), pool)

    def test_limit_one_only_gives_zero(self):
        self.assertEqual([Fraction(0)], value_pool(1))


class ConstraintTest(unittest.TestCase):
    """需求 3、4、5 对单道题的约束。"""

    def test_constraints_hold_for_many_problems(self):
        for limit in (2, 5, 10, 30):
            for problem in Generator(limit=limit, seed=limit).generate(200):
                self.assertLessEqual(problem.operator_count(), DEFAULT_MAX_OPERATORS)
                for node in walk(problem):
                    if node.is_leaf:
                        self.assertLess(node.value, limit)
                        if node.value.denominator > 1:
                            self.assertLess(node.value.denominator, limit)
                    else:
                        self.assertGreaterEqual(node.value, 0)  # 计算过程不出现负数
                        if node.op == DIV:
                            self.assertGreater(node.value, 0)
                            self.assertLess(node.value, 1)      # 商一定是真分数

    def test_division_never_divides_by_zero(self):
        for problem in Generator(limit=10, seed=13).generate(300):
            for node in walk(problem):
                if not node.is_leaf and node.op == DIV:
                    self.assertNotEqual(0, node.right.value)


class UniquenessTest(unittest.TestCase):

    def test_no_duplicate_problems(self):
        problems = Generator(limit=10, seed=7).generate(1000)
        keys = [problem.canonical() for problem in problems]
        self.assertEqual(len(keys), len(set(keys)))

    def test_count_matches_request(self):
        self.assertEqual(7, len(Generator(limit=10, seed=1).generate(7)))

    def test_same_seed_gives_the_same_problems(self):
        first = [str(p) for p in Generator(limit=10, seed=42).generate(20)]
        second = [str(p) for p in Generator(limit=10, seed=42).generate(20)]
        self.assertEqual(first, second)

    def test_ten_thousand_problems(self):
        # 需求 8: 一次运行要能造出一万道题
        problems = Generator(limit=10, seed=2026).generate(10000)
        self.assertEqual(10000, len(problems))
        self.assertEqual(10000, len({problem.canonical() for problem in problems}))

    def test_limit_one_still_works_for_small_counts(self):
        # -r 1 是允许的, 这时题目里只会出现 0
        problems = Generator(limit=1, seed=3).generate(20)
        self.assertEqual(20, len(problems))
        for problem in problems:
            self.assertEqual(Fraction(0), problem.evaluate())

    def test_range_too_small_is_reported(self):
        # 范围内凑不齐这么多不重复的题时, 应该报错而不是死循环
        with self.assertRaises(GeneratorError):
            Generator(limit=1, seed=5).generate(1000)

    def test_invalid_arguments_are_rejected(self):
        with self.assertRaises(ValueError):
            Generator(limit=0)
        with self.assertRaises(ValueError):
            Generator(limit=10).generate(0)
