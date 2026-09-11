# 论文查重（个人项目）

给出原文和一份在原文上经过增删改得到的抄袭版论文，计算两者的重复率，
结果写入答案文件，精确到小数点后两位。

## 快速开始

```bash
python main.py <原文文件绝对路径> <抄袭版论文绝对路径> <答案文件绝对路径>
```

例如：

```bash
python main.py samples/orig.txt samples/orig_add.txt samples/ans.txt
cat samples/ans.txt      # -> 89.12
```

## 环境要求

运行 `main.py` **只需要 Python 3.6+ 的标准库**，不需要安装任何第三方包。
`requirements.txt` 里列出的 `pytest` / `pytest-cov` 只用于跑测试和统计覆盖率。

## 目录结构

```
3124004477/                 # 学号目录
├── main.py                 # 命令行入口: python main.py 原文 抄袭版 答案
├── similarity.py           # 计算模块: 归一化 + 最长公共子序列 + 重复率
├── textio.py               # 文件读写: utf-8 / gb18030 兼容
├── errors.py               # 异常层级(每种异常自带退出码)
├── requirements.txt
├── .flake8 / .coveragerc / .gitignore
├── samples/                # 自带的样例原文与三种抄袭版
├── tests/                  # 45 个单元测试
├── tools/
│   ├── benchmark.py        # 性能对比 + cProfile 热点 + 生成图表
│   └── compare_metrics.py  # 打印三种归一化口径的重复率, 便于与样例答案核对
└── docs/                   # PSP 表格、博客草稿、性能与质量报告、图表
```

## 自带样例的期望输出

| 原文 | 抄袭版 | 答案 |
| --- | --- | --- |
| `samples/orig.txt` | `samples/orig.txt` | `100.00` |
| `samples/orig.txt` | `samples/orig_add.txt` | `89.12` |
| `samples/orig.txt` | `samples/orig_del.txt` | `84.55` |
| `samples/orig.txt` | `samples/orig_modify.txt` | `98.82` |

## 运行测试与覆盖率

```bash
python -m pytest --cov=. --cov-branch --cov-report=term-missing tests -q
# 不想装 pytest 也可以:
python -m unittest discover -s tests -t . -v
```

当前结果：**45 passed，4 个源文件语句与分支覆盖率 100%**。
想看带颜色的报告可以再跑 `python -m pytest --cov=. --cov-report=html tests`，
然后浏览器打开 `htmlcov/index.html`（该目录已在 `.gitignore` 中，不需要提交）。

## 代码质量分析

```bash
python -m flake8 .        # 配置见 .flake8, 当前 0 警告
```

## 性能分析

```bash
python tools/benchmark.py
```

会重新生成 `docs/benchmark_results.txt`、`docs/profile_stats.txt` 与
`docs/img/` 下的两张图。当前实测：10 万字文档纯计算 0.61 秒，
完整命令行运行（含 Python 解释器启动）0.68 秒，评测上限为 5 秒。

## 算法说明（一句话版）

`重复率 = 2 × LCS(原文, 抄袭版) / (原文长度 + 抄袭版长度) × 100%`，
LCS 长度用**位并行算法**（大整数位掩码）计算，复杂度 O(n×m/w)，
比二维动态规划快两个数量级。详见 `docs/blog.md` 第二节。

## 退出码约定

| 退出码 | 含义 |
| --- | --- |
| 0 | 成功 |
| 1 | 未预期的错误 |
| 2 | 命令行参数个数不对 |
| 3 | 输入文件不存在 / 不是普通文件 / 打不开 |
| 4 | 输入文件编码不受支持（非 UTF-8 / GB18030） |
| 5 | 答案文件无法写入 |

## 与班级样例核对

如果答案数值与班级样例对不上，很可能是归一化口径不同：

```bash
python tools/compare_metrics.py <原文> <抄袭版>
```

它会同时打印 `LCS/原文长度`、`LCS/抄袭版长度`、`2*LCS/(m+n)` 三种口径，
确认后修改 `similarity.duplication_rate` 中的那一行公式即可。
