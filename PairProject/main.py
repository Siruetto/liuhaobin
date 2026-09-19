"""小学四则运算题目生成器 / 批改器 命令行入口。

用法::

    python main.py -n 10 -r 10                       # 生成 10 道 10 以内的题目
    python main.py -e Exercises.txt -a Answers.txt   # 批改, 结果写进 Grade.txt
"""

import argparse
import sys

from generator import Generator, GeneratorError
from grading import grade
from records import (
    ANSWER_FILE,
    EXERCISE_FILE,
    GRADE_FILE,
    write_answers,
    write_exercises,
    write_grade,
)

DESCRIPTION = "小学四则运算题目生成器"

EPILOG = """\
示例:
  python main.py -n 10 -r 10                      生成 10 道 10 以内的题目
  python main.py -e Exercises.txt -a Answers.txt  批改题目, 结果写进 Grade.txt

说明:
  -n 指定题目个数, -r 指定数值范围(题目里出现的自然数、真分数及其分母都小于 r)。
  生成时题目写进当前目录的 Exercises.txt, 答案写进 Answers.txt。
  -r 是必须给的参数, 缺了程序会报错并显示这段帮助。
"""


def build_parser():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-n", type=int, metavar="N", help="生成题目的个数")
    parser.add_argument("-r", type=int, metavar="R", help="数值范围, 题目里的数都小于 R")
    parser.add_argument("-e", metavar="EXERCISE", help="要批改的题目文件")
    parser.add_argument("-a", metavar="ANSWER", help="与题目文件对应的答案文件")
    return parser


def main(argv=None):
    """执行一次生成或批改, 返回进程退出码(0 表示成功)。"""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.e or arguments.a:
            return _run_grade(parser, arguments)
        return _run_generate(parser, arguments)
    except GeneratorError as error:
        print("错误: {}".format(error), file=sys.stderr)
        return 1
    except (ValueError, OSError) as error:
        print("错误: {}".format(error), file=sys.stderr)
        return 1


def _run_generate(parser, arguments):
    if arguments.n is None or arguments.r is None:
        return _reject(parser, "-n 和 -r 都必须给出")
    if arguments.n < 1:
        return _reject(parser, "-n 必须是正整数")
    if arguments.r < 1:
        return _reject(parser, "-r 必须是不小于 1 的自然数")

    problems = Generator(limit=arguments.r).generate(arguments.n)
    write_exercises(EXERCISE_FILE, problems)
    write_answers(ANSWER_FILE, problems)
    print("已生成 {} 道题目, 写入 {} 和 {}".format(
        len(problems), EXERCISE_FILE, ANSWER_FILE))
    return 0


def _run_grade(parser, arguments):
    if not (arguments.e and arguments.a):
        return _reject(parser, "-e 和 -a 必须同时给出")
    if arguments.n is not None or arguments.r is not None:
        return _reject(parser, "批改模式不能和 -n / -r 一起使用")

    correct, wrong = grade(arguments.e, arguments.a)
    write_grade(GRADE_FILE, correct, wrong)
    print("批改完成: 正确 {} 题, 错误 {} 题, 结果写入 {}".format(
        len(correct), len(wrong), GRADE_FILE))
    return 0


def _reject(parser, message):
    """参数不对时: 打印错误信息 + 帮助, 返回码 2。"""
    print("参数错误: {}".format(message), file=sys.stderr)
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
