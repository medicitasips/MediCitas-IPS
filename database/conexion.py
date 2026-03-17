"""database/conexion.py – Factory de conexión MySQL."""
import mysql.connector
from mysql.connector import Error
from flask import current_app

def get_connection():
    try:
        return mysql.connector.connect(
            host               = current_app.config["MYSQL_HOST"],
            port               = current_app.config["MYSQL_PORT"],
            user               = current_app.config["MYSQL_USER"],
            password           = current_app.config["MYSQL_PASSWORD"],
            database           = current_app.config["MYSQL_DB"],
            charset            = "utf8mb4",
            use_unicode        = True,
            connection_timeout = 10,
        )
    except Error as e:
        raise RuntimeError(f"Error al conectar con MySQL: {e}") from e
