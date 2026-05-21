from config.config import Config
from db import get_connection


config = Config(get_connection)