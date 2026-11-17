# 李彦峰 · 数据库建表脚本

对应角色：后端 / 运维。本目录是报时鸟的建表 SQL（SQLite），与《报时鸟数据库设计说明书》一致：

- `schema.sql`：user / reminder / todo_item / schedule / device / conversation 六张表，含外键、CHECK 约束和两个查询索引。

本地验证：

```bash
sqlite3 deskbird.db < schema.sql
sqlite3 deskbird.db ".tables"
```
