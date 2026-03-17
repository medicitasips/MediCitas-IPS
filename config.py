"""config.py – Configuración centralizada por entorno."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY      = os.getenv("SECRET_KEY", "cambia_esta_clave_en_produccion")
    DEBUG           = False
    MYSQL_HOST      = os.getenv("MYSQL_HOST",     "localhost")
    MYSQL_PORT      = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER      = os.getenv("MYSQL_USER",     "root")
    MYSQL_PASSWORD  = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB        = os.getenv("MYSQL_DB",       "eps_citas")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}
