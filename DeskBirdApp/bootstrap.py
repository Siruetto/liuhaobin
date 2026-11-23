"""把上一版 AgentProject 加入导入路径, 以便直接复用四个既有模块。"""

import os
import sys


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(APP_ROOT)
AGENT_PROJECT = os.path.join(REPO_ROOT, "AgentProject")


def ensure_agent_project_on_path():
    if AGENT_PROJECT not in sys.path:
        sys.path.insert(0, AGENT_PROJECT)
