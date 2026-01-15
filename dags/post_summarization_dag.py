from airflow import DAG
from airflow.sdk import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
from airflow.sdk import timezone
import os
import json
import time
import re
import nltk
from airflow.models import Variable
from airflow.utils.log.logging_mixin import LoggingMixin
nltk.download('punkt_tab')

#Summarization libraries
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer

#Configuration
POSTGRES_CONN_ID = 'postgres_default'

default_args = {
    'owner': 'airflow',
    'start_date': timezone.utcnow() - timedelta(days=1)
}

with DAG(
    dag_id = 'reddit_post_summarization',
    default_args = default_args,
    schedule = '@daily',
    catchup = False
) as dag:

    logger = LoggingMixin().log

    @task
    def fetch_posts_for_summary():
        logger.info("Fetching posts which are not already summarized")
        pg_hook = PostgresHook(postgres_conn_id = POSTGRES_CONN_ID)

        # Creating the Summary table
        logger.info("Creating the summary table")
        pg_hook.run("""
        CREATE TABLE IF NOT EXISTS Summary (
        summary_id SERIAL PRIMARY KEY,
        post_id VARCHAR REFERENCES Posts(post_id),
        summary_text TEXT,
        model_used VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Adding unique constraint for ON CONFLICT target
        pg_hook.run(
            """
            ALTER TABLE summary
            ADD CONSTRAINT summary_post_id_unique UNIQUE (post_id);
            """,
            autocommit=True,
        )

        # Fetching the posts for summarization
        logger.info("Fetching the posts to summarize")
        df = pg_hook.get_pandas_df("""
        SELECT p.post_id, p.full_text
        FROM Posts p
        WHERE NOT EXISTS (
        SELECT 1 
        FROM Summary s
        WHERE s.post_id = p.post_id); -- Standard correlation
        """)

        logger.info("Successfully fetched the posts to summarize")
        return df.to_dict("records")

    @task
    def summarize_posts(posts, sentences_count: int = 3):

        logger.info("Initializing Summarization")

        summarizer = TextRankSummarizer()
        summaries = []

        for post in posts:
            post_id = post.get("post_id")
            text = post.get("full_text")

            if not post_id or not text.strip():
                logger.info("Post doesnt have the desired attributes")
                continue

            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            picked = summarizer(parser.document, sentences_count)

            summaries.append({
                "post_id": post_id,
                "summary": " ".join(str(sentence) for sentence in picked),
                "model_used": "sumy_textrank_3sent"
            })

            logger.info("Posts summarized successfully!")

        return summaries

    @task
    def store_summaries(summaries):
        logger.info("Writing the summaries to the database")
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        conn = pg_hook.get_conn()
        cursor = conn.cursor()

        for s in summaries:
            cursor.execute("""
            INSERT INTO Summary (post_id, summary_text, model_used)
            VALUES (%s, %s, %s)
            ON CONFLICT (post_id) DO NOTHING
            """,
            (s['post_id'], s['summary'], s['model_used']))

        conn.commit()
        cursor.close()
        conn.close()

        logger.info("Summaries written successfully!")

    # DAG Workflow - Text Summarization
    posts = fetch_posts_for_summary()
    summaries = summarize_posts(posts)
    store_summaries(summaries)



