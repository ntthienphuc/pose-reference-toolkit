param([int]$Port = 8010)
$ErrorActionPreference = 'Stop'
$PoseReferenceRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $PoseReferenceRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed' }
}
& '.venv\Scripts\python.exe' -m pip install -e '.[server]'
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
if (-not (Test-Path -LiteralPath 'demo_run')) {
    & '.venv\Scripts\pose-ref.exe' demo --out demo_run
    if ($LASTEXITCODE -ne 0) { throw 'Demo generation failed' }
}
& '.venv\Scripts\pose-ref.exe' serve --bank demo_run/bank --policy demo_run/policy.json --demo-root demo_run --port $Port
