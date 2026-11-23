import datetime
import os
import shutil
import tempfile
import unittest

from reminder_scheduler import ReminderScheduler, SchedulerError


class SchedulerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.scheduler = ReminderScheduler(os.path.join(self.tmp, "deskbird.db"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_add_and_reload(self):
        created = self.scheduler.add("交作业", "2026-11-23 22:00")
        reloaded = ReminderScheduler(os.path.join(self.tmp, "deskbird.db"))
        self.assertEqual(created["reminder_id"], reloaded.list()[0]["reminder_id"])

    def test_once_fires_and_becomes_done(self):
        self.scheduler.add("交作业", "2026-11-23 22:00")
        sent = []
        result = self.scheduler.tick(
            datetime.datetime(2026, 11, 23, 22, 0), notify=sent.append
        )
        self.assertEqual(1, len(result))
        self.assertEqual(result, sent)
        self.assertEqual([], self.scheduler.list("pending"))

    def test_daily_reschedules_next_day(self):
        reminder = self.scheduler.add(
            "背单词", "2026-11-23 21:00", "daily", 0
        )
        self.scheduler.tick(datetime.datetime(2026, 11, 23, 21, 0))
        updated = self.scheduler.get(reminder["reminder_id"])
        self.assertEqual("2026-11-24 21:00", updated["remind_at"])
        self.assertEqual("pending", updated["status"])

    def test_interval_reschedules(self):
        reminder = self.scheduler.add(
            "喝水", "2026-11-23 21:00", "interval", 45
        )
        self.scheduler.tick(datetime.datetime(2026, 11, 23, 21, 0))
        updated = self.scheduler.get(reminder["reminder_id"])
        self.assertEqual("2026-11-23 21:45", updated["remind_at"])

    def test_snooze(self):
        reminder = self.scheduler.add("开会", "2026-11-23 21:00")
        updated = self.scheduler.snooze(
            reminder["reminder_id"], 10, datetime.datetime(2026, 11, 23, 21, 0)
        )
        self.assertEqual("2026-11-23 21:10", updated["remind_at"])

    def test_invalid_repeat_type(self):
        with self.assertRaises(SchedulerError):
            self.scheduler.add("x", "2026-11-23 21:00", "none", 0)

    def test_interval_requires_positive_minutes(self):
        with self.assertRaises(SchedulerError):
            self.scheduler.add("x", "2026-11-23 21:00", "interval", 0)


if __name__ == "__main__":
    unittest.main()
