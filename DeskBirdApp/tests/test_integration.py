import datetime
import os
import shutil
import tempfile
import unittest

from app import create_agent


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.agent = create_agent(
            db_path=os.path.join(self.tmp, "deskbird.db"),
            memory_path=os.path.join(self.tmp, "memory.json"),
            clock=lambda: datetime.datetime(2026, 11, 23, 10, 0),
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_add_then_list_reminder(self):
        reply = self.agent.chat("提醒我 明天 22:00 交软工作业")
        self.assertTrue(reply["actions"][0]["ok"])
        listing = self.agent.chat("查看提醒")
        self.assertIn("交软工作业", listing["text"])

    def test_old_calculator_still_works(self):
        reply = self.agent.chat("帮我算一下 (3+5)*2")
        self.assertEqual("16", reply["text"])

    def test_schedule_query(self):
        reply = self.agent.chat("明天有什么课")
        self.assertIn("课表", reply["text"])
        self.assertEqual("schedule_query", reply["actions"][0]["tool"])

    def test_tool_count_stays_at_ten(self):
        names = [item["function"]["name"] for item in self.agent.toolbox.schemas()]
        self.assertEqual(10, len(names))
        self.assertIn("schedule_query", names)

    def test_due_reminder_returns_notification(self):
        self.agent.chat("提醒我 明天 22:00 交软工作业")
        sent = []
        self.agent.scheduler.tick(
            datetime.datetime(2026, 11, 24, 22, 0), notify=sent.append
        )
        self.assertEqual("交软工作业", sent[0]["content"])


if __name__ == "__main__":
    unittest.main()
