import os
from pathlib import Path

from dotenv import load_dotenv

# Определяем расположение проекта и файла тестовых настроек.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_ENV_FILE = PROJECT_ROOT / ".env.test"

# Тесты разрешено выполнять только с этой базой данных.
EXPECTED_TEST_DB = "beetles_test_db"

# Если тестовая конфигурация отсутствует, запрещаем запуск тестов.
if not TEST_ENV_FILE.is_file():
    raise RuntimeError(f"Не найден файл тестовой конфигурации: {TEST_ENV_FILE}")

# Сначала загружаем настройки из .env.test.
# override=True гарантирует, что тестовые значения заменят
# одноимённые переменные окружения, заданные ранее.
load_dotenv(TEST_ENV_FILE, override=True)

# Проверяем имя базы данных ДО импорта модуля database.
# Это первая защита от случайного запуска тестов на рабочей БД.
if os.getenv("DB_NAME") != EXPECTED_TEST_DB:
    raise RuntimeError(f"Тесты разрешены только на {EXPECTED_TEST_DB}")

# ВАЖНО: ЭТОТ ИМПОРТ НЕЛЬЗЯ ПЕРЕНОСИТЬ В НАЧАЛО ФАЙЛА!
#
# Модуль database читает настройки подключения при импорте.
# Поэтому сначала необходимо загрузить .env.test и проверить DB_NAME.
#
# Если импортировать database раньше, он может прочитать настройки
# рабочей базы данных вместо тестовой.
#
# noqa: E402 — разрешаем этот импорт после настройки окружения.
# Правило Ruff E402 остаётся включённым для остальных импортов.
from database import DB_CONFIG  # noqa: E402

# Дополнительная проверка: убеждаемся, что приложение действительно
# настроено на тестовую БД, а не только переменная окружения DB_NAME.
# Если база отличается от ожидаемой, тестирование прекращается.
if DB_CONFIG["database"] != EXPECTED_TEST_DB:
    raise RuntimeError(
        f"Опасная конфигурация: приложение подключается к "
        f"{DB_CONFIG['database']}, а ожидалась {EXPECTED_TEST_DB}"
    )
