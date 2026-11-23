$ErrorActionPreference = "Stop"
$vlogRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = "C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1116-1220-0_26.1116.1220.0_x64__3k8sg7r9htsxt\dependencies\python\python.exe"
$workspaceRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $vlogRoot))
$ttsDeps = Join-Path $workspaceRoot ".audit\pydeps"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = $ttsDeps
$env:FFMPEG_EXE = "C:\Program Files\kedou\ffmpeg.exe"
& $python (Join-Path $vlogRoot "generate_edge_narration.py")
