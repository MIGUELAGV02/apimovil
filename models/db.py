import os
from contextlib import contextmanager

from dotenv import load_dotenv
from mysql.connector.pooling import MySQLConnectionPool


load_dotenv()

_connection_pool = None


def _build_pool():
    global _connection_pool

    if _connection_pool is None:
        config = {
            "host": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        }

        ssl_mode = os.getenv("DB_SSLMODE", "").lower()
        ssl_ca = os.getenv("DB_SSL_CA")
        if ssl_mode == "require" and ssl_ca:
            config["ssl_ca"] = ssl_ca

        _connection_pool = MySQLConnectionPool(
            pool_name="evauno_pool",
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            pool_reset_session=True,
            **config,
        )

    return _connection_pool


def get_connection():
    return _build_pool().get_connection()


@contextmanager
def get_cursor(dictionary=True):
    connection = get_connection()
    cursor = connection.cursor(dictionary=dictionary)
    try:
        yield connection, cursor
    finally:
        cursor.close()
        connection.close()