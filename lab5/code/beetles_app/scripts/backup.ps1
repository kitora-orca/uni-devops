$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$envFile = Join-Path $projectRoot ".env"

if (-not (Test-Path $envFile)) {
    throw "Не найден файл .env"
}

foreach ($line in Get-Content $envFile) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

$backupDir = Join-Path $projectRoot "backups"
New-Item -ItemType Directory -Force $backupDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path $backupDir "beetles_$timestamp.dump"

pg_dump `
    -h $env:DB_HOST `
    -p $env:DB_PORT `
    -U $env:DB_USER `
    -d $env:DB_NAME `
    -F c `
    -f $backupFile

if ($LASTEXITCODE -ne 0) {
    throw "Резервное копирование завершилось с ошибкой"
}

Write-Host "Резервная копия создана: $backupFile"
