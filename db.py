import psycopg
from config import host, user, password, db_name

def get_connection():
    return psycopg.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name,
        port=5432
    )