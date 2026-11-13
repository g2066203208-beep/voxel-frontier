# Read-only source verification and isolated Git worktree upload for the two user-owned DOCX files.
# THIS FILE HAS NOT BEEN EXECUTED BY CHATGPT: GitHub connector cannot stream DOCX bytes directly.
param(
    [Parameter(Mandatory = $true)][string]$RepoDir,
    [Parameter(Mandatory = $true)][string]$AugustDocx,
    [Parameter(Mandatory = $true)][string]$SeptemberDocx
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$branch = 'research/t080-seismic-integration-gates-20261022'
$destRoot = 'research/wind-tower/manuscript/source-uploads/2026-11-13/original-docx'
$augName = '10MW级陆上风机预应力混凝土钢混合塔架_R5_R2Z34新进展融合与主线收敛版_20260827.docx'
$sepName = '10MW级陆上风机预应力混凝土钢混合塔架_R2Z74_修正36组统计_Rainflow_DEL闭合_20260905_第四章修订版.docx'
$items = @(
    @{ Src = $AugustDocx; Name = $augName; SHA = 'da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9' },
    @{ Src = $SeptemberDocx; Name = $sepName; SHA = '5dfe6c70e768f13ebd90c2e561a768e9be143f571b240945b1f17807628512d0' }
)
function Git {
    param([string]$Repo, [string[]]$Argv)
    $s = & git -C $Repo @Argv 2>&1
    if ($LASTEXITCODE -ne 0) { throw "git command failed: $($Argv -join ' ') | $s" }
    return $s
}
foreach ($item in $items) {
    if (-not (Test-Path -LiteralPath $item.Src -PathType Leaf)) { throw "Missing source: $($item.Src)" }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $item.Src).Hash.ToLowerInvariant()
    if ($actual -ne $item.SHA) { throw "Wrong source SHA256: $($item.Name) got $actual" }
}
$RepoDir = (Resolve-Path -LiteralPath $RepoDir).Path
$remote = (Git -Repo $RepoDir -Argv @('remote','get-url','origin')).Trim()
if ($remote -notmatch 'g2066203208-beep/voxel-frontier') { throw "Wrong origin: $remote" }
[void](Git -Repo $RepoDir -Argv @('fetch','origin',$branch))
$tmp = Join-Path $env:TEMP ('thesis-originals-upload-' + [guid]::NewGuid().ToString('N'))
[void](Git -Repo $RepoDir -Argv @('worktree','add','--detach',$tmp,'FETCH_HEAD'))
try {
    $dest = Join-Path $tmp ($destRoot -replace '/','\')
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
    foreach ($item in $items) {
        $outPath = Join-Path $dest $item.Name
        if (Test-Path -LiteralPath $outPath) {
            $old = (Get-FileHash -Algorithm SHA256 -LiteralPath $outPath).Hash.ToLowerInvariant()
            if ($old -ne $item.SHA) { throw "Existing remote file has different bytes: $outPath" }
        } else { Copy-Item -LiteralPath $item.Src -Destination $outPath -ErrorAction Stop }
        $copySHA = (Get-FileHash -Algorithm SHA256 -LiteralPath $outPath).Hash.ToLowerInvariant()
        if ($copySHA -ne $item.SHA) { throw "Copy changed bytes: $outPath" }
    }
    [void](Git -Repo $tmp -Argv @('add','--',$destRoot))
    $changes = (Git -Repo $tmp -Argv @('status','--porcelain','--',$destRoot)) -join "`n"
    if ($changes.Trim().Length -gt 0) {
        [void](Git -Repo $tmp -Argv @('commit','-m','docs: preserve both unmodified source thesis DOCX binaries (SHA locked)'))
        [void](Git -Repo $tmp -Argv @('push','origin',('HEAD:refs/heads/'+$branch)))
    }
    [void](Git -Repo $tmp -Argv @('fetch','origin',$branch))
    foreach ($item in $items) {
        $rel = "$destRoot/$($item.Name)"
        $remoteBlob = (Git -Repo $tmp -Argv @('rev-parse',("FETCH_HEAD:"+$rel))).Trim()
        $localBlob = (Git -Repo $tmp -Argv @('hash-object',(Join-Path $dest $item.Name))).Trim()
        if ($remoteBlob -ne $localBlob) { throw "Remote blob identity mismatch: $rel" }
        Write-Output "BINARY_UPLOADED_VERIFIED $rel SHA256=$($item.SHA) GIT_BLOB=$remoteBlob"
    }
} finally {
    try { [void](Git -Repo $RepoDir -Argv @('worktree','remove','--force','--',$tmp)) }
    catch { Write-Warning "Manual worktree cleanup required: $tmp" }
}