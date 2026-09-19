"""分数文本格式的单元测试。"""

import unittest
from fractions import Fraction

import number_text


class FormatNumberTest(unittest.TestCase):

    def test_integer(self):
        self.assertEqual("3", number_text.format_number(Fraction(3)))
        self.assertEqual("0", number_text.format_number(Fraction(0)))

    def test_proper_fraction(self):
        self.assertEqual("3/5", number_text.format_number(Fraction(3, 5)))

    def test_mixed_number(self):
        # 二又八分之三写成 2'3/8
        self.assertEqual("2'3/8", number_text.format_number(Fraction(19, 8)))

    def test_fraction_is_reduced(self):
        self.assertEqual("1/2", number_text.format_number(Fraction(2, 4)))


class ParseNumberTest(unittest.TestCase):

    def test_parse_integer(self):
        self.assertEqual(Fraction(7), number_text.parse_number("7"))

    def test_parse_proper_fraction(self):
        self.assertEqual(Fraction(3, 5), number_text.parse_number("3/5"))

    def test_parse_mixed_number_with_ascii_apostrophe(self):
        self.assertEqual(Fraction(19, 8), number_text.parse_number("2'3/8"))

    def test_parse_mixed_number_with_fullwidth_apostrophe(self):
        # 题面里写的是全角撇号, 也要能读
        self.assertEqual(Fraction(19, 8), number_text.parse_number("2\u20193/8"))

    def test_roundtrip(self):
        values = [Fraction(0), Fraction(7), Fraction(3, 5), Fraction(19, 8), Fraction(61, 40)]
        for value in values:
            self.assertEqual(
                value, number_text.parse_number(number_text.format_number(value))
            )

    def test_reject_bad_text(self):
        for text in ("", "abc", "1/", "/2", "2'3"):
            with self.assertRaises(ValueError):
                number_text.parse_number(text)

    def test_reject_zero_denominator(self):
        with self.assertRaises(ValueError):
            number_text.parse_number("1/0")
