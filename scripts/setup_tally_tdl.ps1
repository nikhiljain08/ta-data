# TallySync — TDL setup helper
# Copies tallysync_exports.tdl to a location you choose and opens TallyPrime
# at the TDL & Add-ons screen so you can register the file.
#
# Usage (from the repo root):
#   .\scripts\setup_tally_tdl.ps1
#
# What this script does
# ---------------------
# 1. Copies tallysync_exports.tdl to C:\TallySync\ (created if absent)
# 2. Prints the exact path to register in TallyPrime
# 3. Opens TallyPrime if it can be found (so you can paste the path)
#
# Manual alternative (if script is not needed)
# --------------------------------------------
# Just note the full path to tallysync_exports.tdl and follow the steps
# printed at the end of this script.

$ErrorActionPreference = "Stop"

# ── 1. Determine paths ─────────────────────────────────────────────────────────

$repoRoot  = Split-Path -Parent $PSScriptRoot
$srcTdl    = Join-Path $repoRoot "tallysync_exports.tdl"
$destDir   = "C:\TallySync"
$destTdl   = Join-Path $destDir "tallysync_exports.tdl"

if (-not (Test-Path $srcTdl)) {
    Write-Error "tallysync_exports.tdl not found at: $srcTdl"
    exit 1
}

# ── 2. Copy TDL file ───────────────────────────────────────────────────────────

New-Item -ItemType Directory -Force -Path $destDir | Out-Null
Copy-Item -Path $srcTdl -Destination $destTdl -Force
Write-Host "TDL file copied to: $destTdl" -ForegroundColor Green

# ── 3. Try to locate TallyPrime executable ────────────────────────────────────

$tallyExePaths = @(
    "C:\Program Files\TallyPrime\tally.exe",
    "C:\Program Files (x86)\TallyPrime\tally.exe",
    "C:\TallyPrime\tally.exe",
    "C:\Tally\TallyPrime\tally.exe",
    "C:\Program Files\Tally\TallyPrime\tally.exe"
)

$tallyExe = $tallyExePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

# ── 4. Print instructions ─────────────────────────────────────────────────────

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  TallySync TDL Setup — Manual steps required in TallyPrime" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "TDL file path (copy this):" -ForegroundColor Yellow
Write-Host "  $destTdl" -ForegroundColor White
Write-Host ""
Write-Host "Steps to load in TallyPrime:" -ForegroundColor Yellow
Write-Host "  1. Open TallyPrime (if not already open)"
Write-Host "  2. At Gateway of Tally, press F12 (Configure)"
Write-Host "  3. Select 'TDL & Add-On Files'"
Write-Host "  4. Under 'Load TDL files on Startup', enter the path above"
Write-Host "  5. Press Ctrl+A to accept"
Write-Host "  6. Restart TallyPrime (close and reopen)"
Write-Host ""
Write-Host "After restart, run:  .venv\Scripts\python -m app.main run" -ForegroundColor Green
Write-Host ""

if ($tallyExe) {
    $answer = Read-Host "TallyPrime found at '$tallyExe'. Open it now? [y/N]"
    if ($answer -match '^[Yy]') {
        Start-Process $tallyExe
        Write-Host "TallyPrime launched." -ForegroundColor Green
    }
} else {
    Write-Host "TallyPrime executable not found in standard paths." -ForegroundColor Yellow
    Write-Host "Open TallyPrime manually and follow the steps above."
}
