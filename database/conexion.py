import os
import mysql.connector
from mysql.connector import Error
from flask import current_app

def get_connection():
    # Railway provee DATABASE_URL, ejemplo:
    # mysql://user:password@host:port/database
    database_url = os.getenv("DATABASE_URL")

    if database_url and database_url.startswith("mysql"):
        # Parsear DATABASE_URL
        import urllib.parse
        url = urllib.parse.urlparse(database_url)
        return mysql.connector.connect(
            host     = url.hostname,
            port     = url.port or 3306,
            user     = url.username,
            password = url.password,
            database = url.path.lstrip("/"),
            charset  = "utf8mb4",
            use_unicode = True,
            connection_timeout = 10,
        )
    else:
        # Variables individuales (desarrollo local)
        try:
            return mysql.connector.connect(
                host     = current_app.config["MYSQL_HOST"],
                port     = current_app.config["MYSQL_PORT"],
                user     = current_app.config["MYSQL_USER"],
                password = current_app.config["MYSQL_PASSWORD"],
                database = current_app.config["MYSQL_DB"],
                charset  = "utf8mb4",
                use_unicode = True,
                connection_timeout = 10,
            )
        except Error as e:
            raise RuntimeError(f"Error al conectar con MySQL: {e}") from e
