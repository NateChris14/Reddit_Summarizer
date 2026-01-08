import os
import uuid
import pytest
from airflow.models import DagBag
from airflow.providers.postgres.hooks.postgres import PostgresHook

from dags.post_ingestion_dag import POSTGRES_CONN_ID


@pytest.fixture()
def airflow_postgres_conn_env(monkeypatch):
    """
    Make sure the Airflow connection exists during the test run.

    IMPORTANT (Windows / Docker Desktop):
    - The tests run inside a container, so 'localhost:5432' would point to the container itself.
    - Use 'host.docker.internal' to reach the host machine from inside the container.
    """
    # If your DAG uses POSTGRES_CONN_ID="postgres_default", this becomes AIRFLOW_CONN_POSTGRES_DEFAULT
    env_key = f"AIRFLOW_CONN_{POSTGRES_CONN_ID.upper()}"

    # Connect to the Postgres that Astro exposes on your host at localhost:5432
    # From inside the test container, use host.docker.internal:5432
    conn_uri = "postgresql://postgres:postgres@host.docker.internal:5432/postgres"

    monkeypatch.setenv(env_key, conn_uri)
    yield


@pytest.fixture()
def isolated_schema(airflow_postgres_conn_env):
    """
    Create a unique schema per test run and clean it up afterwards.
    """
    schema = f"it_{uuid.uuid4().hex[:10]}"

    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = hook.get_conn()
    cur = conn.cursor()

    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
    conn.commit()

    cur.close()
    conn.close()

    yield schema

    # cleanup
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = hook.get_conn()
    cur = conn.cursor()

    cur.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    conn.commit()

    cur.close()
    conn.close()


def _set_search_path(conn, schema: str):
    """
    Ensures subsequent SQL in this session uses the test schema first.
    """
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {schema}, public;")
    cur.close()


@pytest.mark.integration
def test_postgres_connection_smoke(airflow_postgres_conn_env):
    """
    Smoke: can we connect and run a trivial query?
    """
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = hook.get_conn()
    cur = conn.cursor()

    cur.execute("SELECT 1;")
    assert cur.fetchone()[0] == 1

    cur.close()
    conn.close()


@pytest.mark.integration
def test_load_task_writes_rows(isolated_schema):
    """
    Smoke: run the real load task (no mocks) and verify rows are inserted.

    NOTE:
    - This assumes your load task creates tables without schema-qualifying them
      (CREATE TABLE Posts..., CREATE TABLE Subreddit...).
    - So we set search_path for the DB session we use to assert results.
    """
    dagbag = DagBag(dag_folder="dags", include_examples=False)
    dag = dagbag.dags.get("reddit_post_ingestion")
    assert dag is not None

    load_func = dag.get_task("load_reddit_posts").python_callable

    cleaned_posts = [
        {
            "post_id": "it_post_1",
            "title": "[D] Smoke test title 1",
            "full_text": "[D] Smoke test title 1\n\nThis is a body with enough length to be inserted.",
            "body": "This is a body with enough length to be inserted.",
            "subreddit": "MachineLearning",
            "score": 123,
            "created_utc": 1640995200.0,
            "num_comments": 5,
            "permalink": "/r/MachineLearning/comments/it_post_1/",
        },
        {
            "post_id": "it_post_2",
            "title": "[P] Smoke test title 2",
            "full_text": "[P] Smoke test title 2\n\nThis is another body with enough length to be inserted.",
            "body": "This is another body with enough length to be inserted.",
            "subreddit": "DataScience",
            "score": 50,
            "created_utc": 1640995300.0,
            "num_comments": 2,
            "permalink": "/r/DataScience/comments/it_post_2/",
        },
    ]

    # Run your real loader
    load_func(cleaned_posts)

    # Verify data (in our dedicated schema for this session)
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = hook.get_conn()
    _set_search_path(conn, isolated_schema)

    cur = conn.cursor()

    # If your load task creates tables in public, these queries will fail.
    # If so, paste the error and the CREATE TABLE SQL from your DAG, and it can be adjusted.
    cur.execute("SELECT COUNT(*) FROM Posts;")
    assert cur.fetchone()[0] == 2

    cur.execute("SELECT COUNT(*) FROM Subreddit;")
    assert cur.fetchone()[0] == 2

    cur.close()
    conn.close()
