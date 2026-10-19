"""路径与运行配置。

所有可变数据都放在项目目录下, 不往系统目录写东西:

* ``workspace/`` —— 文件工具能碰到的唯一目录;
* ``data/``      —— 待办清单和对话记忆。
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(PROJECT_ROOT, "workspace")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
TODO_FILE = os.path.join(DATA_DIR, "todos.json")


def ensure_dirs():
    """确保运行需要的两个目录存在。"""
    for path in (WORKSPACE_DIR, DATA_DIR):
        os.makedirs(path, exist_ok=True)
