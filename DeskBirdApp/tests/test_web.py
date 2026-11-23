import datetime
import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.request

from app import create_agent
from web_server import AppState, create_server


class WebServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.now = datetime.datetime(2026, 11, 23, 10, 0)
        agent = create_agent(
            db_path=os.path.join(self.tmp, "deskbird.db"),
            memory_path=os.path.join(self.tmp, "memory.json"),
            clock=lambda: self.now,
        )
        self.state = AppState(agent, clock=lambda: self.now)
        self.server = create_server(self.state, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:{}".format(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def request(self, path, method="GET", body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_status(self):
        status, data = self.request("/api/status")
        self.assertEqual(200, status)
        self.assertEqual(10, data["tools"])
        self.assertEqual("0.1.0-alpha.1", data["version"])

    def test_index_is_served(self):
        request = urllib.request.Request(self.base + "/")
        with urllib.request.urlopen(request, timeout=3) as response:
            body = response.read().decode("utf-8")
        self.assertIn("报时鸟", body)

    def test_chat_endpoint(self):
        status, data = self.request(
            "/api/chat", "POST", {"message": "帮我算一下 (3+5)*2"}
        )
        self.assertEqual(200, status)
        self.assertEqual("16", data["reply"])

    def test_create_and_complete_reminder(self):
        status, created = self.request(
            "/api/reminders",
            "POST",
            {
                "content": "交软工作业",
                "remind_at": "2026-11-24 22:00",
                "repeat_type": "once",
                "repeat_interval": 0,
            },
        )
        self.assertEqual(201, status)
        reminder_id = created["reminder"]["reminder_id"]
        status, _ = self.request(
            "/api/reminders/{}".format(reminder_id),
            "PATCH",
            {"action": "done"},
        )
        self.assertEqual(200, status)
        self.assertEqual([], self.state.scheduler.list("pending"))

    def test_due_event_is_returned_once(self):
        self.state.scheduler.add("演示", "2026-11-23 10:00")
        self.state.tick(self.now)
        _, data = self.request("/api/events?after=0")
        self.assertEqual(1, len(data["events"]))
        _, again = self.request("/api/events?after=1")
        self.assertEqual([], again["events"])

    def test_tools_are_ten(self):
        _, data = self.request("/api/tools")
        names = [item["function"]["name"] for item in data["tools"]]
        self.assertEqual(10, len(names))
        self.assertIn("schedule_query", names)

    def test_device_status(self):
        _, data = self.request("/api/devices")
        self.assertEqual(2, len(data["devices"]))
        self.assertTrue(data["devices"][0]["online"])


if __name__ == "__main__":
    unittest.main()
