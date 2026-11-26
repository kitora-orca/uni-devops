
.PHONY: container-check

container-check:
	@echo "=== 1. Проверка конфигурации Docker Compose ==="
	@sudo docker compose config --quiet
	@echo "=== 2. Проверка работающих контейнеров ==="
	@sudo docker compose ps
	@sudo docker compose exec -T app true
	@sudo docker compose exec -T db true
	@echo "=== 3. Проверка PostgreSQL ==="
	@sudo docker compose exec -T db sh -c 'pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'
	@echo "=== 4. Проверка FastAPI ==="
	@curl --fail --silent --show-error http://localhost:8000/health
	@echo
	@echo "=== 5. Проверка пользователя приложения ==="
	@test "$$(sudo docker compose exec -T app whoami)" = "appuser"
	@echo "Приложение работает от appuser"
	@echo "=== 6. Проверка подключения к PostgreSQL ==="
	@sudo docker compose exec -T app python -c 'from database import get_connection; conn = get_connection(); conn.close(); print("Подключение к PostgreSQL: OK")'
	@echo "=== Все проверки успешно пройдены ==="
