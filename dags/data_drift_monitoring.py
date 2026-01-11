from airflow import DAG
from airflow.sdk import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import timezone
from datetime import timedelta
import pandas as pd
from airflow.utils.log.logging_mixin import LoggingMixin

#Configuration
POSTGRES_CONN_ID = "postgres_default"

default_args = {
    "owner": "airflow",
    "start_date": timezone.utcnow() - timedelta(days=1)
}

with DAG(
    dag_id="reddit_pipeline_monitoring",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
    tags=["monitoring","reddit"]
) as dag:

    logger = LoggingMixin().log
    
    @task
    def extract_and_compute_metrics():
        """Pull recent posts and summaries and compute metrics"""

        pg = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        query = """
        SELECT
            p.post_id,
            LENGTH(p.full_text) AS post_length,
            LENGTH(s.summary_text) AS summary_length
        FROM Posts p
        LEFT JOIN Summary s
        ON p.post_id = s.post_id
        WHERE p.created_utc >= NOW() - INTERVAL '1 day';
        """

        df = pg.get_pandas_df(query)

        metrics = {
        "total_posts": len(df),
        "avg_post_length": df["post_length"].mean(),
        "avg_summary_length": df["summary_length"].mean(),
        "empty_summaries": df["summary_length"].isna().sum(),
        "summary_coverage_pct" : (
            (len(df) - df["summary_length"].isna().sum()) / len(df)
        ) * 100 if len(df) > 0 else 0
        }
        logger.info(f"Monitoring metrics: {metrics}")
        return metrics

    @task
    def detect_drift(metrics: dict):
        """Rule based drift detection"""
        alerts = []

        if metrics['avg_post_length'] < 100:
            alerts.append("Avg post length dropped below threshold")
        
        if metrics['avg_summary_length'] < 30:
            alerts.append("Avg summary length is unusually low")

        if metrics['summary_coverage_pct'] < 80:
            alerts.append("Many posts missing summaries")

        if metrics['total_posts'] < 10:
            alerts.append("Sudden drop in ingested posts")

        if alerts:
            for alert in alerts:
                logger.warning(alert)
        
        else:
            logger.info("No drift detected")

        return alerts

    @task
    def store_metrics(metrics: dict):
        """Persist monitoring metrics"""
        pg = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        conn = pg.get_conn()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metrics (
        run_date DATE,
        total_posts INT,
        avg_post_length FLOAT,
        avg_summary_length FLOAT,
        summary_coverage_pct FLOAT
        );
        """)

        cur.execute("""
        INSERT INTO pipeline_metrics
        VALUES (CURRENT_DATE, %s, %s, %s, %s);
        """, (
            metrics['total_posts'],
            metrics['avg_post_length'],
            metrics['avg_summary_length'],
            metrics['summary_coverage_pct']
        ))

        conn.commit()
        cur.close()
        conn.close()

    # DAG Flow
    metrics = extract_and_compute_metrics()
    alerts = detect_drift(metrics)
    store_metrics(metrics)


        
