"""题目生成: 随机造题, 并保证满足作业里的各项约束。

约束来自题目要求:

1. 题目中出现的数值(自然数、真分数的分子和分母)都小于 ``-r`` 给出的范围;
2. 任何形如 e1 − e2 的子式, 结果不能是负数;
3. 任何形如 e1 ÷ e2 的子式, 结果必须是真分数(0 < 商 < 1);
4. 每道题的运算符个数不超过 3;
5. 两道题如果只通过交换 + 和 × 的左右子式就能变成同一道题, 就算重复。
"""

import random
from fractions import Fraction

from expression import ADD, DIV, MUL, SUB, Expression

DEFAULT_MAX_OPERATORS = 3

# 连续这么多次都撞上重复题, 就认为范围内的题已经出完了
_MAX_CONSECUTIVE_REPEATS = 20000


class GeneratorError(Exception):
    """造不出这么多不重复的题目(通常是 -r 给得太小)。"""


def value_pool(limit):
    """列出取值范围 [0, limit) 内允许出现的所有数值。

    包括自然数 0, 1, ..., limit-1, 以及分母小于 limit 的真分数。
    """
    values = [Fraction(number) for number in range(limit)]
    for denominator in range(2, limit):
        for numerator in range(1, denominator):
            values.append(Fraction(numerator, denominator))
    return values


class Generator:
    """按范围随机造题, 并在内部记下已出过的题, 保证不重复。"""

    def __init__(self, limit, max_operators=DEFAULT_MAX_OPERATORS, seed=None):
        if limit < 1:
            raise ValueError("范围 -r 必须是不小于 1 的自然数")
        self.limit = limit
        self.max_operators = max_operators
        self.values = value_pool(limit)
        self.random = random.Random(seed)
        self._seen = set()

    def generate(self, count):
        """造出 count 道互不重复的题目, 返回表达式列表。

        一直撞重复就说明范围内的题差不多出完了, 这时抛 GeneratorError,
        而不是无限循环下去。
        """
        if count < 1:
            raise ValueError("题目个数 -n 必须是正整数")
        problems = []
        repeats = 0
        while len(problems) < count:
            expression = self.random_expression()
            key = expression.canonical()
            if key in self._seen:
                repeats += 1
                if repeats > _MAX_CONSECUTIVE_REPEATS:
                    raise GeneratorError(
                        "在 -r {} 的范围内凑不齐 {} 道不重复的题目, 请把 -r 调大"
                        .format(self.limit, count)
                    )
                continue
            repeats = 0
            self._seen.add(key)
            problems.append(expression)
        return problems

    def random_expression(self):
        """随机造一道题(运算符个数 1 ~ max_operators)。"""
        return self._build(self.random.randint(1, self.max_operators))[0]

    def _build(self, operators):
        """造一棵恰好 operators 个运算符的表达式, 返回 (表达式, 值)。"""
        if operators == 0:
            value = self.random.choice(self.values)
            return Expression.number(value), value
        left_count = self.random.randrange(operators)
        right_count = operators - 1 - left_count
        left, left_value = self._build(left_count)
        right, right_value = self._build(right_count)
        return self._combine(left, left_value, right, right_value)

    def _combine(self, left, left_value, right, right_value):
        """先看两个子式的值, 再从"可行的运算符"里随机挑一个。

        这样挑出来的运算符天然满足约束, 不需要事后反复重试:
        加和乘永远可行; 减法只在左不小于右时给出; 除法只在交换后能得到
        真分数(0 < 商 < 1)时给出。
        """
        smaller, larger = sorted((left_value, right_value))
        choices = [ADD, MUL]
        if left_value >= right_value:
            choices.append(SUB)
        if 0 < smaller < larger:
            choices.append(DIV)

        op = self.random.choice(choices)
        if op == DIV and left_value > right_value:
            left, right = right, left  # 让小的当被除数, 商才是真分数
        expression = Expression.binary(op, left, right)
        return expression, expression.value
