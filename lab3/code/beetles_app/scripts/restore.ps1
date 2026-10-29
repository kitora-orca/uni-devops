param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$backupPath = (Resolve-Path $BackupFile).Path

$confirmation = Read-Host "Восстановление может заменить существующие объекты. Для продолжения введи RESTORE"

if ($confirmation -cne "RESTORE") {
    Write-Host "Восстановление отменено."
    exit 0
}

$envFile = Join-Path $projectRoot ".env"

if (-not (Test-Path $envFile)) {
    throw "Не найден файл .env"
}

foreach ($line in Get-Content $envFile) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

pg_restore `
    -h $env:DB_HOST `
    -p $env:DB_PORT `
    -U $env:DB_USER `
    -d $env:DB_NAME `
    --clean `
    --if-exists `
    --no-owner `
    --no-acl `
    $backupPath

if ($LASTEXITCODE -ne 0) {
    throw "Восстановление завершилось с ошибкой"
}

Write-Host "Восстановление завершено."
