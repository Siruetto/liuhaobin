"""文件输入输出: 只读命令行给出的两个输入文件, 只写一个答案文件。"""

import os

from errors import DecodeError, InputFileError, OutputFileError
from similarity import format_rate

# 中文论文常见的两种编码; utf-8-sig 同时兼容带 BOM 与不带 BOM 的 UTF-8
SUPPORTED_ENCODINGS = ("utf-8-sig", "gb18030")


def read_text(path):
    """按 utf-8 / gb18030 依次尝试读取文本文件。

    读取失败时抛出 InputFileError; 编码都不匹配时抛出 DecodeError。
    """
    if not os.path.exists(path):
        raise InputFileError("输入文件不存在: {}".format(path))
    if not os.path.isfile(path):
        raise InputFileError("输入路径不是普通文件: {}".format(path))

    for encoding in SUPPORTED_ENCODINGS:
        try:
            with open(path, "r", encoding=encoding) as handle:
                return handle.read()
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            raise InputFileError("输入文件无法读取: {} ({})".format(path, exc))
    raise DecodeError(
        "输入文件编码不受支持(仅支持 utf-8 / gb18030): {}".format(path)
    )


def write_rate(path, rate):
    """把重复率写入答案文件。

    写入的是百分数形式的数字本身, 保留两位小数, 例如 89.12。
    不加百分号, 也不写别的文字: 答案文件要求是浮点型,
    混入其它字符会让评测方无法解析。
    """
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(format_rate(rate))
    except OSError as exc:
        raise OutputFileError("答案文件无法写入: {} ({})".format(path, exc))
