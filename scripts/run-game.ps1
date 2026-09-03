param(
    [ValidateSet('Debug','Release')]
    [string]$Configuration = 'Debug'
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$native = Join-Path $repo 'native'
$preset = if ($Configuration -eq 'Release') { 'windows-release' } else { 'windows-debug' }
$exe = Join-Path $repo "build\vscode-windows\$Configuration\voxel_frontier.exe"

Write-Host "=== Voxel Frontier $Configuration ==="
Push-Location $native
try {
    cmake --preset $preset
    if ($LASTEXITCODE -ne 0) { throw 'CMake configure failed.' }

    cmake --build --preset $preset --parallel
    if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }

    ctest --preset $preset
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
}
finally {
    Pop-Location
}

if (-not (Test-Path $exe)) { throw "Executable not found: $exe" }
Write-Host "Launching: $exe"
Start-Process -FilePath $exe -WorkingDirectory $repo
