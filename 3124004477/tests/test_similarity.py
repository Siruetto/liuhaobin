"""计算模块的单元测试(白盒 + 边界 + 随机对照)。

期望值全部由测试文件内独立的朴素 DP 参考实现推导后写死,
不使用被测函数自己算期望值, 避免"自己测自己"。
"""

import random
import unittest

import similarity


def reference_lcs(first, second):
    """教科书式的二维 DP, 只做对照用, 不参与产品代码。"""
    if len(first) < len(second):
        first, second = second, first
    previous = [0] * (len(second) + 1)
    for char in first:
        current = [0] * (len(second) + 1)
        for index in range(1, len(second) + 1):
            if char == second[index - 1]:
                current[index] = previous[index - 1] + 1
            else:
                current[index] = max(previous[index], current[index - 1])
        previous = current
    return previous[-1]


class NormalizeTest(unittest.TestCase):
    """归一化: 空白字符不应该影响查重结果。"""

    def test_removes_spaces_tabs_newlines_and_fullwidth_space(self):
        text = "a b\tc\nd\r\n\u3000e"
        self.assertEqual("abcde", similarity.normalize(text))

    def test_keeps_punctuation(self):
        self.assertEqual("今天。", similarity.normalize(" 今天。 "))


class LcsLengthTest(unittest.TestCase):
    """LCS 长度: 位并行实现必须与朴素 DP 完全一致。"""

    def test_empty_inputs(self):
        self.assertEqual(0, similarity.lcs_length("", ""))
        self.assertEqual(0, similarity.lcs_length("abc", ""))
        self.assertEqual(0, similarity.lcs_length("", "abc"))

    def test_identical_single_character(self):
        self.assertEqual(1, similarity.lcs_length("a", "a"))
        self.assertEqual(0, similarity.lcs_length("a", "b"))

    def test_order_matters(self):
        # abcd 与 dcba 的最长公共子序列是单个字符
        self.assertEqual(1, similarity.lcs_length("abcd", "dcba"))

    def test_is_symmetric(self):
        self.assertEqual(
            similarity.lcs_length("abcdef", "azced"),
            similarity.lcs_length("azced", "abcdef"),
        )

    def test_matches_plain_dp_on_random_inputs(self):
        random.seed(20260911)
        for _ in range(200):
            alphabet = "abc" if _ % 2 else "abcdefgh"
            first = "".join(random.choice(alphabet) for _ in range(random.randint(0, 20)))
            second = "".join(random.choice(alphabet) for _ in range(random.randint(0, 24)))
            self.assertEqual(
                reference_lcs(first, second),
                similarity.lcs_length(first, second),
                msg="不一致: {!r} vs {!r}".format(first, second),
            )

    def test_matches_plain_dp_on_chinese_text(self):
        original = "今天是星期天，天气晴，今天晚上我要去看电影。"
        copied = "今天是周天，天气晴朗，我晚上要去看电影。"
        self.assertEqual(
            reference_lcs(original, copied), similarity.lcs_length(original, copied)
        )


class DuplicationRateTest(unittest.TestCase):
    """重复率: 覆盖完全相同 / 完全不同 / 增 / 删 / 改 / 空文档。"""

    def test_identical_documents_are_one_hundred_percent(self):
        self.assertAlmostEqual(
            100.0, similarity.duplication_rate("论文查重", "论文查重"), places=6
        )

    def test_disjoint_documents_are_zero_percent(self):
        self.assertAlmostEqual(0.0, similarity.duplication_rate("abc", "xyz"), places=6)

    def test_empty_copy_scores_zero(self):
        self.assertAlmostEqual(0.0, similarity.duplication_rate("abc", ""), places=6)

    def test_empty_original_scores_zero(self):
        self.assertAlmostEqual(0.0, similarity.duplication_rate("", "abc"), places=6)

    def test_both_empty_is_defined_as_identical(self):
        self.assertAlmostEqual(100.0, similarity.duplication_rate("", ""), places=6)

    def test_whitespace_only_differences_are_ignored(self):
        original = "今天是星期天，天气晴，\n今天晚上我要去看电影。"
        copied = "今天是星期天，天气晴，今天晚上我要去看电影。"
        self.assertAlmostEqual(100.0, similarity.duplication_rate(original, copied), places=6)

    def test_sample_pair_from_the_specification(self):
        original = "今天是星期天，天气晴，今天晚上我要去看电影。"
        copied = "今天是周天，天气晴朗，我晚上要去看电影。"
        # LCS = 17, len = 22 + 20 -> 2 * 17 / 42 = 80.952...%
        self.assertAlmostEqual(80.95238095238095, similarity.duplication_rate(original, copied))

    def test_insertion_only(self):
        # LCS = 10, len = 10 + 15 -> 80.00%
        self.assertAlmostEqual(80.0, similarity.duplication_rate("abcdefghij", "abcdefghijABCDE"))

    def test_deletion_only(self):
        # LCS = 10, len = 20 + 10 -> 66.66...%
        self.assertAlmostEqual(
            66.66666666666667,
            similarity.duplication_rate("0123456789ABCDEFGHIJ", "0123456789"),
        )

    def test_modification_only(self):
        # LCS = 8, len = 10 + 10 -> 80.00%
        self.assertAlmostEqual(80.0, similarity.duplication_rate("abcdefghij", "abXdefghYj"))

    def test_reversed_words_drop_the_rate(self):
        # LCS = 1, len = 4 + 4 -> 25.00%
        self.assertAlmostEqual(25.0, similarity.duplication_rate("abcd", "dcba"))

    def test_rate_stays_inside_zero_to_one_hundred(self):
        random.seed(1)
        for _ in range(100):
            first = "".join(random.choice("论文查重测试") for _ in range(random.randint(0, 30)))
            second = "".join(random.choice("论文查重测试") for _ in range(random.randint(0, 30)))
            rate = similarity.duplication_rate(first, second)
            self.assertGreaterEqual(rate, 0.0)
            self.assertLessEqual(rate, 100.0)


class FormatRateTest(unittest.TestCase):
    """输出格式: 必须是保留两位小数的浮点数。"""

    def test_rounds_to_two_decimals(self):
        self.assertEqual("80.95", similarity.format_rate(80.95238095238095))

    def test_keeps_zero_decimals(self):
        self.assertEqual("100.00", similarity.format_rate(100.0))
        self.assertEqual("0.00", similarity.format_rate(0.0))
