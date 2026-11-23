$ErrorActionPreference = "Stop"
$appRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$testRoot = Join-Path $appRoot "tests"
$runRoot = Join-Path $appRoot "data\verify"
$db = Join-Path $runRoot "verify.db"
$memory = Join-Path $runRoot "verify-memory.json"
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null

Write-Host "[1/3] Running automated tests"
python -m unittest discover -s $testRoot -t $appRoot -v

Write-Host "[2/3] Starting the web app"
$process = Start-Process python `
  -ArgumentList @(
    (Join-Path $appRoot "web_server.py"),
    "--port", "8766",
    "--db", $db,
    "--memory", $memory
  ) `
  -WorkingDirectory $appRoot `
  -WindowStyle Hidden `
  -PassThru

try {
  $ready = $false
  for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
      $status = Invoke-RestMethod "http://127.0.0.1:8766/api/status" -TimeoutSec 2
      $ready = $true
      break
    } catch {
      Start-Sleep -Milliseconds 300
    }
  }
  if (-not $ready) {
    throw "Web app did not become ready"
  }

  Write-Host "[3/3] Checking the public API"
  if ($status.tools -ne 10) {
    throw "Expected 10 tools, got $($status.tools)"
  }
  $requestBody = [System.Text.Encoding]::UTF8.GetBytes('{"message":"1+1"}')
  $chat = Invoke-RestMethod `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body $requestBody `
    "http://127.0.0.1:8766/api/chat"
  if ($chat.reply -ne "2") {
    throw "Calculator check failed: $($chat.reply)"
  }
  Write-Host "Verification passed"
} finally {
  Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
}
