import os
from enum import Enum

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
MAX_CONNECTIONS_COUNT = 20
MIN_CONNECTIONS_COUNT = 10

DATABASE_NAME = os.environ.get("MONGO_DB_NAME")

ALLOWED_HOSTS = ["*"]
API_V1_STR = "/api"
PROJECT_NAME = "SoftWare Technology Assignment API"
