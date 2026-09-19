"""表达式求值、文本输出与判重的单元测试。"""

import unittest
from fractions import Fraction

from expression import ADD, DIV, MUL, SUB, Expression, parse_expression


def number(value):
    return Expression.number(Fraction(value))


class EvaluateTest(unittest.TestCase):

    def test_integer_arithmetic(self):
        expression = Expression.binary(
            ADD, number(3), Expression.binary(MUL, number(4), number(5))
        )
        self.assertEqual(Fraction(23), expression.evaluate())

    def test_fraction_addition_from_the_spec(self):
        # 题面给的例子: 1/6 + 1/8 = 7/24
        expression = Expression.binary(ADD, number(Fraction(1, 6)), number(Fraction(1, 8)))
        self.assertEqual(Fraction(7, 24), expression.evaluate())

    def test_division_is_exact(self):
        expression = Expression.binary(DIV, number(Fraction(1, 2)), number(Fraction(3, 4)))
        self.assertEqual(Fraction(2, 3), expression.evaluate())

    def test_division_by_zero_is_rejected(self):
        with self.assertRaises(ZeroDivisionError):
            Expression.binary(DIV, number(1), number(0))


class RenderTest(unittest.TestCase):

    def test_lower_precedence_child_gets_parentheses(self):
        expression = Expression.binary(
            MUL, Expression.binary(ADD, number(1), number(2)), number(3)
        )
        self.assertEqual("(1 + 2) × 3", str(expression))

    def test_left_associative_chain_has_no_parentheses(self):
        expression = Expression.binary(
            ADD, Expression.binary(ADD, number(1), number(2)), number(3)
        )
        self.assertEqual("1 + 2 + 3", str(expression))

    def test_right_child_with_same_precedence_gets_parentheses(self):
        expression = Expression.binary(
            SUB, number(5), Expression.binary(SUB, number(3), number(1))
        )
        self.assertEqual("5 − (3 − 1)", str(expression))

    def test_fraction_and_mixed_number_text(self):
        expression = Expression.binary(ADD, number(Fraction(1, 2)), number(Fraction(19, 8)))
        self.assertEqual("1/2 + 2'3/8", str(expression))


class CanonicalTest(unittest.TestCase):
    """判重规则: 只允许交换 + 和 × 的左右子式。"""

    def test_addition_is_commutative(self):
        left = Expression.binary(ADD, number(23), number(45))
        right = Expression.binary(ADD, number(45), number(23))
        self.assertEqual(left.canonical(), right.canonical())

    def test_multiplication_is_commutative(self):
        left = Expression.binary(MUL, number(6), number(8))
        right = Expression.binary(MUL, number(8), number(6))
        self.assertEqual(left.canonical(), right.canonical())

    def test_subtraction_is_not_commutative(self):
        left = Expression.binary(SUB, number(5), number(3))
        right = Expression.binary(SUB, number(3), number(5))
        self.assertNotEqual(left.canonical(), right.canonical())

    def test_three_addends_with_same_structure_are_equivalent(self):
        # 题面说 3+(2+1) 和 1+2+3 是同一道题
        left = Expression.binary(ADD, number(3), Expression.binary(ADD, number(2), number(1)))
        right = Expression.binary(ADD, Expression.binary(ADD, number(1), number(2)), number(3))
        self.assertEqual(left.canonical(), right.canonical())

    def test_different_addend_structures_are_not_equivalent(self):
        # 题面说 1+2+3 和 3+2+1 不是同一道题
        left = Expression.binary(ADD, Expression.binary(ADD, number(1), number(2)), number(3))
        right = Expression.binary(ADD, Expression.binary(ADD, number(3), number(2)), number(1))
        self.assertNotEqual(left.canonical(), right.canonical())

    def test_different_operators_are_not_confused(self):
        left = Expression.binary(ADD, Expression.binary(MUL, number(2), number(3)), number(4))
        right = Expression.binary(MUL, number(2), Expression.binary(ADD, number(3), number(4)))
        self.assertNotEqual(left.canonical(), right.canonical())


class ParseTest(unittest.TestCase):

    def test_parse_and_evaluate(self):
        self.assertEqual(Fraction(7, 24), parse_expression("1/6 + 1/8").evaluate())

    def test_parse_with_parentheses(self):
        self.assertEqual(Fraction(9), parse_expression("(1 + 2) × 3").evaluate())

    def test_parse_accepts_ascii_operators(self):
        self.assertEqual(Fraction(5), parse_expression("10 - 5").evaluate())
        self.assertEqual(Fraction(3), parse_expression("9 / 3").evaluate())

    def test_parse_then_render_keeps_the_structure(self):
        for text in ("1 + 2 + 3", "5 − (3 − 1)", "(1 + 2) × 3", "8 ÷ (2 + 2)"):
            self.assertEqual(text, str(parse_expression(text)))

    def test_parse_rejects_broken_input(self):
        for text in ("1 +", "1 + 2)", "(1 + 2", "1 $ 2"):
            with self.assertRaises(ValueError):
                parse_expression(text)

    def test_operator_count(self):
        self.assertEqual(0, parse_expression("3").operator_count())
        self.assertEqual(3, parse_expression("1 + 2 × 3 ÷ 4").operator_count())
