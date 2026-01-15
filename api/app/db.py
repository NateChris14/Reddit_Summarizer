# Instead of always opening/closing a raw connection in every endpoint 
# function manually we will use a pool + dependency injection so connections
# are released reliably

from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from .settings import settings

pool : SimpleConnectionPool | None = None

def open_pool() -> None:
    global pool
    pool = SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=settings.pg_host,
        dbname=settings.pg_db,
        user=settings.pg_user,
        password=settings.pg_password,
        port=settings.pg_port,
        cursor_factory=RealDictCursor,
    )

def close_pool() -> None:
    global pool
    if pool:
        pool.closeall()
        pool = None

def get_conn():
    # FastAPI dependency (yield ensures cleanup)
    assert pool is not None, "DB pool not initialized"
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)
