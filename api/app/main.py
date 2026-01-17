from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extensions import connection as PgConn
from psycopg2.extras import RealDictCursor
from .db import open_pool, close_pool, get_conn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from .settings import settings

app = FastAPI(
    title="Reddit Insights API",
    description="Trend-aware summarization of ML, Python and Data Science discussions",
    verison="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://13.63.49.1:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Creating limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
def _startup():
    open_pool()

@app.on_event("shutdown")
def _shutdown():
    close_pool()

@app.get("/")
def root():
    return {"service": "reddit-summarizer-api", "status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "reddit-summarizer-api"}

@app.get("/trends")
@limiter.limit("100/hour")
def get_trending_topics(
    request: Request,
    days : int = Query(7, ge=1, le=365),
    limit : int = Query(10, ge=1, le=100),
    conn: PgConn = Depends(get_conn)
    ):

    sql = """
    SELECT 
        LOWER(regexp_replace(word, '[^a-zA-Z]', '', 'g')) AS topic,
        COUNT(*) AS mentions
    FROM (
        SELECT unnest(string_to_array(full_text, ' ')) AS word
        FROM Posts
        WHERE created_utc >= NOW() - make_interval(days => %s)
        ) AS t
    WHERE LENGTH(word) > 4
    GROUP BY topic
    ORDER BY mentions DESC
    LIMIT %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (days, limit))
        results = cur.fetchall()

    return {"window_days": days, "trending_topics": results}

@app.get("/summaries")
@limiter.limit("150/hour")
def get_topic_summaries(
    request: Request,
    topic : str = Query(..., min_length=2, description="Topic keyword"),
    limit : int = Query(5, ge=1, le=50),
    conn : PgConn = Depends(get_conn),     
): 
    sql = """
    SELECT
        p.post_id,
        p.title,
        sub.name,
        p.score,
        p.permalink,
        s.summary_text
    FROM Posts p
    LEFT JOIN Summary s
    ON p.post_id = s.post_id
    INNER JOIN Subreddit sub 
    ON p.subreddit_id = sub.subreddit_id
    WHERE p.full_text ILIKE %s
    ORDER BY p.score DESC
    LIMIT %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (f"%{topic}%", limit))
        posts = cur.fetchall()

    return {"topic": topic, "posts_analyzed": len(posts), "summaries": posts}

@app.get("/beginner/insights")
@limiter.limit("300/hour")
def beginner_insights(
    request: Request,
    days : int = Query(7, ge=1, le=365),
    conn : PgConn = Depends(get_conn)
):
    
    sql = """
    SELECT title, score
    FROM posts
    WHERE created_utc >= NOW() - make_interval(days => %s)
    AND (
    full_text ILIKE %s
    OR full_text ILIKE %s
    OR full_text ILIKE %s
    OR full_text ILIKE %s
    )
    ORDER BY score DESC
    LIMIT 10;
    """

    params = (
    days,
    "%beginner%",
    "%how to%",
    "%roadmap%",
    "%confused%",
    )
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        posts = cur.fetchall()

    recommendations = [
        {
            "insight": f"Beginners are actively discussing: {p['title']}",
            "score": p["score"]
        }
        for p in posts
    ]

    return {
        "window_days": days,
        "recommended_learning_focus": recommendations,
        "posts_used": len(posts) 
    }

@app.get("/monitoring")
@limiter.limit("300/hour")
def pipeline_monitoring(
    request: Request,
    conn :PgConn = Depends(get_conn)
):
    sql = """
    SELECT 
        COUNT(*) AS total_posts,
        COUNT(s.summary_text) AS summarized_posts
    FROM Posts p
    LEFT JOIN Summary s
    ON p.post_id = s.post_id"""

    with conn.cursor() as cur:
        cur.execute(sql)
        data = cur.fetchone()

    total_posts = data['total_posts'] or 0
    summarized_posts = data['summarized_posts'] or 0
    coverage = (summarized_posts / total_posts * 100) if total_posts else 0.0

    return {
        "total_posts" : total_posts,
        "summarized_posts" : summarized_posts,
        "summary_coverage_pct" : round(coverage, 2),
        "pipeline_status" : "healthy" if coverage > 80 else "degraded"

    }

@app.get("/search")
@limiter.limit("200/hour")
def search_posts(
    request: Request,
    query : str = Query(..., min_length = 2),
    subreddit : str | None = None,
    limit : int = Query(20, ge=1, le=200),
    conn : PgConn = Depends(get_conn),
):
    sql = """
    SELECT p.title, p.score, p.permalink,s.name AS subreddit
    FROM Posts p
    JOIN Subreddit s ON p.subreddit_id = s.subreddit_id
    WHERE p.full_text ILIKE %s
    """

    params: list[object] = [f"%{query}%"]

    if subreddit:
        sql += " AND s.name = %s"
        params.append(subreddit)

    sql += " ORDER BY p.score DESC LIMIT %s"
    params.append(limit)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, tuple(params))
        results = cur.fetchall()

    return {"query" : query,
    "subreddit_filter": subreddit,
    "results_count": len(results), 
    "results": results}    





