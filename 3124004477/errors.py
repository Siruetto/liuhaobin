"""自定义异常。

设计原则: 每一种"可预期的失败"都对应一个独立的异常类, 由 main.py 统一
捕获并翻译成"人话 + 退出码", 这样程序在出错时不会抛出难以阅读的调用栈,
也方便单元测试针对每一种失败场景分别断言。
"""


class PlagiarismError(Exception):
    """本程序所有可预期错误的基类, 默认退出码为 1。"""

    exit_code = 1


class ArgumentError(PlagiarismError):
    """命令行参数个数不是 3 个。

    设计目标: 使用者在忘记传参数或传错参数时, 应该立刻看到正确的用法,
    而不是让程序带着错误的参数继续跑下去。
    """

    exit_code = 2


class InputFileError(PlagiarismError):
    """输入文件不存在 / 不是普通文件 / 打开失败。

    设计目标: 把"路径写错"和"路径指向目录"这两种最常见的误用区分开,
    并在错误信息里回显出问题的路径。
    """

    exit_code = 3


class DecodeError(PlagiarismError):
    """输入文件不是受支持的文本编码(utf-8 / gb18030)。

    设计目标: 中文论文常见 GBK 与 UTF-8 两种编码, 程序依次尝试,
    都失败时明确告知使用者是"编码问题", 而不是给出乱码后的错误答案。
    """

    exit_code = 4


class OutputFileError(PlagiarismError):
    """答案文件无法写入(父目录不存在、没有权限等)。

    设计目标: 计算已经成功, 却写不出答案时, 必须让使用者知道
    "失败发生在写文件这一步", 而不是误以为算法出了问题。
    """

    exit_code = 5
