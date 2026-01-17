from pydantic import BaseModel
import os

class Settings(BaseModel):
    pg_host : str = os.getenv("PGHOST", "localhost")
    pg_db : str = os.getenv("PGDATABASE", "postgres")
    pg_user : str = os.getenv("PGUSER", "postgres")
    pg_password : str = os.getenv("PGPASSWORD", "postgres")
    pg_port : int = int(os.getenv("PGPORT", "5432"))

    frontend_url_1 : str = os.getenv("FRONTEND_URL_1", "http://localhost")
    frontend_url_2 : str = os.getenv("FRONTEND_URL_2", "http://127.0.0.1")

settings = Settings()
