"""效能分析: 找出生成大量题目时的性能瓶颈, 并对比两种判重写法。

运行方式(在项目根目录)::

    python tools/benchmark.py

产物:

* ``docs/benchmark_results.txt`` —— 耗时表、热点函数排名、优化前后对比
* ``docs/profile_stats.txt``     —— cProfile 的原始文本报告
* ``docs/img/profile_tottime.png``    —— 各函数自身耗时条形图
* ``docs/img/canonical_compare.png``  —— 判重写法优化前后对比图
"""

import cProfile
import os
import pstats
import statistics
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from expression import COMMUTATIVE, Expression  # noqa: E402  需要先补 sys.path
from generator import Generator  # noqa: E402
from number_text import format_number  # noqa: E402

COUNTS = (1000, 5000, 10000)
LIMITS = (10, 100)
AB_ROUNDS = 5

_TUPLE_CANONICAL = Expression.canonical


def string_canonical(self):
    """优化前的写法: 把规范形式拼成字符串。留着做对比。"""
    if self.is_leaf:
        return format_number(self.value)
    left = string_canonical(self.left)
    right = string_canonical(self.right)
    if self.op in COMMUTATIVE and right < left:
        left, right = right, left
    return "({} {} {})".format(self.op, left, right)


def time_generation(count, limit, seed=1):
    """生成 count 道题, 返回耗时(秒)。"""
    started = time.perf_counter()
    Generator(limit=limit, seed=seed).generate(count)
    return time.perf_counter() - started


def timing_table():
    """不同题量和范围下的耗时。"""
    lines = ["{:<10}{:>12}{:>12}".format("题目个数", "-r 10", "-r 100")]
    lines.append("-" * 34)
    for count in COUNTS:
        row = [time_generation(count, limit) for limit in LIMITS]
        lines.append("{:<10}{:>11.3f}s{:>11.3f}s".format(count, row[0], row[1]))
    return lines


def compare_canonical_keys(rounds=AB_ROUNDS, count=10000):
    """对比两种判重写法: 交替测量, 免得机器一会儿快一会儿慢影响结论。

    Returns:
        (字符串写法耗时列表, 元组写法耗时列表)
    """
    before, after = [], []
    for seed in range(rounds):
        Expression.canonical = string_canonical
        before.append(time_generation(count, 10, seed))
        Expression.canonical = _TUPLE_CANONICAL
        after.append(time_generation(count, 10, seed))
    Expression.canonical = _TUPLE_CANONICAL
    return before, after


def profile_once(count=10000, limit=10):
    """对生成过程做一次 cProfile, 返回统计对象。"""
    profiler = cProfile.Profile()
    profiler.enable()
    Generator(limit=limit, seed=2).generate(count)
    profiler.disable()
    return pstats.Stats(profiler)


def top_functions(stats, size=8):
    """按函数自身耗时排出前几名。"""
    rows = []
    for (filename, _line, function), item in stats.stats.items():
        rows.append((item[2], function, os.path.basename(filename)))
    rows.sort(reverse=True)
    return rows[:size]


def _use_chinese_font(matplotlib):
    from matplotlib import font_manager

    available = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in ("Microsoft YaHei", "SimHei", "DejaVu Sans"):
        if candidate in available:
            matplotlib.rcParams["font.sans-serif"] = [candidate]
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


def write_charts(stats, before, after, chart_dir):
    """画两张图: 热点函数, 以及判重写法优化前后对比。"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _use_chinese_font(matplotlib)
    os.makedirs(chart_dir, exist_ok=True)

    rows = [row for row in top_functions(stats, 10) if row[0] > 0.001]
    labels = ["{}.{}".format(row[2], row[1]) for row in rows][::-1]
    values = [row[0] for row in rows][::-1]
    plt.figure(figsize=(7.5, 4))
    plt.barh(labels, values)
    plt.xlabel("tottime (s)")
    plt.title("cProfile: 生成 10000 道题时各函数自身耗时")
    plt.tight_layout()
    plt.savefig(os.path.join(chart_dir, "profile_tottime.png"), dpi=150)
    plt.close()

    plt.figure(figsize=(5.5, 4))
    bars = plt.bar(
        ["拼接字符串", "嵌套元组"],
        [statistics.median(before), statistics.median(after)],
        color=["#c0c8d0", "#4a90d9"],
    )
    for bar, values_ in zip(bars, (before, after)):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                 "{:.3f}s".format(statistics.median(values_)),
                 ha="center", va="bottom")
    plt.ylabel("生成 10000 道题的耗时 (s)")
    plt.title("判重写法优化前后对比")
    plt.tight_layout()
    plt.savefig(os.path.join(chart_dir, "canonical_compare.png"), dpi=150)
    plt.close()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    docs_dir = os.path.join(PROJECT_ROOT, "docs")
    chart_dir = os.path.join(docs_dir, "img")
    os.makedirs(chart_dir, exist_ok=True)

    lines = timing_table()
    lines.append("")

    before, after = compare_canonical_keys()
    lines.append("判重写法对比(生成 10000 道题, 交替测量 {} 轮):".format(AB_ROUNDS))
    lines.append("  拼接字符串: 中位数 {:.4f}s".format(statistics.median(before)))
    lines.append("  嵌套元组  : 中位数 {:.4f}s".format(statistics.median(after)))
    lines.append("  提速      : {:.2f} 倍".format(
        statistics.median(before) / statistics.median(after)))
    lines.append("")

    stats = profile_once()
    lines.append("生成 10000 道题(-r 10)时, 自身耗时最多的函数:")
    for tottime, function, filename in top_functions(stats):
        lines.append("  {:>8.4f}s  {:<22} ({})".format(tottime, function, filename))

    report = "\n".join(lines)
    print(report)
    with open(os.path.join(docs_dir, "benchmark_results.txt"), "w", encoding="utf-8") as handle:
        handle.write(report + "\n")
    with open(os.path.join(docs_dir, "profile_stats.txt"), "w", encoding="utf-8") as handle:
        stats.stream = handle
        stats.sort_stats("tottime").print_stats(20)

    try:
        write_charts(stats, before, after, chart_dir)
    except ImportError:
        print("\n[提示] 没装 matplotlib, 跳过画图。")


if __name__ == "__main__":
    main()
