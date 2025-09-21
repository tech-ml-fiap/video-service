from pydantic import BaseModel
import os

class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./local.db")
    broker_url: str = os.getenv("BROKER_URL", "amqp://guest:guest@localhost:5672//")
    result_backend: str = os.getenv("RESULT_BACKEND", "rpc://")
    storage_dir: str = os.getenv("STORAGE_DIR", "./data")
    CUSTOMER_SERVICE_URL: str = os.getenv("CUSTOMER_SERVICE_URL", "")

settings = Settings()
