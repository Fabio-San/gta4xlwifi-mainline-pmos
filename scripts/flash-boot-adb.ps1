# Scrive un boot.img nella partizione boot via adb, dalla Lineage Recovery.
#
# Perche' da recovery: con la ROM stock `adb root` e' disabilitato e
# `fastboot fetch` non espone la partizione boot; la recovery invece espone
# adbd come root (uid=0) e permette dd.
#
# Prima del flash fa SEMPRE un backup verificato della partizione boot
# attuale in backups/live/boot-<timestamp>.img (61 MB, sha256 confrontato).
# Usa -SkipBackup solo se il backup esiste gia' ed e' stato verificato.
#
# Uso:
#   pwsh -File scripts/flash-boot-adb.ps1 -Image flash\boot-debug-telnet.img
#   pwsh -File scripts/flash-boot-adb.ps1 -Image ... -Reboot
#
# Il flash e' verificato: SHA256 del file, SHA256 riletto dalla partizione.
# NON tocca bootloader, dtbo, recovery, vbmeta.

param(
    [Parameter(Mandatory = $true)][string]$Image,
    [switch]$Reboot,
    [switch]$SkipBackup,
    [string]$Serial = ''
)

$ErrorActionPreference = 'Stop'
$BootPartitionBytes = 61865984
$RemoteTmp = '/tmp/boot.img'
$ProjectRoot = Split-Path -Parent $PSScriptRoot

if ($Serial) { $env:ANDROID_SERIAL = $Serial }

function Fail([string]$msg) { Write-Error $msg; exit 1 }

if (-not (Test-Path $Image)) { Fail "immagine non trovata: $Image" }
$img = Get-Item $Image
if ($img.Length -gt $BootPartitionBytes) {
    Fail ("boot.img troppo grande: {0} byte (limite {1})" -f $img.Length, $BootPartitionBytes)
}
if ($img.Length -lt 1024) { Fail "file sospettosamente piccolo: $($img.Length) byte" }

$header = [System.IO.File]::ReadAllBytes($img.FullName)[0..7]
if ([System.Text.Encoding]::ASCII.GetString($header) -ne 'ANDROID!') {
    Fail "header non valido: atteso 'ANDROID!'"
}

$devices = @(adb devices | Select-Object -Skip 1 | Where-Object { $_ -match '\t(\w+)$' })
if ($Serial) { $devices = @($devices | Where-Object { $_ -match "^$([regex]::Escape($Serial))\t" }) }
if ($devices.Count -ne 1) { Fail "atteso il dispositivo $Serial in recovery, trovati $($devices.Count)" }
if ($devices[0] -notmatch 'recovery$') {
    Fail "il dispositivo non e' in recovery. Riavvia in Lineage Recovery (Vol Up + Power) e riprova."
}

# --- backup verificato della partizione boot attuale -----------------------
if (-not $SkipBackup) {
    $backupDir = Join-Path $ProjectRoot 'backups/live'
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    $stamp = (Get-Date).ToString('yyyyMMdd-HHmmss')
    $remoteBak = '/tmp/boot-backup.img'
    $localBak = Join-Path $backupDir "boot-$stamp.img"

    Write-Host "--- backup partizione boot -> $localBak"
    adb shell "dd if=/dev/block/by-name/boot of=$remoteBak bs=1M" | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "backup: dd fallito" }
    adb shell "sync"
    adb pull $remoteBak $localBak | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "backup: pull fallito" }

    $remoteBakSha = (adb shell "sha256sum $remoteBak" | ForEach-Object { ($_ -split '\s+')[0] }).Trim()
    $localBakSha = (Get-FileHash $localBak -Algorithm SHA256).Hash.ToLower()
    $bakLen = (Get-Item $localBak).Length
    adb shell "rm -f $remoteBak" | Out-Null

    if ($bakLen -ne $BootPartitionBytes) { Fail ("backup: dimensione inattesa {0} (attesa {1})" -f $bakLen, $BootPartitionBytes) }
    if ($remoteBakSha -ne $localBakSha) { Fail "backup: sha256 locale/remoto diverso" }
    Write-Host "backup OK: $bakLen byte, sha256 $localBakSha"
}

$localSha = (Get-FileHash $Image -Algorithm SHA256).Hash.ToLower()
Write-Host "immagine : $($img.FullName) ($($img.Length) byte)"
Write-Host "sha256   : $localSha"

Write-Host "--- push in $RemoteTmp"
adb push $Image $RemoteTmp
if ($LASTEXITCODE -ne 0) { Fail "adb push fallito" }

$remoteSha = (adb shell "sha256sum $RemoteTmp" | ForEach-Object { ($_ -split '\s+')[0] }).Trim()
if ($remoteSha -ne $localSha) { Fail "sha256 remoto diverso: $remoteSha" }
Write-Host "sha256 remoto OK"

Write-Host "--- dd su /dev/block/by-name/boot"
adb shell "dd if=$RemoteTmp of=/dev/block/by-name/boot bs=1M"
if ($LASTEXITCODE -ne 0) { Fail "dd fallito" }
adb shell "sync"

Write-Host "--- verifica rilettura ($($img.Length) byte)"
$readSha = (adb shell "dd if=/dev/block/by-name/boot bs=1M 2>/dev/null | head -c $($img.Length) | sha256sum" |
    ForEach-Object { ($_ -split '\s+')[0] }).Trim()
if ($readSha -ne $localSha) { Fail "rilettura diversa: $readSha (boot NON valido)" }
Write-Host "verifica OK: partizione boot identica all'immagine"

adb shell "rm -f $RemoteTmp" | Out-Null

if ($Reboot) {
    Write-Host "--- reboot"
    adb reboot
}
