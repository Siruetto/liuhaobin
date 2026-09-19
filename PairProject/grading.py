"""批改: 用题目文件算出标准答案, 再和答案文件里写的答案逐个比对。"""

from records import read_answers, read_exercises


def grade(exercise_path, answer_path):
    """返回 (正确的题号列表, 错误的题号列表), 都按题号升序。"""
    given = read_answers(answer_path)
    correct, wrong = [], []
    for number, expression in read_exercises(exercise_path):
        if number not in given:
            raise ValueError("答案文件里缺少第 {} 题的答案".format(number))
        if given[number] == expression.evaluate():
            correct.append(number)
        else:
            wrong.append(number)
    return correct, wrong
