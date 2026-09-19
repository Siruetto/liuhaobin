"""分数与文本之间的转换。

题目规定了真分数的写法: 五分之三写成 ``3/5``, 二又八分之三写成 ``2'3/8``。
题面里用的是全角撇号 ``’``, 为了兼容两种写法, 解析时半角和全角都接受,
输出时统一用半角撇号。
"""

import re
from fractions import Fraction

# 带分数的分隔符: 半角撇号、全角撇号、全角单引号
MIXED_SEPARATORS = ("'", "\u2019", "\uff07")

_MIXED_RE = re.compile(r"^(\d+)['\u2019\uff07](\d+)/(\d+)$")
_FRACTION_RE = re.compile(r"^(\d+)/(\d+)$")
_INTEGER_RE = re.compile(r"^\d+$")


def format_number(value):
    """把分数写成题目要求的文本: ``3``、``3/5``、``2'3/8``。"""
    if value.denominator == 1:
        return str(value.numerator)
    sign = "-" if value < 0 else ""
    numerator = abs(value.numerator)
    if numerator < value.denominator:
        return "{}{}/{}".format(sign, numerator, value.denominator)
    whole, remainder = divmod(numerator, value.denominator)
    return "{}{}'{}/{}".format(sign, whole, remainder, value.denominator)


def parse_number(text):
    """把 ``3``、``3/5``、``2'3/8`` 这样的文本解析成分数。

    格式不合法时抛出 ValueError, 由调用方决定怎么处理。
    """
    cleaned = "".join(text.split())
    if not cleaned:
        raise ValueError("答案为空")
    sign = 1
    if cleaned.startswith("-"):
        sign, cleaned = -1, cleaned[1:]

    mixed = _MIXED_RE.match(cleaned)
    if mixed:
        whole, numerator, denominator = (int(part) for part in mixed.groups())
        _check_denominator(denominator)
        return sign * Fraction(whole * denominator + numerator, denominator)

    fraction = _FRACTION_RE.match(cleaned)
    if fraction:
        numerator, denominator = (int(part) for part in fraction.groups())
        _check_denominator(denominator)
        return sign * Fraction(numerator, denominator)

    if _INTEGER_RE.match(cleaned):
        return sign * Fraction(int(cleaned))

    raise ValueError("无法解析的数值: {!r}".format(text))


def _check_denominator(denominator):
    if denominator == 0:
        raise ValueError("分母不能为 0")
