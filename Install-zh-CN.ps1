param([switch]$Restore)
$ErrorActionPreference = 'Stop'
$appDirectory = Join-Path $env:LOCALAPPDATA 'Programs\antigravity'
if (Get-Process -Name Antigravity -ErrorAction SilentlyContinue) {
    throw 'Please save your work and exit Antigravity from its tray menu before running this script. No process was stopped.'
}
$pythonCommand = if (Get-Command py -ErrorAction SilentlyContinue) { (Get-Command py).Source } elseif (Get-Command python -ErrorAction SilentlyContinue) { (Get-Command python).Source } else {
    throw 'Python 3.11+ is required. Please install Python and add it to PATH.'
}
if ($Restore) {
    & $pythonCommand (Join-Path $PSScriptRoot 'patcher.py') --app-dir $appDirectory --restore
} else {
    $version = (& $pythonCommand -c "import sys; sys.path.insert(0, r'$PSScriptRoot'); import patcher; print(patcher.VERSION)")
    if (-not $version) { $version = '2.15.1' }
    $bundleDirectory = Join-Path $PSScriptRoot "build\$version-release"
    if (-not (Test-Path -LiteralPath $bundleDirectory)) {
        & $pythonCommand (Join-Path $PSScriptRoot 'patcher.py') --app-dir $appDirectory --build $bundleDirectory
        if ($LASTEXITCODE -ne 0) { throw 'Build failed; original installation has not been changed.' }
    }
    & $pythonCommand (Join-Path $PSScriptRoot 'patcher.py') --app-dir $appDirectory --install $bundleDirectory
}
if ($LASTEXITCODE -ne 0) { throw 'Patch operation failed. See the error above.' }
Start-Process -FilePath (Join-Path $appDirectory 'Antigravity.exe') -WindowStyle Hidden
