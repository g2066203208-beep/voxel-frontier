param(
    [ValidateSet('Debug','Release')]
    [string]$Configuration = 'Debug'
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$buildScript = Join-Path $PSScriptRoot 'build-game.ps1'
$exe = Join-Path $repo "build\vscode-windows\$Configuration\voxel_frontier.exe"

& $buildScript -Configuration $Configuration
if ($LASTEXITCODE -ne 0) { throw "Build gate failed with exit code $LASTEXITCODE." }

if (-not (Test-Path $exe)) { throw "Executable not found: $exe" }
Write-Host "Launching: $exe"
Start-Process -FilePath $exe -WorkingDirectory $repo
