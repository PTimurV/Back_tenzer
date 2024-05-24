import psycopg
from config import host, user, password, db_name

class Database:
    @staticmethod
    def get_connection():
        return psycopg.connect(
            host=host,
            user=user,
            password=password,
            dbname=db_name,
            port=5432
        )

    @staticmethod
    def close_connection(conn):
        if conn:
            conn.close()