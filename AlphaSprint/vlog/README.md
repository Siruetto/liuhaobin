# 报时鸟 Alpha 冲刺 Vlog

## 成片

- `报时鸟-Alpha冲刺Vlog.mp4`
- 目标时长：3:00
- 旁白：系统中文 TTS
- 画面：真实产品截图、Day 1 日志、GitHub 协作记录、架构与测试数据

## 现场必须补录的原生素材

作业要求“将每天拍摄的视频进行整合”。以下内容无法用代码生成，必须由团队真实拍摄：

- 每日 10 分钟站立会，每天 20-30 秒。
- 每位成员说一句当天完成、问题和计划。
- 队友讨论、白板或屏幕协作的过程。
- 7 名成员各 5-10 秒的冲刺体会。
- 可选：ESP32 点亮、播报和硬件联调画面。

## 素材命名

```text
raw/2026-11-23-站立会.mp4
raw/2026-11-23-刘浩彬.mp4
raw/2026-11-24-站立会.mp4
...
raw/2026-12-06-团队复盘.mp4
```

## 复现当前 3 分钟版本

```powershell
cd liuhaobin\AlphaSprint\vlog
.\create_narration.ps1
python -m http.server 8790 --directory ..
```

另开一个终端：

```powershell
& "C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1116-1220-0_26.1116.1220.0_x64__3k8sg7r9htsxt\dependencies\node\bin\node.exe" build_vlog.mjs
```

旁白生成使用 `edge-tts`，只在重新制作视频时需要联网和临时依赖；已经生成的成片不需要网络。

真实素材到齐后，把 `raw/` 中的片段插入第 147-170 秒的协作证据段落，并替换 Day 1 之外的计划展示。最终仍需保持总时长 3 分钟。
