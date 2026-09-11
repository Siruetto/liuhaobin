"""对照工具: 打印同一对文件在几种"重复率"定义下的取值。

不同老师给的样例答案可能采用不同的归一化方式, 用这个脚本可以快速
判断产品默认的 Dice 系数是否与样例答案一致; 若不一致, 只需改
similarity.duplication_rate 里的那一行公式。

用法::

    python tools/compare_metrics.py <原文文件> <抄袭版文件>
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import similarity  # noqa: E402  需要先补好 sys.path 才能 import
import textio  # noqa: E402


def _format(value):
    return "n/a" if value is None else similarity.format_rate(value)


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip())
        return 2
    original = similarity.normalize(textio.read_text(argv[0]))
    copied = similarity.normalize(textio.read_text(argv[1]))
    lcs = similarity.lcs_length(original, copied)
    total = len(original) + len(copied)

    by_original = 100.0 * lcs / len(original) if original else None
    by_copied = 100.0 * lcs / len(copied) if copied else None
    dice = 200.0 * lcs / total if total else 100.0

    print("原文长度                : {}".format(len(original)))
    print("抄袭版长度              : {}".format(len(copied)))
    print("最长公共子序列          : {}".format(lcs))
    print("LCS / 原文长度          : {}".format(_format(by_original)))
    print("LCS / 抄袭版长度        : {}".format(_format(by_copied)))
    print("Dice(2*LCS/(m+n), 默认) : {}".format(similarity.format_rate(dice)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
