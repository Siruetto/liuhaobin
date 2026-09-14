"""论文查重命令行入口。

用法::

    python main.py <原文文件> <抄袭版论文文件> <答案文件>

三个参数都是文件的绝对路径。答案文件里只写一个百分数(保留两位小数,
如 83.72, 表示重复率 83.72%), 不加百分号也不写别的文字。
"""

import sys

import similarity
import textio
from errors import ArgumentError, PlagiarismError

USAGE = "用法: python main.py <原文文件> <抄袭版论文文件> <答案文件>"


def compute_rate(original_path, copied_path):
    """读取两篇论文并返回重复率, 百分数形式的 0 ~ 100。"""
    original_text = textio.read_text(original_path)
    copied_text = textio.read_text(copied_path)
    return similarity.duplication_rate(original_text, copied_text)


def main(argv=None):
    """执行一次查重, 返回进程退出码(0 表示成功)。"""
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        if len(arguments) != 3:
            raise ArgumentError(
                "需要 3 个参数, 实际收到 {} 个。\n{}".format(len(arguments), USAGE)
            )
        rate = compute_rate(arguments[0], arguments[1])
        textio.write_rate(arguments[2], rate)
    except PlagiarismError as exc:
        print("错误: {}".format(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # 兜底: 预想不到的错误也不要留下调用栈
        print("未知错误: {}".format(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
