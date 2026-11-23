"""演示用课表数据与自然语言查询。"""

import datetime


WEEKDAY_NAMES = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
SAMPLE_SCHEDULE = {
    "周一": [
        ("08:30", "10:00", "软件工程", "博学楼 302"),
        ("14:00", "15:30", "计算机网络", "明德楼 205"),
    ],
    "周二": [
        ("10:10", "11:40", "数据库原理", "实验楼 401"),
    ],
    "周三": [
        ("08:30", "10:00", "人工智能导论", "博学楼 101"),
        ("19:00", "20:30", "软件工程实践", "创新中心 206"),
    ],
    "周四": [
        ("14:00", "15:30", "编译原理", "明德楼 108"),
    ],
    "周五": [
        ("10:10", "11:40", "软件测试", "实验楼 305"),
    ],
    "周六": [],
    "周日": [],
}


def _resolve_day(value, now):
    text = (value or "today").strip()
    if text in ("today", "今天", ""):
        return WEEKDAY_NAMES[now.weekday()]
    if text in ("tomorrow", "明天"):
        return WEEKDAY_NAMES[(now + datetime.timedelta(days=1)).weekday()]
    if text in ("昨天",):
        return WEEKDAY_NAMES[(now - datetime.timedelta(days=1)).weekday()]
    normalized = text.replace("星期", "周")
    if normalized in WEEKDAY_NAMES:
        return normalized
    return WEEKDAY_NAMES[now.weekday()]


def query_schedule(day="today", now=None):
    current = now or datetime.datetime.now()
    day_name = _resolve_day(day, current)
    courses = SAMPLE_SCHEDULE.get(day_name, [])
    if not courses:
        return "{}没有安排课程。".format(day_name)
    lines = ["{}的课表:".format(day_name)]
    for start, end, name, location in courses:
        lines.append("{}–{} {} ({})".format(start, end, name, location))
    return "\n".join(lines)
