# 报时鸟 App（第三阶段最小闭环）

本目录在上一版 `AgentProject` 基础上实现第三阶段第一块功能：

```text
自然语言新增提醒 -> SQLite 持久化 -> 到点扫描触发
```

保留上一版的四个核心模块，不复制、不改写：

- `Agent`
- `Planner`
- `ToolBox`
- `Memory`

本阶段新增：

- `reminder_scheduler.py`：提醒存储、到期扫描、once/daily/interval 重排；
- `reminder_planner.py`：识别常见提醒说法，其余请求交回上一版规划器；
- `reminder_toolbox.py`：在原有 9 个工具上增加课表查询，工具总数保持 10；
- `web_server.py`：REST API、到期事件推送和后台值守线程；
- `device.py`：ESP32 设备接口与可运行的模拟设备状态；
- `web/`：真实可交互网页，支持文字、浏览器语音、提醒面板和主动弹窗；
- `app.py`：命令行入口与值守扫描。

## 运行

在仓库根目录执行：

```powershell
python DeskBirdApp/app.py "提醒我 明天 22:00 交软工作业"
python DeskBirdApp/app.py "每天 21:00 提醒背单词"
python DeskBirdApp/app.py "每 45 分钟提醒我起来喝水"
python DeskBirdApp/app.py "查看提醒"
python DeskBirdApp/app.py --tick
python DeskBirdApp/app.py --watch 5
```

不带消息时进入交互模式。`--watch 5` 表示每 5 秒检查一次到期提醒。

## 网页运行

```powershell
cd DeskBirdApp
.\run_alpha.ps1
```

浏览器打开 <http://127.0.0.1:8765>。网页支持：

- 自然语言对话和原 9 个工具；
- 课表查询；
- 一次性、每日、固定间隔提醒；
- 提醒完成与 10 分钟推迟；
- 到期主动弹窗和语音播报；
- 浏览器语音识别，失败时保留文字输入；
- 工具状态、长期记忆查看。
- 设备在线状态与离线降级展示。

## 测试

```powershell
python -m unittest discover -s DeskBirdApp/tests -t DeskBirdApp -v
.\DeskBirdApp\verify_alpha.ps1
```

## 当前范围

已验证：

- 一次性、每日、固定间隔提醒；
- 提醒持久化、完成、推迟；
- 原有计算器等工具仍可调用；
- 10 个工具的网页与 API 可调用；
- 到期事件可触发弹窗与语音；
- 26 个自动化测试通过。

尚未实现：

- ESP32 硬件联动；
- 云端部署与大模型接口现场联调；
- 14 天冲刺的团队成员原始视频和亲笔过程材料。
