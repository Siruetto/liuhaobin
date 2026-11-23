import datetime
import unittest

from reminder_planner import ReminderParser


class ReminderParserTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime(2026, 11, 23, 10, 0)
        self.parser = ReminderParser()

    def test_tomorrow_once(self):
        spec = self.parser.parse("提醒我 明天 22:00 交软工作业", self.now)
        self.assertEqual("交软工作业", spec["content"])
        self.assertEqual(datetime.datetime(2026, 11, 24, 22, 0), spec["remind_at"])
        self.assertEqual("once", spec["repeat_type"])

    def test_today_without_date(self):
        spec = self.parser.parse("提醒我 15:30 开会", self.now)
        self.assertEqual(datetime.datetime(2026, 11, 23, 15, 30), spec["remind_at"])

    def test_past_time_without_date_moves_to_tomorrow(self):
        spec = self.parser.parse("提醒我 09:00 交作业", self.now)
        self.assertEqual(datetime.datetime(2026, 11, 24, 9, 0), spec["remind_at"])

    def test_weekday(self):
        spec = self.parser.parse("提醒我周五 22:00 交软工作业", self.now)
        self.assertEqual(datetime.datetime(2026, 11, 27, 22, 0), spec["remind_at"])

    def test_daily(self):
        spec = self.parser.parse("每天 21:00 提醒背单词", self.now)
        self.assertEqual("背单词", spec["content"])
        self.assertEqual("daily", spec["repeat_type"])
        self.assertEqual(datetime.datetime(2026, 11, 23, 21, 0), spec["remind_at"])

    def test_interval(self):
        spec = self.parser.parse("每 45 分钟提醒我起来喝水", self.now)
        self.assertEqual("起来喝水", spec["content"])
        self.assertEqual("interval", spec["repeat_type"])
        self.assertEqual(45, spec["repeat_interval"])

    def test_non_reminder_is_not_parsed(self):
        self.assertIsNone(self.parser.parse("今天天气怎么样", self.now))


if __name__ == "__main__":
    unittest.main()
