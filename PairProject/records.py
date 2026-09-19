"""三种文件的读写: 题目文件、答案文件、成绩文件。

文件格式按题目要求:

* ``Exercises.txt``: ``1. 1/2 + 1/3 =``
* ``Answers.txt``:   ``1. 5/6``
* ``Grade.txt``:     ``Correct: 1 (1)`` / ``Wrong: 1 (2)``
"""

import re

from expression import parse_expression
from number_text import format_number, parse_number

EXERCISE_FILE = "Exercises.txt"
ANSWER_FILE = "Answers.txt"
GRADE_FILE = "Grade.txt"

_ENTRY_RE = re.compile(r"^(\d+)\s*[.、:：]\s*(.+)$")


def write_exercises(path, problems):
    """写题目文件, 每行是"题号. 表达式 ="的形式。"""
    with open(path, "w", encoding="utf-8") as handle:
        for index, problem in enumerate(problems, start=1):
            handle.write("{}. {} =\n".format(index, problem))


def write_answers(path, problems):
    """写答案文件, 每行是"题号. 答案"。"""
    with open(path, "w", encoding="utf-8") as handle:
        for index, problem in enumerate(problems, start=1):
            handle.write("{}. {}\n".format(index, format_number(problem.evaluate())))


def read_exercises(path):
    """读题目文件, 返回 [(题号, 表达式), ...]。"""
    entries = []
    for line in _read_lines(path):
        text = line.rstrip("=").strip()
        if not text:
            continue
        number, body = _split_entry(text, path)
        entries.append((number, parse_expression(body)))
    return entries


def read_answers(path):
    """读答案文件, 返回 {题号: 数值}。"""
    answers = {}
    for line in _read_lines(path):
        if not line.strip():
            continue
        number, body = _split_entry(line, path)
        answers[number] = parse_number(body)
    return answers


def write_grade(path, correct, wrong):
    """写成绩文件, 一行正确一行错误。"""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(_format_line("Correct", correct) + "\n")
        handle.write(_format_line("Wrong", wrong) + "\n")


def _read_lines(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def _split_entry(text, path):
    match = _ENTRY_RE.match(text.strip())
    if not match:
        raise ValueError("{} 里的这一行不符合格式: {!r}".format(path, text))
    return int(match.group(1)), match.group(2).strip()


def _format_line(label, numbers):
    return "{}: {} ({})".format(label, len(numbers), ", ".join(str(n) for n in numbers))
