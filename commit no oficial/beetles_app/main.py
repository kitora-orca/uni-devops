from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_connection


app = FastAPI(title="Фирма по ловле жуков")

app.mount("/static", StaticFiles(directory="static"), name="static")


# =========================
# МОДЕЛИ ДАННЫХ
# =========================

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


# =========================
# ГЛАВНАЯ СТРАНИЦА
# =========================

@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        return file.read()


# =========================
# TEAMS
# =========================

@app.get("/api/teams")
def get_teams():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT team_id, team_name
        FROM teams
        ORDER BY team_id
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "team_id": row[0],
            "team_name": row[1]
        }
        for row in rows
    ]


@app.post("/api/teams")
def create_team(team: TeamCreate):
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
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        conn.close()


# =========================
# PLACES
# =========================

@app.get("/api/places")
def get_places():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT place_id, place_name
        FROM places
        ORDER BY place_id
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "place_id": row[0],
            "place_name": row[1]
        }
        for row in rows
    ]


@app.post("/api/places")
def create_place(place: PlaceCreate):
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
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        conn.close()


# =========================
# SPECIES
# =========================

@app.get("/api/species")
def get_species():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT species_id, species_name
        FROM beetle_species
        ORDER BY species_id
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "species_id": row[0],
            "species_name": row[1]
        }
        for row in rows
    ]


@app.post("/api/species")
def create_species(species: SpeciesCreate):
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
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        conn.close()


# =========================
# EXPEDITIONS
# =========================

@app.get("/api/expeditions")
def get_expeditions():
    conn = get_connection()
    cur = conn.cursor()

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
        JOIN teams t ON e.team_id = t.team_id
        JOIN places p ON e.place_id = p.place_id
        ORDER BY e.expedition_id
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

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


@app.post("/api/expeditions")
def create_expedition(expedition: ExpeditionCreate):
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
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        conn.close()


# =========================
# CATCH
# =========================

@app.get("/api/catch")
def get_catches():
    conn = get_connection()
    cur = conn.cursor()

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

    cur.close()
    conn.close()

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


@app.post("/api/catch")
def create_catch(catch: CatchCreate):

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
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        conn.close()


# =========================
# ОТЧЁТ ПО УЛОВУ
# =========================

@app.get("/api/catch/report")
def catch_report(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
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

    cur.execute(query, params)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "species_name": row[0],
            "total_quantity": row[1]
        }
        for row in rows
    ]