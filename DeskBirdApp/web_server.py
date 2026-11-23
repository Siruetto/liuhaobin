"""报时鸟 Alpha 版网页服务与提醒事件推送。"""

import argparse
import datetime
import json
import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app import APP_ROOT, APP_VERSION, create_agent
from device import DeviceHub


WEB_ROOT = os.path.join(APP_ROOT, "web")


class AppState:
    """集中保存智能体、提醒事件和最近一次通知。"""

    def __init__(self, agent, clock=None):
        self.agent = agent
        self.scheduler = agent.scheduler
        self.devices = DeviceHub()
        self.clock = clock or datetime.datetime.now
        self._events = []
        self._next_event_id = 1
        self._state_lock = threading.Lock()
        self._tick_lock = threading.Lock()

    def tick(self, now=None):
        with self._tick_lock:
            return self.scheduler.tick(now or self.clock(), notify=self._notify)

    def _notify(self, reminder):
        with self._state_lock:
            event = {
                "id": self._next_event_id,
                "type": "reminder_due",
                "reminder_id": reminder["id"],
                "content": reminder["content"],
                "scheduled_at": reminder["scheduled_at"],
                "created_at": self.clock().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self._next_event_id += 1
            self._events.append(event)
            self._events = self._events[-200:]
        self.devices.dispatch(reminder["content"])

    def events_after(self, event_id=0):
        with self._state_lock:
            return [event for event in self._events if event["id"] > int(event_id)]

    def status(self):
        return {
            "mode": self.agent.mode,
            "version": APP_VERSION,
            "server_time": self.clock().strftime("%Y-%m-%d %H:%M:%S"),
            "pending_reminders": len(self.scheduler.list("pending")),
            "tools": len(self.agent.toolbox.schemas()),
            "devices_online": sum(
                1 for device in self.devices.list_devices() if device["online"]
            ),
        }

    def add_demo_reminder(self):
        when = self.clock() + datetime.timedelta(seconds=3)
        return self.scheduler.add(
            "演示提醒：准备 Alpha 冲刺展示",
            when.strftime("%Y-%m-%d %H:%M"),
            "once",
            0,
        )


def create_server(state, host="127.0.0.1", port=0):
    class Handler(BaseHTTPRequestHandler):
        app_state = state
        web_root = WEB_ROOT

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            if path == "/api/status":
                self._json(self.app_state.status())
                return
            if path == "/api/reminders":
                status = (query.get("status") or ["pending"])[0]
                reminders = self.app_state.scheduler.list(None if status == "all" else status)
                self._json({"reminders": reminders})
                return
            if path == "/api/events":
                after = int((query.get("after") or ["0"])[0])
                self._json({"events": self.app_state.events_after(after)})
                return
            if path == "/api/tools":
                self._json({"tools": self.app_state.agent.toolbox.schemas()})
                return
            if path == "/api/memory":
                self._json({"facts": self.app_state.agent.memory.recall()})
                return
            if path == "/api/devices":
                self._json({"devices": self.app_state.devices.list_devices()})
                return
            if path == "/":
                self._file("index.html", "text/html; charset=utf-8")
                return
            if path == "/app.js":
                self._file("app.js", "application/javascript; charset=utf-8")
                return
            if path == "/styles.css":
                self._file("styles.css", "text/css; charset=utf-8")
                return
            self._json({"error": "not found"}, status=404)

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                body = self._read_json()
                if path == "/api/chat":
                    message = str(body.get("message") or "").strip()
                    if not message:
                        self._json({"error": "message 不能为空"}, status=400)
                        return
                    reply = self.app_state.agent.chat(message)
                    self._json(
                        {
                            "reply": reply["text"],
                            "actions": reply["actions"],
                            "reminders": self.app_state.scheduler.list("pending"),
                        }
                    )
                    return
                if path == "/api/reminders":
                    reminder = self.app_state.scheduler.add(
                        body.get("content"),
                        body.get("remind_at"),
                        body.get("repeat_type", "once"),
                        body.get("repeat_interval", 0),
                    )
                    self._json({"reminder": reminder}, status=201)
                    return
                if path == "/api/demo":
                    reminder = self.app_state.add_demo_reminder()
                    self._json({"reminder": reminder}, status=201)
                    return
                if path == "/api/reset":
                    self.app_state.agent.reset()
                    self._json({"ok": True})
                    return
            except (ValueError, TypeError) as error:
                self._json({"error": str(error)}, status=400)
                return
            self._json({"error": "not found"}, status=404)

        def do_PATCH(self):
            match = re.fullmatch(r"/api/reminders/(\d+)", urlparse(self.path).path)
            if not match:
                self._json({"error": "not found"}, status=404)
                return
            reminder_id = int(match.group(1))
            try:
                body = self._read_json()
                action = body.get("action")
                if action == "done":
                    changed = self.app_state.scheduler.mark_done(reminder_id)
                elif action == "snooze":
                    reminder = self.app_state.scheduler.snooze(
                        reminder_id, int(body.get("minutes", 10))
                    )
                    changed = reminder is not None
                else:
                    self._json({"error": "action 只能是 done 或 snooze"}, status=400)
                    return
                if not changed:
                    self._json({"error": "没有找到该提醒"}, status=404)
                    return
                self._json({"ok": True})
            except (ValueError, TypeError) as error:
                self._json({"error": str(error)}, status=400)

        def _read_json(self):
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8") or "{}")

        def _file(self, name, content_type):
            path = os.path.join(self.web_root, name)
            with open(path, "rb") as handle:
                body = handle.read()
            self._send(200, content_type, body)

        def _json(self, payload, status=200):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send(status, "application/json; charset=utf-8", body)

        def _send(self, status, content_type, body):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            return

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server


class SchedulerWorker(threading.Thread):
    def __init__(self, state, interval=1):
        super().__init__(daemon=True)
        self.state = state
        self.interval = interval
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.wait(self.interval):
            try:
                self.state.tick()
            except Exception:
                # 单次扫描失败不应结束整个提醒值守线程。
                continue

    def stop(self):
        self.stop_event.set()


def main(argv=None):
    parser = argparse.ArgumentParser(description="报时鸟 Alpha 版网页")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", default=os.path.join(APP_ROOT, "data", "deskbird.db"))
    parser.add_argument(
        "--memory", default=os.path.join(APP_ROOT, "data", "memory.json")
    )
    args = parser.parse_args(argv)

    agent = create_agent(db_path=args.db, memory_path=args.memory)
    state = AppState(agent)
    worker = SchedulerWorker(state)
    worker.start()
    server = create_server(state, args.host, args.port)
    print("报时鸟已启动: http://{}:{}/".format(args.host, args.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        worker.stop()
        server.server_close()


if __name__ == "__main__":
    main()
