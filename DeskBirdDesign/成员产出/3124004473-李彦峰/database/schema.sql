-- 报时鸟数据库建表脚本（SQLite），与《报时鸟数据库设计说明书》一致

PRAGMA foreign_keys = ON;

CREATE TABLE user (
    user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    preference  TEXT,
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE reminder (
    reminder_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER REFERENCES user(user_id),
    content           TEXT NOT NULL,
    remind_at         TEXT NOT NULL,
    repeat_type       TEXT NOT NULL DEFAULT 'none'
                      CHECK (repeat_type IN ('none', 'daily', 'interval')),
    repeat_interval   INTEGER NOT NULL DEFAULT 0,
    status            TEXT NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending', 'done')),
    last_notified_at  TEXT
);

CREATE TABLE todo_item (
    todo_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES user(user_id),
    text        TEXT NOT NULL,
    done        INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)),
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE schedule (
    schedule_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER REFERENCES user(user_id),
    course_name  TEXT NOT NULL,
    day_of_week  INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    start_time   TEXT NOT NULL,
    end_time     TEXT NOT NULL,
    location     TEXT,
    weeks        TEXT
);

CREATE TABLE device (
    device_id  TEXT PRIMARY KEY,
    user_id    INTEGER REFERENCES user(user_id),
    name       TEXT,
    online     INTEGER NOT NULL DEFAULT 0 CHECK (online IN (0, 1)),
    last_seen  TEXT
);

CREATE TABLE conversation (
    turn_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES user(user_id),
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX idx_reminder_due ON reminder(remind_at, status);
CREATE INDEX idx_schedule_day ON schedule(day_of_week);
