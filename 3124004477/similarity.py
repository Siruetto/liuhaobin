"""计算模块: 文本归一化与最长公共子序列(LCS)。

重复率采用最长公共子序列的 Dice 系数:

    rate = 2 * LCS(原文, 抄袭版) / (len(原文) + len(抄袭版)) * 100

抄袭版是在原文上"增删改"得到的, 增、删、改都会让 LCS 变小, 从而让重复率下降;
分母同时用两篇的长度, 可以避免"抄袭版拼接大量无关内容"时重复率仍逼近 100%。

第一版先用教科书上的二维动态规划把结果算对, 性能问题留到后续版本再优化。
"""


def normalize(text):
    """去掉所有空白字符(空格、制表符、换行、全角空格)。

    论文排版时的换行、缩进属于格式而不是内容, 归一化后可以避免
    "同一段话因为换行位置不同而被判成不同"。
    """
    return "".join(text.split())


def lcs_length(first, second):
    """返回两个字符串的最长公共子序列长度(二维动态规划)。"""
    rows, cols = len(first), len(second)
    table = [[0] * (cols + 1) for _ in range(rows + 1)]
    for i in range(1, rows + 1):
        for j in range(1, cols + 1):
            if first[i - 1] == second[j - 1]:
                table[i][j] = table[i - 1][j - 1] + 1
            else:
                table[i][j] = max(table[i - 1][j], table[i][j - 1])
    return table[rows][cols]


def duplication_rate(original_text, copied_text):
    """返回抄袭版相对于原文的重复率(百分数, 0 ~ 100)。"""
    original = normalize(original_text)
    copied = normalize(copied_text)
    total = len(original) + len(copied)
    if total == 0:
        return 100.0
    return 200.0 * lcs_length(original, copied) / total


def format_rate(rate):
    """把重复率格式化成"精确到小数点后两位"的字符串。"""
    return "{:.2f}".format(rate)
