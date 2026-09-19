"""算术表达式: 求值、输出成题目文本、以及判重用的规范形式。

表达式是一棵二叉树:

* 叶子节点保存一个数值(自然数或真分数);
* 内部节点保存运算符和左右子树。

内部节点的值在构造时就按分数精确算好, 所以整个生成过程不碰浮点,
不会出现 1/3 变成 0.333333 这种误差。

同一个模块还负责把题目文本解析回表达式树, 批改时要用它算出标准答案。
"""

import re
from fractions import Fraction

from number_text import format_number, parse_number

ADD = "+"
SUB = "\u2212"  # 减号
MUL = "\u00d7"  # 乘号
DIV = "\u00f7"  # 除号

PRECEDENCE = {ADD: 1, SUB: 1, MUL: 2, DIV: 2}
COMMUTATIVE = (ADD, MUL)

# 判重时要把规范形式排序, 用一个稳定的运算符编号代替字符串比较
_OP_CODE = {ADD: 0, SUB: 1, MUL: 2, DIV: 3}

# 一个数值写成: 3、3/5、2'3/8(撇号半角全角都收)
_NUMBER_PATTERN = r"\d+(?:['\u2019\uff07]\d+/\d+|/\d+)?"
_TOKEN_RE = re.compile(
    "({}|[()+*/×÷]|[-\u2212])".format(_NUMBER_PATTERN)
)


class Expression:
    """表达式节点: ``op`` 为 None 时是叶子, 否则是"左 op 右"。"""

    __slots__ = ("op", "left", "right", "value")

    def __init__(self, op=None, left=None, right=None, value=None):
        self.op = op
        self.left = left
        self.right = right
        self.value = value

    @staticmethod
    def number(value):
        """造一个叶子节点。"""
        return Expression(value=Fraction(value))

    @staticmethod
    def binary(op, left, right):
        """造一个内部节点, 并顺手把它的值算出来。"""
        if op == ADD:
            value = left.value + right.value
        elif op == SUB:
            value = left.value - right.value
        elif op == MUL:
            value = left.value * right.value
        elif op == DIV:
            if right.value == 0:
                raise ZeroDivisionError("除数不能为 0")
            value = left.value / right.value
        else:
            raise ValueError("未知运算符: {!r}".format(op))
        return Expression(op, left, right, value)

    @property
    def is_leaf(self):
        return self.op is None

    def evaluate(self):
        """返回表达式的精确值(Fraction)。"""
        return self.value

    def operator_count(self):
        """返回表达式中运算符的个数。"""
        if self.is_leaf:
            return 0
        return 1 + self.left.operator_count() + self.right.operator_count()

    def __str__(self):
        """输出成题目里的写法, 只在必要的地方加括号。

        规则是标准的: 优先级低的子式要加括号, 右子式与父节点同优先级时也要加,
        因为 + − × ÷ 都是左结合的。这样"打印出来再读回去"能还原出同一棵树。
        """
        if self.is_leaf:
            return format_number(self.value)
        return "{} {} {}".format(
            self._child_text(self.left, is_right=False),
            self.op,
            self._child_text(self.right, is_right=True),
        )

    def _child_text(self, child, is_right):
        if child.is_leaf:
            return format_number(child.value)
        needs_parens = PRECEDENCE[child.op] < PRECEDENCE[self.op] or (
            PRECEDENCE[child.op] == PRECEDENCE[self.op] and is_right
        )
        return "({})".format(child) if needs_parens else str(child)

    def canonical(self):
        """返回判重用的规范形式(可哈希)。

        题目规定: 两道题如果只通过交换 + 和 × 的左右子式就能变成同一个式子,
        那它们算重复。所以这里在 + 和 × 节点上把两个子式的规范形式排序,
        − 和 ÷ 不允许交换, 保持原顺序。

        规范形式用嵌套元组表示, 而不是拼字符串:

        * 叶子 -> ``(0, 分子, 分母)``
        * 内部节点 -> ``(1, 运算符编号, 左, 右)``

        元组比较和哈希都比字符串快得多(实测快 3 倍), 而判重结果完全一样。
        """
        if self.is_leaf:
            value = self.value
            return (0, value.numerator, value.denominator)
        left = self.left.canonical()
        right = self.right.canonical()
        if self.op in COMMUTATIVE and right < left:
            left, right = right, left
        return (1, _OP_CODE[self.op], left, right)


def parse_expression(text):
    """把题目文本解析成表达式树。

    支持题目规定的写法(运算符和括号前后可以有空格), 也接受 ASCII 的 ``- * /``。
    """
    return _Parser(_tokenize(text)).parse()


def _tokenize(text):
    """把题目文本切成记号: 数值、运算符、括号。"""
    return [token for token in _TOKEN_RE.findall(text) if token.strip()]


class _Parser:
    """递归下降: 表达式 -> 项 -> 因子, 与运算符的优先级一一对应。"""

    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def parse(self):
        """解析出一个完整表达式, 并确认没有多余内容。"""
        node = self.parse_expression()
        if self.position != len(self.tokens):
            raise ValueError(
                "表达式末尾有多余内容: {}".format(" ".join(self.tokens[self.position:]))
            )
        return node

    def parse_expression(self):
        node = self.parse_term()
        while self._peek() in (ADD, SUB, "-"):
            op = ADD if self._next() == ADD else SUB
            node = Expression.binary(op, node, self.parse_term())
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self._peek() in (MUL, DIV, "*", "/"):
            token = self._next()
            op = MUL if token in (MUL, "*") else DIV
            node = Expression.binary(op, node, self.parse_factor())
        return node

    def parse_factor(self):
        token = self._next()
        if token is None:
            raise ValueError("表达式不完整")
        if token == "(":
            node = self.parse_expression()
            if self._next() != ")":
                raise ValueError("括号不匹配")
            return node
        return Expression.number(parse_number(token))

    def _peek(self):
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def _next(self):
        token = self._peek()
        if token is not None:
            self.position += 1
        return token
