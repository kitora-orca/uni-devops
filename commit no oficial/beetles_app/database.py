import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "beetles_db",
    "user": "postgres",
    "password": "123"
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)