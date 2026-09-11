"""文件读写: 读取原文与抄袭版, 写出答案。"""

from similarity import format_rate


def read_text(path):
    """读取文本文件(UTF-8)。"""
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write_rate(path, rate):
    """把重复率写入答案文件, 只写数字, 精确到小数点后两位。"""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(format_rate(rate))
