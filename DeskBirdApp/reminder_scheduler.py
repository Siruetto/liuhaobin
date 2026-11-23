"""提醒调度器: SQLite 持久化、到期扫描、周期重排。"""

import datetime
import os
import sqlite3


REPEAT_TYPES = ("once", "daily", "interval")
DATE_FORMAT = "%Y-%m-%d %H:%M"


class SchedulerError(ValueError):
    """提醒数据不合法。"""


def _format_time(value):
    if isinstance(value, datetime.datetime):
        return value.strftime(DATE_FORMAT)
    return datetime.datetime.strptime(str(value), DATE_FORMAT).strftime(DATE_FORMAT)


def _parse_time(value):
    if isinstance(value, datetime.datetime):
        return value
    return datetime.datetime.strptime(str(value), DATE_FORMAT)


class ReminderScheduler:
    """管理一次性、每日和固定间隔提醒。"""

    def __init__(self, db_path):
        self.db_path = db_path
        parent = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(parent, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reminder (
                    reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    remind_at TEXT NOT NULL,
                    repeat_type TEXT NOT NULL DEFAULT 'once'
                        CHECK (repeat_type IN ('once', 'daily', 'interval')),
                    repeat_interval INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'done')),
                    last_notified_at TEXT
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_reminder_due "
                "ON reminder(remind_at, status)"
            )

    @staticmethod
    def _row_to_dict(row):
        return dict(row)

    def add(self, content, remind_at, repeat_type="once", repeat_interval=0):
        text = (content or "").strip()
        if not text:
            raise SchedulerError("提醒内容不能为空")
        if repeat_type not in REPEAT_TYPES:
            raise SchedulerError("重复类型只能是 once、daily 或 interval")
        try:
            when = _format_time(remind_at)
            interval = int(repeat_interval or 0)
        except (TypeError, ValueError):
            raise SchedulerError("提醒时间或间隔格式不正确")
        if repeat_type == "interval" and interval <= 0:
            raise SchedulerError("间隔提醒必须给出正数分钟")
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO reminder"
                "(content, remind_at, repeat_type, repeat_interval, status) "
                "VALUES (?, ?, ?, ?, 'pending')",
                (text, when, repeat_type, interval),
            )
            reminder_id = cursor.lastrowid
        return self.get(reminder_id)

    def get(self, reminder_id):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM reminder WHERE reminder_id = ?", (int(reminder_id),)
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def list(self, status="pending"):
        query = "SELECT * FROM reminder"
        params = ()
        if status is not None:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY remind_at, reminder_id"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def mark_done(self, reminder_id):
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE reminder SET status = 'done' WHERE reminder_id = ?",
                (int(reminder_id),),
            )
        return cursor.rowcount > 0

    def snooze(self, reminder_id, minutes=10, now=None):
        current = now or datetime.datetime.now()
        next_at = _format_time(current + datetime.timedelta(minutes=int(minutes)))
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE reminder SET remind_at = ?, status = 'pending' "
                "WHERE reminder_id = ?",
                (next_at, int(reminder_id)),
            )
        return self.get(reminder_id) if cursor.rowcount else None

    def due(self, now=None):
        current = _format_time(now or datetime.datetime.now())
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM reminder "
                "WHERE status = 'pending' AND remind_at <= ? "
                "ORDER BY remind_at, reminder_id",
                (current,),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def tick(self, now=None, notify=None):
        """触发全部到期提醒, 返回本次通知; 周期提醒自动排下一次。"""
        current_dt = now if isinstance(now, datetime.datetime) else datetime.datetime.now()
        current = _format_time(current_dt)
        due_rows = self.due(current_dt)
        if not due_rows:
            return []

        notifications = []
        with self._connect() as connection:
            for row in due_rows:
                notifications.append(
                    {
                        "id": row["reminder_id"],
                        "content": row["content"],
                        "scheduled_at": row["remind_at"],
                        "repeat_type": row["repeat_type"],
                    }
                )
                if row["repeat_type"] == "once":
                    connection.execute(
                        "UPDATE reminder SET status = 'done', last_notified_at = ? "
                        "WHERE reminder_id = ?",
                        (current, row["reminder_id"]),
                    )
                    continue

                next_time = self._next_time(
                    row["remind_at"], row["repeat_type"], row["repeat_interval"]
                )
                while next_time <= current_dt:
                    next_time = self._next_time(
                        next_time.strftime(DATE_FORMAT),
                        row["repeat_type"],
                        row["repeat_interval"],
                    )
                connection.execute(
                    "UPDATE reminder SET remind_at = ?, last_notified_at = ? "
                    "WHERE reminder_id = ?",
                    (next_time.strftime(DATE_FORMAT), current, row["reminder_id"]),
                )

        if notify is not None:
            for notification in notifications:
                notify(notification)
        return notifications

    @staticmethod
    def _next_time(remind_at, repeat_type, interval):
        current = _parse_time(remind_at)
        if repeat_type == "daily":
            return current + datetime.timedelta(days=1)
        if repeat_type == "interval":
            return current + datetime.timedelta(minutes=int(interval))
        return current
