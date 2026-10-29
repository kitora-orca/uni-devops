
param(
    [Parameter(Position=0)]
    [ValidateSet("setup", "install", "run", "test", "migrate", "backup", "restore", "verify")]
    [string]$Command = "test"
)

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

switch ($Command) {
    "setup" {
        Write-Host "=== Первоначальная настройка проекта ==="

        if (-not (Test-Path ".venv\Scripts\python.exe")) {
            python -m venv .venv
            if ($LASTEXITCODE -ne 0) {
                throw "Ошибка создания виртуального окружения"
            }
        }

        & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            throw "Ошибка установки зависимостей"
        }

        if (-not (Test-Path ".env")) {
            if (Test-Path ".env.example") {
                Copy-Item ".env.example" ".env"
                Write-Host "Создан .env. Проверь настройки подключения к БД."
            }
            else {
                throw "Не найден ни .env, ни .env.example"
            }
        }

        if (-not (Test-Path "backups")) {
            New-Item -ItemType Directory -Path "backups" | Out-Null
        }

        Write-Host "=== Первоначальная настройка завершена ==="
    }

    "install" {
        & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            throw "Ошибка установки зависимостей"
        }
    }

    "run" {
        & ".\.venv\Scripts\python.exe" -m uvicorn main:app --reload
    }

    "test" {
        & ".\.venv\Scripts\python.exe" -m pytest
    }

    "migrate" {
        & ".\.venv\Scripts\python.exe" -m alembic upgrade head
    }

    "backup" {
        & ".\scripts\backup.ps1"
    }

    "restore" {
        $backupFile = Read-Host "Укажи путь к файлу резервной копии"
        & ".\scripts\restore.ps1" -BackupFile $backupFile
    }




    "verify" {
    $python = ".\.venv\Scripts\python.exe"

    Write-Host "=== 0. Проверка политики качества ==="
    & $python -m quality_policy.check_quality_policy
    if ($LASTEXITCODE -ne 0) {
    throw "Нарушена политика качества"
    }

    Write-Host "=== 1. Проверка Ruff ==="
    & $python -m ruff check .
    if ($LASTEXITCODE -ne 0) {
        throw "Проверка Ruff не пройдена"
    }

    Write-Host "=== 2. Проверка Bandit ==="
    & $python -m bandit main.py database.py
    if ($LASTEXITCODE -ne 0) {
        throw "Проверка Bandit не пройдена"
    }

    Write-Host "=== 3. Запуск тестов с покрытием ==="
    & $python -m pytest --cov=main --cov=database --cov-report=term-missing --cov-fail-under=40
    if ($LASTEXITCODE -ne 0) {
        throw "Тесты или проверка покрытия не пройдены"
    }

    Write-Host "=== Все проверки успешно пройдены ==="
}





}
