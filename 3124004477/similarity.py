"""计算模块: 文本归一化、最长公共子序列(LCS)与重复率。

算法要点
--------
1. 重复率采用"最长公共子序列"的 Dice 系数:

       rate = 2 * LCS(原文, 抄袭版) / (len(原文) + len(抄袭版)) * 100

   抄袭版是在原文上"增删改"得到的, 增、删、改都会使 LCS 变小,
   因此分子分母同时变化能让重复率单调地反映"抄了多少"。
   用两个长度之和归一化(而不是只用原文长度), 可以避免"抄袭版
   无脑拼接大量无关内容"时重复率仍逼近 100% 的失真。

2. LCS 长度使用位并行(Bit-Parallel)算法: 把较短串看作模式串, 每个
   字符对应一个大整数的位掩码, 用整数加减与移位一次推进整个 DP 列。
   复杂度 O(n * m / w), 内存 O(m / w), 比教科书上的二维 DP 快一到
   两个数量级, 大论文也能满足评测的 5 秒限制。
"""


def normalize(text):
    """去掉所有空白字符(空格、制表符、换行、全角空格)。

    论文在排版时换行、缩进是格式而不是内容, 归一化后可以避免
    "同一段话因为换行位置不同而被判为不同"。
    """
    return "".join(text.split())


def _build_masks(pattern):
    """把模式串中每个字符出现的位置编码成位掩码。"""
    masks = {}
    for index, char in enumerate(pattern):
        masks[char] = masks.get(char, 0) | (1 << index)
    return masks


def lcs_length(first, second):
    """返回两个字符串的最长公共子序列长度(位并行实现)。

    参数为原始字符串, 内部不做归一化, 便于单元测试逐位对照。
    """
    if len(first) > len(second):
        first, second = second, first  # 短串做模式串, 位宽取短的
    pattern = first
    text = second
    pattern_len = len(pattern)
    if pattern_len == 0:
        return 0

    masks = _build_masks(pattern)
    full_mask = (1 << pattern_len) - 1
    vector = full_mask  # V 向量, 初值全 1
    for char in text:
        match = masks.get(char, 0)
        overlap = vector & match
        vector = ((vector + overlap) | (vector - overlap)) & full_mask
    # V 中 0 的个数就是 LCS 长度
    return pattern_len - bin(vector).count("1")


def duplication_rate(original_text, copied_text):
    """返回抄袭版相对于原文的重复率(百分数, 0 ~ 100)。

    输入是两篇文档的原始文本, 函数内部先做归一化;
    两篇都为空时定义为完全一致, 返回 100.0。
    """
    original = normalize(original_text)
    copied = normalize(copied_text)
    total = len(original) + len(copied)
    if total == 0:
        return 100.0
    return 200.0 * lcs_length(original, copied) / total


def format_rate(rate):
    """把重复率格式化成"精确到小数点后两位"的字符串。"""
    return "{:.2f}".format(rate)
