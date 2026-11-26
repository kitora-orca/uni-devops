import uuid
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from database import get_connection
from main import (
    CatchCreate,
    ExpeditionCreate,
    app,
    create_catch,
    create_expedition,
    hash_password,
    verify_password,
)


# Вспомогательный класс для имитации авторизованного пользователя.
# Позволяет тестировать функции без настоящего входа в систему и обращения к БД.
class FakeRequest:
    """Имитация авторизованного пользователя без обращения к БД."""

    def __init__(self):
        self.session = {
            "user_id": 1,
            "username": "test_user",
        }


# ============================================================
# БЛОК 1. МОДУЛЬНЫЕ ТЕСТЫ
# Проверяют отдельные функции и валидацию входных данных.
# ============================================================


# Тест 1. Проверяет, что пароль хранится не в открытом виде.
# Функция hash_password должна преобразовать исходный пароль
# в хеш, который отличается от исходного текста и содержит разделитель.
def test_password_hash_is_not_plain_text():
    password = "test_password"  # noqa: S105 — фиктивный пароль для теста . Здесь используется тестовый пароль, а не настоящий секрет
    password_hash = hash_password(password)

    assert password_hash != password
    assert "$" in password_hash


# Тест 2. Проверяет успешную проверку правильного пароля.
# Сначала создаётся хеш пароля, затем verify_password
# должна подтвердить соответствие исходного пароля этому хешу.
def test_password_verification_success():
    password = "test_password"  # noqa: S105 — фиктивный пароль для теста. Здесь используется тестовый пароль, а не настоящий секрет
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


# Тест 3. Проверяет отклонение неправильного пароля.
# Хеш создаётся для correct_password, поэтому проверка
# wrong_password должна вернуть False.
def test_password_verification_wrong_password():
    password_hash = hash_password("correct_password")

    assert (
        verify_password(
            "wrong_password",
            password_hash,
        )
        is False
    )


# Тест 4. Проверяет обработку некорректного хеша.
# Если передана строка, которая не является допустимым хешем,
# функция проверки пароля должна безопасно вернуть False,
# а не завершиться необработанной ошибкой.
def test_password_verification_invalid_hash():
    assert verify_password("password", "invalid_hash") is False


# Тест 5. Проверяет валидацию времени экспедиции.
# Время окончания задано раньше времени начала.
# Функция create_expedition должна отклонить такие данные
# и вызвать HTTPException со статусом 400.
def test_expedition_rejects_end_before_start():
    expedition = ExpeditionCreate(
        team_id=1,
        place_id=1,
        start_time=datetime(2026, 6, 10, 12, 0),
        end_time=datetime(2026, 6, 10, 10, 0),
    )

    with pytest.raises(HTTPException) as error:
        create_expedition(expedition, FakeRequest())

    assert error.value.status_code == 400


# Тест 6. Проверяет, что количество пойманных жуков должно быть положительным.
# pytest.mark.parametrize запускает один тест с тремя значениями:
# 0, -1 и -10.
# Для каждого значения функция create_catch должна вызвать
# HTTPException со статусом 400.
@pytest.mark.parametrize("quantity", [0, -1, -10])
def test_catch_rejects_non_positive_quantity(quantity):
    catch = CatchCreate(
        expedition_id=1,
        species_id=1,
        quantity=quantity,
    )

    with pytest.raises(HTTPException) as error:
        create_catch(catch, FakeRequest())

    assert error.value.status_code == 400


# ============================================================
# БЛОК 2. ТЕСТЫ HTTP-МАРШРУТОВ И АВТОРИЗАЦИИ
# Проверяют ответы приложения на HTTP-запросы.
# ============================================================

"""блок новых тестов прибавка 1"""



# Создаём тестовый HTTP-клиент FastAPI.
# С его помощью можно обращаться к маршрутам приложения
# без ручного запуска сервера.
api_client = TestClient(app)

# Тест нового функционального изменения для пункта 15.
def test_health_check():
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}



# Тест 7. Проверяет доступность страницы авторизации.
# GET-запрос к /auth должен вернуть HTTP 200,
# то есть страница успешно открывается.
def test_auth_page_opens():
    response = api_client.get("/auth")
    assert response.status_code == 200


# Тест 8. Проверяет перенаправление неавторизованного пользователя.
# При обращении к главной странице без входа в систему
# приложение должно перенаправить пользователя на страницу /auth.
# follow_redirects=False позволяет проверить сам ответ перенаправления,
# не переходя автоматически на другую страницу.
def test_home_redirects_unauthenticated_user():
    response = api_client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "/auth" in response.headers.get("location", "")


# Тест 9. Проверяет защиту API-маршрутов авторизацией.
# Параметризация запускает тест отдельно для каждого указанного пути.
# Без авторизации каждый GET-запрос должен вернуть статус 401.
@pytest.mark.parametrize(
    "path",
    [
        "/api/me",
        "/api/teams",
        "/api/places",
        "/api/species",
        "/api/expeditions",
        "/api/catch",
        "/api/catch/report",
    ],
)
def test_api_requires_authentication(path):
    response = api_client.get(path)
    assert response.status_code == 401

    """блок новых тестов прибавка 2"""





# ============================================================
# БЛОК 3. ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# Проверяют работу нескольких частей приложения совместно:
# HTTP-маршрутов, авторизации и PostgreSQL.
# Для тестовых записей используются уникальные имена.
# В блоках finally тестовые данные очищаются из БД.
# ============================================================


# Тест 10. Проверяет создание и чтение справочных данных.
# Создаёт отдельного тестового пользователя, выполняет вход,
# добавляет команду, место и вид жука через API.
# Затем проверяет, что все три записи возвращаются GET-запросами.
# В finally удаляет созданные тестовые записи и завершает сессию.
def test_integration_create_and_read_reference_data():
    """Проверяет создание и чтение команды, места и вида жука."""
    suffix = uuid.uuid4().hex[:12]
    team_name = f"pytest_team_{suffix}"
    place_name = f"pytest_place_{suffix}"
    species_name = f"pytest_species_{suffix}"

    created_ids = {}

    try:
        # Создаём тестового пользователя через API и входим.
        username = f"pytest_user_{suffix}"
        response = api_client.post(
            "/api/register",
            json={"username": username, "password": "test_password"},
        )
        assert response.status_code == 200, response.text

        response = api_client.post(
            "/api/login",
            json={"username": username, "password": "test_password"},
        )
        assert response.status_code == 200, response.text

        # Создаём команду через POST /api/teams.
        # Сохраняем ID, чтобы позднее проверить и удалить эту запись.
        response = api_client.post("/api/teams", json={"team_name": team_name})
        assert response.status_code == 200, response.text
        created_ids["team_id"] = response.json()["team_id"]

        # Создаём место через POST /api/places.
        # Сохраняем ID созданного места.
        response = api_client.post("/api/places", json={"place_name": place_name})
        assert response.status_code == 200, response.text
        created_ids["place_id"] = response.json()["place_id"]

        # Создаём вид жука через POST /api/species.
        # Сохраняем ID созданного вида.
        response = api_client.post("/api/species", json={"species_name": species_name})
        assert response.status_code == 200, response.text
        created_ids["species_id"] = response.json()["species_id"]

        # Проверяем, что созданная команда присутствует
        # в списке, полученном через GET /api/teams.
        response = api_client.get("/api/teams")
        assert response.status_code == 200
        assert any(item["team_name"] == team_name for item in response.json())

        # Проверяем, что созданное место присутствует
        # в списке, полученном через GET /api/places.
        response = api_client.get("/api/places")
        assert response.status_code == 200
        assert any(item["place_name"] == place_name for item in response.json())

        # Проверяем, что созданный вид жука присутствует
        # в списке, полученном через GET /api/species.
        response = api_client.get("/api/species")
        assert response.status_code == 200
        assert any(item["species_name"] == species_name for item in response.json())

    finally:
        # Удаляем только тестовые записи по уникальным ID.
        # Учитываем внешние ключи: сначала удаляем связанные уловы
        # и экспедиции, а затем справочные записи.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Удаляем уловы, связанные с тестовым видом жука.
                if created_ids.get("species_id"):
                    cur.execute(
                        "DELETE FROM catch WHERE species_id = %s",
                        (created_ids["species_id"],),
                    )

                # Удаляем уловы и экспедиции, связанные с тестовой
                # командой и тестовым местом.
                if created_ids.get("team_id") and created_ids.get("place_id"):
                    cur.execute(
                        """
                        DELETE FROM catch
                        WHERE expedition_id IN (
                            SELECT expedition_id FROM expeditions
                            WHERE team_id = %s AND place_id = %s
                        )
                        """,
                        (created_ids["team_id"], created_ids["place_id"]),
                    )
                    cur.execute(
                        """
                        DELETE FROM expeditions
                        WHERE team_id = %s AND place_id = %s
                        """,
                        (created_ids["team_id"], created_ids["place_id"]),
                    )

                # Удаляем созданную тестовую команду.
                if created_ids.get("team_id"):
                    cur.execute(
                        "DELETE FROM teams WHERE team_id = %s",
                        (created_ids["team_id"],),
                    )

                # Удаляем созданное тестовое место.
                if created_ids.get("place_id"):
                    cur.execute(
                        "DELETE FROM places WHERE place_id = %s",
                        (created_ids["place_id"],),
                    )

                # Удаляем созданный тестовый вид жука.
                if created_ids.get("species_id"):
                    cur.execute(
                        "DELETE FROM beetle_species WHERE species_id = %s",
                        (created_ids["species_id"],),
                    )

                # Удаляем тестового пользователя по уникальному имени.
                cur.execute(
                    "DELETE FROM users WHERE username = %s",
                    (f"pytest_user_{suffix}",),
                )
            conn.commit()
        finally:
            # Закрываем соединение с БД даже в случае ошибки.
            conn.close()

        # Завершаем авторизованную сессию тестового пользователя.
        api_client.post("/api/logout")


# Тест 11. Проверяет полный сценарий работы с экспедицией и уловом.
# Создаёт пользователя, команду, место и вид жука.
# Затем создаёт экспедицию и улов из трёх жуков,
# проверяет списки экспедиций и уловов, а также сводный отчёт.
# В finally удаляет созданные тестовые записи и закрывает сессию.
def test_integration_expedition_catch_and_report():
    """Проверяет создание экспедиции, улова и отчёт."""
    suffix = uuid.uuid4().hex[:12]
    username = f"pytest_user_{suffix}"
    team_name = f"pytest_team_{suffix}"
    place_name = f"pytest_place_{suffix}"
    species_name = f"pytest_species_{suffix}"

    # Переменные нужны для сохранения ID созданных записей.
    # Если тест завершится ошибкой, finally сможет очистить то,
    # что успело создаться до возникновения ошибки.
    team_id = None
    place_id = None
    species_id = None
    expedition_id = None

    try:
        # Регистрируем отдельного тестового пользователя.
        response = api_client.post(
            "/api/register",
            json={"username": username, "password": "test_password"},
        )
        assert response.status_code == 200, response.text

        # Выполняем вход, чтобы запросы к защищённым маршрутам
        # могли выполняться от имени авторизованного пользователя.
        response = api_client.post(
            "/api/login",
            json={"username": username, "password": "test_password"},
        )
        assert response.status_code == 200, response.text

        # Создаём команду для тестовой экспедиции.
        response = api_client.post("/api/teams", json={"team_name": team_name})
        assert response.status_code == 200, response.text
        team_id = response.json()["team_id"]

        # Создаём место проведения экспедиции.
        response = api_client.post("/api/places", json={"place_name": place_name})
        assert response.status_code == 200, response.text
        place_id = response.json()["place_id"]

        # Создаём вид жука, который будет указан в улове.
        response = api_client.post("/api/species", json={"species_name": species_name})
        assert response.status_code == 200, response.text
        species_id = response.json()["species_id"]

        # Формируем время начала и окончания экспедиции.
        # Окончание задаётся на два часа позже начала.
        start_time = datetime.now().replace(microsecond=0)
        end_time = start_time + timedelta(hours=2)

        # Создаём экспедицию через API.
        # Проверяем успешный ответ и сохраняем ID экспедиции.
        response = api_client.post(
            "/api/expeditions",
            json={
                "team_id": team_id,
                "place_id": place_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
        )
        assert response.status_code == 200, response.text
        expedition_id = response.json()["expedition_id"]

        # Проверяем, что созданная экспедиция присутствует
        # в ответе GET /api/expeditions.
        response = api_client.get("/api/expeditions")
        assert response.status_code == 200
        assert any(item["expedition_id"] == expedition_id for item in response.json())

        # Создаём запись об улове: три жука выбранного вида.
        response = api_client.post(
            "/api/catch",
            json={
                "expedition_id": expedition_id,
                "species_id": species_id,
                "quantity": 3,
            },
        )
        assert response.status_code == 200, response.text

        # Проверяем, что улов присутствует в списке.
        # Сверяем экспедицию, вид жука и количество.
        response = api_client.get("/api/catch")
        assert response.status_code == 200
        assert any(
            item["expedition_id"] == expedition_id
            and item["species_id"] == species_id
            and item["quantity"] == 3
            for item in response.json()
        )

        # Проверяем отчёт за период, включающий дату экспедиции.
        # В отчёте для тестового вида должно быть указано
        # суммарное количество, равное трём.
        response = api_client.get(
            "/api/catch/report",
            params={
                "date_from": start_time.date().isoformat(),
                "date_to": (start_time.date() + timedelta(days=1)).isoformat(),
            },
        )
        assert response.status_code == 200, response.text
        assert any(
            item["species_name"] == species_name and item["total_quantity"] == 3
            for item in response.json()
        )

    finally:
        # Очищаем данные, созданные этим интеграционным тестом.
        # Сначала удаляем уловы и экспедицию, чтобы не нарушить
        # ограничения внешних ключей в БД.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Удаляем уловы тестовой экспедиции и саму экспедицию.
                if expedition_id:
                    cur.execute(
                        "DELETE FROM catch WHERE expedition_id = %s",
                        (expedition_id,),
                    )
                    cur.execute(
                        "DELETE FROM expeditions WHERE expedition_id = %s",
                        (expedition_id,),
                    )

                # Удаляем тестовую команду.
                if team_id:
                    cur.execute("DELETE FROM teams WHERE team_id = %s", (team_id,))

                # Удаляем тестовое место.
                if place_id:
                    cur.execute("DELETE FROM places WHERE place_id = %s", (place_id,))

                # Удаляем тестовый вид жука.
                if species_id:
                    cur.execute(
                        "DELETE FROM beetle_species WHERE species_id = %s",
                        (species_id,),
                    )

                # Удаляем тестового пользователя по уникальному имени.
                cur.execute("DELETE FROM users WHERE username = %s", (username,))
            conn.commit()
        finally:
            # Гарантируем закрытие соединения с PostgreSQL.
            conn.close()

        # Завершаем сессию тестового пользователя.
        api_client.post("/api/logout")

        """Блок новых тестов: мутационное тестирование."""


# ============================================================
# БЛОК 4. ПРОВЕРКИ ОШИБОЧНЫХ ДАННЫХ АВТОРИЗАЦИИ
# Проверяем, отклоняет ли приложение некорректные учётные данные.
# ============================================================


# Тест 12. Проверяет минимальную длину имени пользователя.
# Имена короче трёх символов должны отклоняться.
@pytest.mark.parametrize("username", ["", "a", "ab"])
def test_register_rejects_short_username(username):
    response = api_client.post(
        "/api/register",
        json={
            "username": username,
            "password": "test_password",
        },
    )

    assert response.status_code == 400


# Тест 13. Проверяет минимальную длину пароля.
# Пароли короче четырёх символов должны отклоняться.
@pytest.mark.parametrize("password", ["", "a", "abc"])
def test_register_rejects_short_password(password):
    response = api_client.post(
        "/api/register",
        json={
            "username": "valid_test_user",
            "password": password,
        },
    )

    assert response.status_code == 400


# Тест 14. Проверяет, что имя из пробелов не принимается.
# После удаления пробелов имя становится пустым,
# поэтому регистрация должна завершиться ошибкой.
def test_register_rejects_whitespace_username():
    response = api_client.post(
        "/api/register",
        json={
            "username": "   ",
            "password": "test_password",
        },
    )

    assert response.status_code == 400


# Тест 15. Проверяет отказ во входе при неправильном пароле.
# Пользователь с таким именем не должен получить доступ,
# если пароль не совпадает с сохранённым хешем.
def test_login_rejects_wrong_password():
    suffix = uuid.uuid4().hex[:12]
    username = f"pytest_user_{suffix}"

    register_response = api_client.post(
        "/api/register",
        json={
            "username": username,
            "password": "correct_password",
        },
    )
    assert register_response.status_code == 200

    try:
        response = api_client.post(
            "/api/login",
            json={
                "username": username,
                "password": "wrong_password",
            },
        )

        assert response.status_code == 401

    finally:
        # Удаляем созданного тестового пользователя.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM users WHERE username = %s",
                    (username,),
                )
            conn.commit()
        finally:
            conn.close()

        api_client.post("/api/logout")


# Тест 16. Проверяет отказ во входе для несуществующего пользователя.
# Приложение не должно авторизовывать пользователя,
# если учётная запись отсутствует в базе данных.
def test_login_rejects_unknown_user():
    username = f"pytest_missing_{uuid.uuid4().hex[:12]}"

    response = api_client.post(
        "/api/login",
        json={
            "username": username,
            "password": "test_password",
        },
    )

    assert response.status_code == 401


# Тест 17. Проверяет граничный случай:
# время начала и окончания экспедиции совпадают.
# По текущей логике приложения такая экспедиция допустима.
def test_expedition_allows_equal_start_and_end(monkeypatch):
    from unittest.mock import MagicMock
    import main

    fake_connection = MagicMock()
    fake_cursor = fake_connection.cursor.return_value
    fake_cursor.fetchone.return_value = (123,)

    # Подменяем подключение к БД, чтобы тест не создавал реальные записи.
    monkeypatch.setattr(main, "get_connection", lambda: fake_connection)

    expedition = ExpeditionCreate(
        team_id=1,
        place_id=1,
        start_time=datetime(2026, 6, 10, 12, 0),
        end_time=datetime(2026, 6, 10, 12, 0),
    )

    result = create_expedition(expedition, FakeRequest())

    assert result["expedition_id"] == 123
    fake_cursor.execute.assert_called_once()
    fake_connection.commit.assert_called_once()
