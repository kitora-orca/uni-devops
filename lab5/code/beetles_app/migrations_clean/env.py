import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL

# Определяем путь к корню проекта и тестовому файлу окружения.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

#!!!!!!!!!!!!!!!!!! меняем окружение на .env.migration_clean
TEST_ENV_FILE = PROJECT_ROOT / ".env.migration_clean"
EXPECTED_TEST_DB = "beetles_migration_lab_db1"
#!!!!!!!!!!!!!!!!!! вот тут ИМЯ бд на которой схема, сюда мигрируем


# Запрещаем запуск миграций без тестовой конфигурации.
if not TEST_ENV_FILE.is_file():
    raise RuntimeError(f"Не найден файл тестовой конфигурации: {TEST_ENV_FILE}")

# Загружаем настройки именно тестовой базы, а не рабочей.
load_dotenv(TEST_ENV_FILE, override=True)

# Первая проверка: запрещаем миграции для любой другой базы.
if os.getenv("DB_NAME") != EXPECTED_TEST_DB:
    raise RuntimeError(
        f"Миграции разрешены только для базы {EXPECTED_TEST_DB}"
    )

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Формируем адрес подключения из тестовых переменных окружения.
database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME"),
)

# Вторая проверка: проверяем фактически сформированный URL.
if database_url.database != EXPECTED_TEST_DB:
    raise RuntimeError(
        f"Опасная конфигурация миграций: {database_url.database}"
    )

config.set_main_option(
    "sqlalchemy.url",
    database_url.render_as_string(hide_password=False).replace("%", "%%"),
)

# Пока не используем SQLAlchemy-модели для автоматической генерации миграций.
# Миграции будем создавать вручную.
target_metadata = None


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

