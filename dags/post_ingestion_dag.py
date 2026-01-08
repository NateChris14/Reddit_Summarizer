from airflow import DAG
from airflow.sdk import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
from airflow.sdk import timezone
import json
import requests
import time
import re
from airflow.models import Variable

#Configuration
POSTGRES_CONN_ID = 'postgres_default'

SUBREDDIT_NAME = ['MachineLearning', 'DataScience','Python']
POST_LIMIT = 100

default_args = {
    'owner': 'airflow',
    'start_date': timezone.utcnow() - timedelta(days=1)
}

with DAG(
    dag_id = 'reddit_post_ingestion',
    default_args = default_args,
    schedule = '@daily',
    catchup = False
) as dag:

    @task
    def extract_reddit_posts():
        posts = []
        for subreddit in SUBREDDIT_NAME:
            url = f'https://www.reddit.com/r/{subreddit}/new.json?limit={POST_LIMIT}'
            headers = {'User-Agent': 'reddit-summarizer/0.1'}

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                for child in data['data']['children']:
                    post = child['data']
                    posts.append({
                        "post_id": post['id'],
                        "title": post['title'],
                        "body": post['selftext'],        
                        "subreddit": post['subreddit'],
                        "score": post['score'],
                        "created_utc": post['created_utc'],
                        "num_comments": post['num_comments'],
                        "permalink": post['permalink']
                        })
                time.sleep(1)
            else:
                raise Exception(f'Failed to fetch data from {url} for subreddit {subreddit}')
        
        return posts

    @task
    def transform_reddit_posts(posts):

        cleaned_posts = []

        for post in posts:
            # Removing empty posts and posts with less than 100 characters
            if not post['body'] or len(post['body']) < 100:
                continue
            # Removing urls from the body
            post['body'] = re.sub(r'http\S+', '', post['body'])
            # Removing special characters from the body
            post['body'] = re.sub(r'[^a-zA-Z0-9\s\[\]\(\)\.,!?;:]', '', post['body'])
            # Removing newlines from the body
            post['body'] = post['body'].replace('\n', ' ')
            # Removing multiple spaces from the body and title
            post['body'] = re.sub(r'\s+', ' ', post['body'])
            post['title'] = re.sub(r'\s+', ' ', post['title'])
            # Removing leading and trailing spaces from the body and title
            post['body'] = post['body'].strip()
            post['title'] = post['title'].strip()
            # Adding the title to the body for better context
            post['full_text'] = post['title'] + '\n\n' + post['body']

            cleaned_posts.append({
                "post_id": post['post_id'],
                "title": post['title'],
                "full_text": post['full_text'],
                "body": post['body'],
                "subreddit": post['subreddit'],
                "score": post['score'],
                "created_utc": post['created_utc'],
                "num_comments": post['num_comments'],
                "permalink": post['permalink']
            })

        return cleaned_posts

    @task
    def load_reddit_posts(cleaned_posts):
        pg_hook = PostgresHook(postgres_conn_id = POSTGRES_CONN_ID)
        conn = pg_hook.get_conn()
        cursor = conn.cursor()


        # Creating the Subreddit table
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS Subreddit (
                subreddit_id SERIAL PRIMARY KEY,
                name VARCHAR UNIQUE NOT NULL);
            """)

        # Creating the Posts table with proper FK
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS Posts (
                post_id VARCHAR PRIMARY KEY,
                subreddit_id INT REFERENCES Subreddit(subreddit_id),
                title TEXT NOT NULL,
                full_text TEXT,
                body TEXT,
                score INT,
                num_comments INT,
                permalink TEXT,
                created_utc TIMESTAMP);
            """)

        # Upsert subreddits first
        subreddit_names = list(set(post['subreddit'] for post in cleaned_posts))
        for name in subreddit_names:
            cursor.execute("""
            INSERT INTO Subreddit (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
            RETURNING subreddit_id;
        """, (name,))

        conn.commit()

        # Insert posts with subreddit_id lookup
        for post in cleaned_posts:
            cursor.execute("""
            INSERT INTO Posts (post_id, subreddit_id, title, full_text, body,
            score, num_comments, permalink, created_utc)
            SELECT %s, s.subreddit_id, %s, %s, %s, %s, %s, %s, to_timestamp(%s)
            FROM Subreddit s
            WHERE s.name = %s
            ON CONFLICT (post_id) DO NOTHING;
            """, (
                post['post_id'],
                post['title'],
                post['full_text'],
                post['body'],
                post['score'],
                post['num_comments'],
                post['permalink'],
                post['created_utc'],
                post['subreddit']
            ))

        conn.commit()
        cursor.close()
        conn.close()

    # DAG Workflow - ETL Pipeline
    posts = extract_reddit_posts()
    cleaned = transform_reddit_posts(posts)
    load_reddit_posts(cleaned)






