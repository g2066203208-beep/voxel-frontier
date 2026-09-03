param(
    [ValidateSet('Debug','Release')]
    [string]$Configuration = 'Debug',
    [switch]$SkipTests
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$native = Join-Path $repo 'native'
$preset = if ($Configuration -eq 'Release') { 'windows-release' } else { 'windows-debug' }
$exe = Join-Path $repo "build\vscode-windows\$Configuration\voxel_frontier.exe"

function Resolve-Tool([string]$Name, [string[]]$Candidates) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($candidate in $Candidates) {
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path $candidate)) {
            return $candidate
        }
    }
    throw "$Name was not found in PATH or known install locations. Run scripts/bootstrap-windows.ps1 -InstallMissing."
}

$cmake = Resolve-Tool 'cmake.exe' @(
    'C:\Program Files\CMake\bin\cmake.exe',
    'C:\Program Files (x86)\CMake\bin\cmake.exe'
)
$ctest = Resolve-Tool 'ctest.exe' @(
    (Join-Path (Split-Path -Parent $cmake) 'ctest.exe'),
    'C:\Program Files\CMake\bin\ctest.exe',
    'C:\Program Files (x86)\CMake\bin\ctest.exe'
)

Write-Host "=== Voxel Frontier $Configuration build gate ==="
Write-Host "CMake: $cmake"

Push-Location $native
try {
    & $cmake --preset $preset
    if ($LASTEXITCODE -ne 0) { throw "CMake configure failed with exit code $LASTEXITCODE." }

    & $cmake --build --preset $preset --parallel
    if ($LASTEXITCODE -ne 0) { throw "Build failed with exit code $LASTEXITCODE." }

    if (-not $SkipTests) {
        & $ctest --preset $preset --output-on-failure
        if ($LASTEXITCODE -ne 0) { throw "Tests failed with exit code $LASTEXITCODE." }
    }
}
finally {
    Pop-Location
}

if (-not (Test-Path $exe)) { throw "Executable not found after successful build: $exe" }
Write-Host "Build gate PASS: $exe"
