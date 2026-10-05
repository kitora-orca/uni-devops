import os
import hashlib
import hmac
import secrets

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from starlette.middleware.sessions import SessionMiddleware

from database import get_connection


app = FastAPI(title="Фирма по ловле жуков")


# =========================================================
# НАСТРОЙКИ СЕССИИ
# =========================================================

SESSION_SECRET = os.getenv(
    "SESSION_SECRET",
    "dev-secret-change-this-later"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="beetles_session",
    max_age=60 * 60 * 24
)


app.mount("/static", StaticFiles(directory="static"), name="static")


# =========================================================
# МОДЕЛИ ДАННЫХ
# =========================================================

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TeamCreate(BaseModel):
    team_name: str


class PlaceCreate(BaseModel):
    place_name: str


class SpeciesCreate(BaseModel):
    species_name: str


class ExpeditionCreate(BaseModel):
    team_id: int
    place_id: int
    start_time: datetime
    end_time: datetime


class CatchCreate(BaseModel):
    expedition_id: int
    species_id: int
    quantity: int


# =========================================================
# РАБОТА С ПАРОЛЕМ
# =========================================================

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000
    )

    return (
        salt.hex()
        + "$"
        + password_hash.hex()
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split("$")

        salt = bytes.fromhex(salt_hex)

        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100_000
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash
        )

    except Exception:
        return False


# =========================================================
# ПРОВЕРКА АВТОРИЗАЦИИ
# =========================================================

def require_auth(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Требуется авторизация"
        )

    return user_id


# =========================================================
# ГЛАВНАЯ СТРАНИЦА
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    if not request.session.get("user_id"):
        return RedirectResponse(
            url="/auth",
            status_code=302
        )

    with open(
        "templates/index.html",
        "r",
        encoding="utf-8"
    ) as file:
        return file.read()


# =========================================================
# СТРАНИЦА АВТОРИЗАЦИИ
# =========================================================

@app.get("/auth", response_class=HTMLResponse)
def auth_page(request: Request):

    if request.session.get("user_id"):
        return RedirectResponse(
            url="/",
            status_code=302
        )

    with open(
        "templates/auth.html",
        "r",
        encoding="utf-8"
    ) as file:
        return file.read()


# =========================================================
# РЕГИСТРАЦИЯ
# =========================================================

@app.post("/api/register")
def register(data: RegisterRequest):

    username = data.username.strip()

    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Логин должен содержать минимум 3 символа"
        )

    if len(data.password) < 4:
        raise HTTPException(
            status_code=400,
            detail="Пароль должен содержать минимум 4 символа"
        )

    password_hash = hash_password(data.password)

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO users
                (username, password_hash)
            VALUES
                (%s, %s)
            RETURNING user_id, username
            """,
            (
                username,
                password_hash
            )
        )

        row = cur.fetchone()

        conn.commit()

        return {
            "user_id": row[0],
            "username": row[1],
            "message": "Регистрация успешна"
        }

    except Exception as e:

        conn.rollback()

        if "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Такой логин уже существует"
            )

        raise HTTPException(
            status_code=400,
            detail="Ошибка регистрации"
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# ВХОД
# =========================================================

@app.post("/api/login")
def login(
    data: LoginRequest,
    request: Request
):

    username = data.username.strip()

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            SELECT
                user_id,
                username,
                password_hash
            FROM users
            WHERE username = %s
            """,
            (username,)
        )

        user = cur.fetchone()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Неверный логин или пароль"
            )

        user_id = user[0]
        stored_hash = user[2]

        if not verify_password(
            data.password,
            stored_hash
        ):
            raise HTTPException(
                status_code=401,
                detail="Неверный логин или пароль"
            )

        request.session["user_id"] = user_id
        request.session["username"] = user[1]

        return {
            "message": "Вход выполнен",
            "username": user[1]
        }

    finally:

        cur.close()
        conn.close()


# =========================================================
# ВЫХОД
# =========================================================

@app.post("/api/logout")
def logout(request: Request):

    request.session.clear()

    return {
        "message": "Вы вышли из системы"
    }


# =========================================================
# ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ
# =========================================================

@app.get("/api/me")
def get_current_user(request: Request):

    require_auth(request)

    return {
        "username": request.session.get("username")
    }


# =========================================================
# TEAMS
# =========================================================

@app.get("/api/teams")
def get_teams(request: Request):

    require_auth(request)

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT team_id, team_name
            FROM teams
            ORDER BY team_id
        """)

        rows = cur.fetchall()

        return [
            {
                "team_id": row[0],
                "team_name": row[1]
            }
            for row in rows
        ]

    finally:

        cur.close()
        conn.close()


@app.post("/api/teams")
def create_team(
    team: TeamCreate,
    request: Request
):

    require_auth(request)

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO teams (team_name)
            VALUES (%s)
            RETURNING team_id, team_name
            """,
            (team.team_name,)
        )

        row = cur.fetchone()

        conn.commit()

        return {
            "team_id": row[0],
            "team_name": row[1]
        }

    except Exception as e:

        conn.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# PLACES
# =========================================================

@app.get("/api/places")
def get_places(request: Request):

    require_auth(request)

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT place_id, place_name
            FROM places
            ORDER BY place_id
        """)

        rows = cur.fetchall()

        return [
            {
                "place_id": row[0],
                "place_name": row[1]
            }
            for row in rows
        ]

    finally:

        cur.close()
        conn.close()


@app.post("/api/places")
def create_place(
    place: PlaceCreate,
    request: Request
):

    require_auth(request)

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO places (place_name)
            VALUES (%s)
            RETURNING place_id, place_name
            """,
            (place.place_name,)
        )

        row = cur.fetchone()

        conn.commit()

        return {
            "place_id": row[0],
            "place_name": row[1]
        }

    except Exception as e:

        conn.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# SPECIES
# =========================================================

@app.get("/api/species")
def get_species(request: Request):

    require_auth(request)

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT species_id, species_name
            FROM beetle_species
            ORDER BY species_id
        """)

        rows = cur.fetchall()

        return [
            {
                "species_id": row[0],
                "species_name": row[1]
            }
            for row in rows
        ]

    finally:

        cur.close()
        conn.close()


@app.post("/api/species")
def create_species(
    species: SpeciesCreate,
    request: Request
):

    require_auth(request)

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO beetle_species (species_name)
            VALUES (%s)
            RETURNING species_id, species_name
            """,
            (species.species_name,)
        )

        row = cur.fetchone()

        conn.commit()

        return {
            "species_id": row[0],
            "species_name": row[1]
        }

    except Exception as e:

        conn.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# EXPEDITIONS
# =========================================================

@app.get("/api/expeditions")
def get_expeditions(request: Request):

    require_auth(request)

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                e.expedition_id,
                e.team_id,
                t.team_name,
                e.place_id,
                p.place_name,
                e.start_time,
                e.end_time
            FROM expeditions e
            JOIN teams t
                ON e.team_id = t.team_id
            JOIN places p
                ON e.place_id = p.place_id
            ORDER BY e.expedition_id
        """)

        rows = cur.fetchall()

        return [
            {
                "expedition_id": row[0],
                "team_id": row[1],
                "team_name": row[2],
                "place_id": row[3],
                "place_name": row[4],
                "start_time": row[5],
                "end_time": row[6]
            }
            for row in rows
        ]

    finally:

        cur.close()
        conn.close()


@app.post("/api/expeditions")
def create_expedition(
    expedition: ExpeditionCreate,
    request: Request
):

    require_auth(request)

    if expedition.end_time < expedition.start_time:

        raise HTTPException(
            status_code=400,
            detail="Время окончания не может быть раньше времени начала"
        )

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO expeditions
                (team_id, place_id, start_time, end_time)
            VALUES
                (%s, %s, %s, %s)
            RETURNING expedition_id
            """,
            (
                expedition.team_id,
                expedition.place_id,
                expedition.start_time,
                expedition.end_time
            )
        )

        expedition_id = cur.fetchone()[0]

        conn.commit()

        return {
            "expedition_id": expedition_id,
            "message": "Экспедиция создана"
        }

    except Exception as e:

        conn.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# CATCH
# =========================================================

@app.get("/api/catch")
def get_catches(request: Request):

    require_auth(request)

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                c.catch_id,
                c.expedition_id,
                c.species_id,
                bs.species_name,
                c.quantity
            FROM catch c
            JOIN beetle_species bs
                ON c.species_id = bs.species_id
            ORDER BY c.catch_id
        """)

        rows = cur.fetchall()

        return [
            {
                "catch_id": row[0],
                "expedition_id": row[1],
                "species_id": row[2],
                "species_name": row[3],
                "quantity": row[4]
            }
            for row in rows
        ]

    finally:

        cur.close()
        conn.close()


@app.post("/api/catch")
def create_catch(
    catch: CatchCreate,
    request: Request
):

    require_auth(request)

    if catch.quantity <= 0:

        raise HTTPException(
            status_code=400,
            detail="Количество должно быть больше нуля"
        )

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO catch
                (expedition_id, species_id, quantity)
            VALUES
                (%s, %s, %s)
            RETURNING catch_id
            """,
            (
                catch.expedition_id,
                catch.species_id,
                catch.quantity
            )
        )

        catch_id = cur.fetchone()[0]

        conn.commit()

        return {
            "catch_id": catch_id,
            "message": "Улов добавлен"
        }

    except Exception as e:

        conn.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# ОТЧЁТ ПО УЛОВУ
# =========================================================

@app.get("/api/catch/report")
def catch_report(
    request: Request,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):

    require_auth(request)

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT
            bs.species_name,
            SUM(c.quantity) AS total_quantity
        FROM catch c
        JOIN beetle_species bs
            ON c.species_id = bs.species_id
        JOIN expeditions e
            ON c.expedition_id = e.expedition_id
        WHERE 1 = 1
    """

    params = []

    if date_from:

        query += " AND e.start_time >= %s"
        params.append(date_from)

    if date_to:

        query += " AND e.start_time <= %s"
        params.append(date_to)

    query += """
        GROUP BY bs.species_name
        ORDER BY total_quantity DESC
    """

    try:

        cur.execute(query, params)

        rows = cur.fetchall()

        return [
            {
                "species_name": row[0],
                "total_quantity": row[1]
            }
            for row in rows
        ]

    finally:

        cur.close()
        conn.close()