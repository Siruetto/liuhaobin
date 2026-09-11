"""论文查重命令行入口。

用法::

    python main.py <原文文件> <抄袭版论文文件> <答案文件>

三个参数都是文件的绝对路径, 答案文件中的内容形如 ``80.95``。
"""

import sys

import similarity
import textio

USAGE = "用法: python main.py <原文文件> <抄袭版论文文件> <答案文件>"


def compute_rate(original_path, copied_path):
    """读取两篇论文并返回重复率。"""
    original_text = textio.read_text(original_path)
    copied_text = textio.read_text(copied_path)
    return similarity.duplication_rate(original_text, copied_text)


def main(argv=None):
    """执行一次查重, 返回进程退出码(0 表示成功)。"""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 3:
        print(USAGE, file=sys.stderr)
        return 2
    rate = compute_rate(arguments[0], arguments[1])
    textio.write_rate(arguments[2], rate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
