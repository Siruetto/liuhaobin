"""性能分析脚本: 对比三代 LCS 实现的耗时, 并用 cProfile 找出热点函数。

运行方式(在项目根目录)::

    python tools/benchmark.py

产物:
    docs/benchmark_results.txt     —— 三种实现的耗时对比表
    docs/profile_stats.txt         —— cProfile 文本报告
    docs/img/profile_tottime.png   —— 各函数自身耗时(热点)条形图
    docs/img/benchmark_speedup.png —— 三种实现的耗时对比图(对数坐标)
"""

import cProfile
import os
import pstats
import random
import sys
import tempfile
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import main  # noqa: E402  需要先补好 sys.path 才能 import
import similarity  # noqa: E402

VOCABULARY = (
    "论文查重系统的设计与实现本文针对文本相似度提出了基于最长公共子序列的算法"
    "测试样例原文抄袭版本增删改重复率动态规划位并行时间复杂度空间复杂度实验结果"
)


def lcs_dp_table(first, second):
    """第一代: 完整二维 DP 表, 时间 O(n*m), 空间 O(n*m)。"""
    rows, cols = len(first), len(second)
    table = [[0] * (cols + 1) for _ in range(rows + 1)]
    for i in range(1, rows + 1):
        for j in range(1, cols + 1):
            if first[i - 1] == second[j - 1]:
                table[i][j] = table[i - 1][j - 1] + 1
            else:
                table[i][j] = max(table[i - 1][j], table[i][j - 1])
    return table[rows][cols]


def lcs_dp_rolling(first, second):
    """第二代: 滚动数组 DP, 时间 O(n*m), 空间降到 O(n)。"""
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


def lcs_bit_parallel(first, second):
    """第三代: 产品代码里的位并行实现。"""
    return similarity.lcs_length(first, second)


def make_sample_pair(size, seed=20260911):
    """造一对抄袭样本: 在原文上删 5%、改 5%、增 5% 的字符。"""
    rng = random.Random(seed)
    original = "".join(rng.choice(VOCABULARY) for _ in range(size))
    copied = []
    for char in original:
        roll = rng.random()
        if roll < 0.05:  # 删除
            continue
        if roll < 0.10:  # 修改
            copied.append(rng.choice(VOCABULARY))
            continue
        copied.append(char)
    for _ in range(int(size * 0.05)):  # 增加
        copied.insert(rng.randrange(len(copied)), rng.choice(VOCABULARY))
    return original, "".join(copied)


def measure(function, first, second, repeats):
    """返回单次平均耗时(秒)。"""
    started = time.perf_counter()
    for _ in range(repeats):
        function(first, second)
    return (time.perf_counter() - started) / repeats


def run_timing_table():
    """三代实现在不同输入规模下的耗时对比。"""
    sizes = (500, 1000, 2000, 4000)
    implementations = (
        ("第一代 二维DP", lcs_dp_table),
        ("第二代 滚动数组DP", lcs_dp_rolling),
        ("第三代 位并行", lcs_bit_parallel),
    )
    lines = []
    header = "{:<18}{:>12}{:>12}{:>12}{:>12}".format(
        "实现", "500字", "1000字", "2000字", "4000字"
    )
    lines.append(header)
    lines.append("-" * len(header))
    table = {}
    for name, function in implementations:
        row = []
        for size in sizes:
            first, second = make_sample_pair(size)
            if size > 1000 and function is lcs_dp_table:
                row.append(None)  # 二维表内存占用过大, 不再参与对比
                continue
            elapsed = measure(function, first, second, repeats=1)
            table[(name, size)] = elapsed
            row.append(elapsed)
        lines.append(
            "{:<18}".format(name)
            + "".join(
                "{:>12}".format("--" if value is None else "{:.4f}s".format(value))
                for value in row
            )
        )
    return lines, table


def run_large_scale_check():
    """评测要求 5 秒内给出答案, 这里验证大论文的真实耗时。"""
    lines = []
    for size in (20000, 50000, 100000):
        first, second = make_sample_pair(size)
        elapsed = measure(lcs_bit_parallel, first, second, repeats=1)
        lines.append("位并行实现, 原文 {} 字: {:.4f} 秒".format(size, elapsed))
    return lines


def profile_pipeline(size=30000):
    """对完整的查重流程做 cProfile, 找出消耗最大的函数。"""
    workdir = tempfile.mkdtemp(prefix="profile_")
    original_path = os.path.join(workdir, "orig.txt")
    copied_path = os.path.join(workdir, "orig_add.txt")
    answer_path = os.path.join(workdir, "ans.txt")
    first, second = make_sample_pair(size)
    with open(original_path, "w", encoding="utf-8") as handle:
        handle.write(first)
    with open(copied_path, "w", encoding="utf-8") as handle:
        handle.write(second)

    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(3):
        main.main([original_path, copied_path, answer_path])
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("tottime")
    return stats


def _setup_chinese_font(matplotlib):
    """优先使用系统里的中文字体, 找不到就退回默认字体。"""
    from matplotlib import font_manager

    available = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in ("Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC"):
        if candidate in available:
            matplotlib.rcParams["font.sans-serif"] = [candidate]
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


def write_charts(stats, table, chart_dir):
    """把热点函数与耗时对比画成图, 供博客引用。"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _setup_chinese_font(matplotlib)
    os.makedirs(chart_dir, exist_ok=True)

    # 图 1: 各函数自身耗时(热点)
    entries = []
    for (filename, _line, function), item in stats.stats.items():
        if "tools" in filename or "matplotlib" in filename:
            continue
        entries.append(("{}.{}".format(os.path.basename(filename), function), item[2]))
    entries.sort(key=lambda item: item[1], reverse=True)
    entries = entries[:8]
    plt.figure(figsize=(7, 4))
    plt.barh([name for name, _ in entries][::-1], [value for _, value in entries][::-1])
    plt.xlabel("tottime (s)")
    plt.title("cProfile: top functions by own time (3 runs, 30k chars)")
    plt.tight_layout()
    plt.savefig(os.path.join(chart_dir, "profile_tottime.png"), dpi=150)
    plt.close()

    # 图 2: 三代实现的耗时对比(对数坐标)
    sizes = (500, 1000, 2000, 4000)
    plt.figure(figsize=(7, 4))
    for name in ("第一代 二维DP", "第二代 滚动数组DP", "第三代 位并行"):
        values, xs = [], []
        for size in sizes:
            value = table.get((name, size))
            if value is not None:
                xs.append(size)
                values.append(max(value, 1e-6))
        plt.plot(xs, values, marker="o", label=name)
    plt.yscale("log")
    plt.xlabel("文档长度(字符)")
    plt.ylabel("耗时(秒, 对数坐标)")
    plt.title("三种 LCS 实现的耗时对比")
    plt.legend()
    plt.grid(True, which="both", linestyle=":")
    plt.tight_layout()
    plt.savefig(os.path.join(chart_dir, "benchmark_speedup.png"), dpi=150)
    plt.close()


def main_entry():
    try:  # 让控制台也能正确显示中文
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    docs_dir = os.path.join(PROJECT_ROOT, "docs")
    chart_dir = os.path.join(docs_dir, "img")
    os.makedirs(docs_dir, exist_ok=True)

    lines, table = run_timing_table()
    lines.append("")
    lines.append("大文件耗时(位并行实现, 评测上限 5 秒):")
    lines.extend(run_large_scale_check())

    stats = profile_pipeline()
    lines.append("")
    lines.append("cProfile 热点(按 tottime 排序, 前 5):")
    top_functions = sorted(stats.stats.items(), key=lambda item: item[1][2], reverse=True)[:5]
    for (filename, _line, function), item in top_functions:
        lines.append(
            "  {:>8.4f}s  {}  ({})".format(item[2], function, os.path.basename(filename))
        )

    report = "\n".join(lines)
    print(report)
    with open(os.path.join(docs_dir, "benchmark_results.txt"), "w", encoding="utf-8") as handle:
        handle.write(report + "\n")
    with open(os.path.join(docs_dir, "profile_stats.txt"), "w", encoding="utf-8") as handle:
        stats.stream = handle
        stats.sort_stats("tottime").print_stats(20)

    try:
        write_charts(stats, table, chart_dir)
    except ImportError:
        print("[提示] 未安装 matplotlib, 跳过图表生成。")


if __name__ == "__main__":
    main_entry()
