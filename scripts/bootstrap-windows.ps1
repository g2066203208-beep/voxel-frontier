param(
    [switch]$InstallMissing,
    [switch]$SkipExtensions
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

function Has-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WingetPackage([string]$Id, [string[]]$ExtraArgs = @()) {
    if (-not (Has-Command 'winget')) {
        throw "winget is required to install missing dependency: $Id"
    }
    $args = @('install', '--id', $Id, '--exact', '--accept-package-agreements', '--accept-source-agreements', '--silent') + $ExtraArgs
    & winget @args
    if ($LASTEXITCODE -ne 0) { throw "winget failed for $Id with exit code $LASTEXITCODE" }
}

Write-Host '=== Voxel Frontier Windows bootstrap ==='

if (-not (Has-Command 'cmake')) {
    if (-not $InstallMissing) { throw 'CMake not found. Re-run with -InstallMissing.' }
    Install-WingetPackage 'Kitware.CMake'
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}

$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$hasMsvc = $false
if (Test-Path $vswhere) {
    $vsPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    $hasMsvc = -not [string]::IsNullOrWhiteSpace(($vsPath | Out-String))
}

if (-not $hasMsvc) {
    if (-not $InstallMissing) { throw 'MSVC C++ Build Tools not found. Re-run with -InstallMissing.' }
    Install-WingetPackage 'Microsoft.VisualStudio.2022.BuildTools' @('--override', '--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended')
}

if (-not $SkipExtensions -and (Has-Command 'code')) {
    & code --install-extension ms-vscode.cpptools --force
    & code --install-extension ms-vscode.cmake-tools --force
}

Write-Host ''
Write-Host 'CMake:'
& cmake --version

if (Test-Path $vswhere) {
    Write-Host ''
    Write-Host 'MSVC installation:'
    & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
}

Write-Host ''
Write-Host 'Bootstrap PASS.'
Write-Host 'Next: run scripts/run-game.ps1 or press F5 in VS Code.'
