#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Installs or removes the TallySync agent as a Windows Service.

.DESCRIPTION
    Copies the PyInstaller bundle to Program Files, registers the Windows
    Service, and configures automatic startup.

.PARAMETER Action
    install  (default) — install and start the service
    uninstall          — stop and remove the service
    reinstall          — uninstall then install

.EXAMPLE
    .\install.ps1
    .\install.ps1 -Action uninstall
    .\install.ps1 -Action reinstall
#>

param(
    [ValidateSet("install", "uninstall", "reinstall")]
    [string]$Action = "install"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ServiceName   = "TallySync"
$DisplayName   = "TallySync Agent"
$InstallDir    = "C:\Program Files\TallySync"
$ExePath       = Join-Path $InstallDir "tallysync.exe"
$ConfigSrc     = Join-Path $PSScriptRoot "config.yaml"
$BundleSrc     = Join-Path $PSScriptRoot "dist\tallysync"

function Install-TallySync {
    Write-Host "Installing $DisplayName to $InstallDir ..."

    if (-not (Test-Path $BundleSrc)) {
        throw "Build artifact not found: $BundleSrc. Run 'pyinstaller tallysync.spec' first."
    }

    # Copy bundle
    if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force }
    Copy-Item -Recurse $BundleSrc $InstallDir

    # Copy config if not already present
    $ConfigDest = Join-Path $InstallDir "config.yaml"
    if (-not (Test-Path $ConfigDest)) {
        Copy-Item $ConfigSrc $ConfigDest
        Write-Host "  Copied default config.yaml — edit $ConfigDest before starting the service."
    }

    # Register service
    & $ExePath service install | Out-Null
    Set-Service -Name $ServiceName -StartupType Automatic

    Write-Host "$DisplayName installed. Edit config at $ConfigDest then run:"
    Write-Host "  Start-Service $ServiceName"
}

function Uninstall-TallySync {
    Write-Host "Uninstalling $DisplayName ..."

    $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($svc) {
        if ($svc.Status -ne "Stopped") {
            Stop-Service -Name $ServiceName -Force
        }
        & $ExePath service uninstall | Out-Null
    }

    if (Test-Path $InstallDir) {
        Remove-Item $InstallDir -Recurse -Force
    }

    Write-Host "$DisplayName uninstalled."
}

switch ($Action) {
    "install"   { Install-TallySync }
    "uninstall" { Uninstall-TallySync }
    "reinstall" { Uninstall-TallySync; Install-TallySync }
}
