from pydantic import BaseModel
import os

class Settings(BaseModel):
    pg_host : str = os.getenv("PGHOST", "localhost")
    pg_db : str = os.getenv("PGDATABASE", "postgres")
    pg_user : str = os.getenv("PGUSER", "postgres")
    pg_password : str = os.getenv("PGPASSWORD", "postgres")
    pg_port : int = int(os.getenv("PGPORT", "5432"))

settings = Settings()
