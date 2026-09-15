param([switch]$Restore)
$ErrorActionPreference = 'Stop'
$appDirectory = Join-Path $env:LOCALAPPDATA 'Programs\antigravity'
if (Get-Process -Name Antigravity -ErrorAction SilentlyContinue) {
    throw 'Please save your work and exit Antigravity from its tray menu before running this script. No process was stopped.'
}
$pythonCommand = if (Get-Command python -ErrorAction SilentlyContinue) { (Get-Command python).Source } elseif (Get-Command py -ErrorAction SilentlyContinue) { (Get-Command py).Source } else {
    throw '未检测到 Python 环境，请安装 Python 3.11+ 并勾选添加到系统 PATH 环境变量后重试。'
}
if ($Restore) {
    & $pythonCommand (Join-Path $PSScriptRoot 'patcher.py') --app-dir $appDirectory --restore
} else {
    $bundleDirectory = Join-Path $PSScriptRoot 'build\2.13.0-release'
    if (-not (Test-Path -LiteralPath $bundleDirectory)) {
        & $pythonCommand (Join-Path $PSScriptRoot 'patcher.py') --app-dir $appDirectory --build $bundleDirectory
        if ($LASTEXITCODE -ne 0) { throw 'Build failed; original installation has not been changed.' }
    }
    & $pythonCommand (Join-Path $PSScriptRoot 'patcher.py') --app-dir $appDirectory --install $bundleDirectory
}
if ($LASTEXITCODE -ne 0) { throw 'Patch operation failed. See the error above.' }
Start-Process -FilePath (Join-Path $appDirectory 'Antigravity.exe') -WindowStyle Hidden
