import pytest
from unittest.mock import patch, MagicMock
from airflow.models import DagBag

from dags.post_ingestion_dag import (
    POSTGRES_CONN_ID,
    SUBREDDIT_NAME,
    POST_LIMIT,
)


# -------------------------
# DAG fixture
# -------------------------
@pytest.fixture
def dagbag():
    """Create a DagBag object for testing."""
    return DagBag(dag_folder="dags", include_examples=False)


# -------------------------
# Helper: get module name
# -------------------------
def _task_module(dag, task_id: str) -> str:
    """Return the actual Python module name where the task callable lives."""
    return dag.get_task(task_id).python_callable.__module__


# -------------------------
# DAG tests
# -------------------------
def test_dag_loaded(dagbag):
    dag = dagbag.dags.get("reddit_post_ingestion")
    assert dag is not None
    assert len(dag.tasks) == 3


def test_dag_structure(dagbag):
    dag = dagbag.dags.get("reddit_post_ingestion")
    assert dag.schedule == "@daily"
    assert not dag.catchup
    assert dag.default_args["owner"] == "airflow"


def test_dag_tasks(dagbag):
    dag = dagbag.dags.get("reddit_post_ingestion")
    task_ids = [t.task_id for t in dag.tasks]

    assert "extract_reddit_posts" in task_ids
    assert "transform_reddit_posts" in task_ids
    assert "load_reddit_posts" in task_ids


def test_dag_task_dependencies(dagbag):
    dag = dagbag.dags.get("reddit_post_ingestion")

    extract_task = dag.get_task("extract_reddit_posts")
    transform_task = dag.get_task("transform_reddit_posts")
    load_task = dag.get_task("load_reddit_posts")

    assert transform_task in extract_task.downstream_list
    assert load_task in transform_task.downstream_list
    assert extract_task in transform_task.upstream_list
    assert transform_task in load_task.upstream_list


# -------------------------
# Extract task tests
# -------------------------
@pytest.fixture
def mock_requests_get(dagbag):
    """Mock requests.get for Reddit API calls (patch at the actual loaded module)."""
    dag = dagbag.dags.get("reddit_post_ingestion")
    module_name = _task_module(dag, "extract_reddit_posts")

    with patch(f"{module_name}.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "children": [
                    {
                        "data": {
                            "id": "test_post_1",
                            "title": "Test Post Title 1",
                            "selftext": (
                                "This is a test post body with more than 100 characters to ensure it passes "
                                "the length filter. It should contain enough content to be valid."
                            ),
                            "subreddit": "MachineLearning",
                            "score": 100,
                            "created_utc": 1640995200.0,
                            "num_comments": 25,
                            "permalink": "/r/MachineLearning/comments/test_post_1/",
                        }
                    },
                    {
                        "data": {
                            "id": "test_post_2",
                            "title": "Test Post Title 2",
                            "selftext": (
                                "Another test post body with more than 100 characters. This one also has a URL "
                                "http://example.com/test and some special characters !@#$%^&*() that should be cleaned."
                            ),
                            "subreddit": "DataScience",
                            "score": 50,
                            "created_utc": 1640995300.0,
                            "num_comments": 10,
                            "permalink": "/r/DataScience/comments/test_post_2/",
                        }
                    },
                ]
            }
        }
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_time_sleep(dagbag):
    """Mock time.sleep to speed up tests (patch at the actual loaded module)."""
    dag = dagbag.dags.get("reddit_post_ingestion")
    module_name = _task_module(dag, "extract_reddit_posts")

    with patch(f"{module_name}.time.sleep") as mock_sleep:
        yield mock_sleep


def test_extract_reddit_posts(mock_requests_get, mock_time_sleep, dagbag):
    dag = dagbag.dags.get("reddit_post_ingestion")
    extract_func = dag.get_task("extract_reddit_posts").python_callable

    result = extract_func()

    assert isinstance(result, list)
    assert len(result) > 0

    # Called once per subreddit
    assert mock_requests_get.call_count == len(SUBREDDIT_NAME)

    post = result[0]
    assert "post_id" in post
    assert "title" in post
    assert "body" in post
    assert "subreddit" in post
    assert "score" in post
    assert "created_utc" in post
    assert "num_comments" in post
    assert "permalink" in post

    assert post["post_id"] == "test_post_1"
    assert post["title"] == "Test Post Title 1"
    assert post["subreddit"] == "MachineLearning"


def test_extract_reddit_posts_failure(mock_time_sleep, dagbag):
    dag = dagbag.dags.get("reddit_post_ingestion")
    extract_func = dag.get_task("extract_reddit_posts").python_callable
    module_name = extract_func.__module__

    with patch(f"{module_name}.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            extract_func()

        assert "Failed to fetch data" in str(exc_info.value)


# -------------------------
# Transform task tests
# -------------------------
def test_transform_reddit_posts(dagbag):
    dag = dagbag.dags.get("reddit_post_ingestion")
    transform_func = dag.get_task("transform_reddit_posts").python_callable

    input_data = [
        {
            "post_id": "test_1",
            "title": "  Test Title 1  ",
            "body": (
                "This is a test body with more than 100 characters to pass the filter. "
                "It has a URL http://example.com/test and some special chars !@#$%^&*() "
                "and multiple    spaces."
            ),
            "subreddit": "MachineLearning",
            "score": 100,
            "created_utc": 1640995200.0,
            "num_comments": 25,
            "permalink": "/r/MachineLearning/comments/test_1/",
        },
        {
            "post_id": "test_2",
            "title": "Test Title 2",
            "body": "Short",  # filtered out (< 100 chars)
            "subreddit": "Python",
            "score": 50,
            "created_utc": 1640995300.0,
            "num_comments": 10,
            "permalink": "/r/Python/comments/test_2/",
        },
        {
            "post_id": "test_3",
            "title": "Test Title 3",
            "body": "",  # filtered out (empty)
            "subreddit": "DataScience",
            "score": 75,
            "created_utc": 1640995400.0,
            "num_comments": 15,
            "permalink": "/r/DataScience/comments/test_3/",
        },
        {
            "post_id": "test_4",
            "title": "Test Title 4",
            "body": (
                "Another valid post with more than 100 characters. This one has\nmultiple\nlines\n"
                "and some URL https://www.example.com/page?param=value that should be removed."
            ),
            "subreddit": "MachineLearning",
            "score": 200,
            "created_utc": 1640995500.0,
            "num_comments": 30,
            "permalink": "/r/MachineLearning/comments/test_4/",
        },
    ]

    result = transform_func(input_data)

    assert isinstance(result, list)
    assert len(result) == 2  # Only test_1 and test_4 remain

    post1 = next(p for p in result if p["post_id"] == "test_1")
    assert post1["title"] == "Test Title 1"
    assert "http://example.com/test" not in post1["body"]
    assert "!@#$%^&*()" not in post1["body"]
    assert post1["full_text"] == post1["title"] + "\n\n" + post1["body"]
    assert post1["subreddit"] == "MachineLearning"
    assert post1["score"] == 100

    post4 = next(p for p in result if p["post_id"] == "test_4")
    assert "\n" not in post4["body"]
    assert "https://www.example.com/page?param=value" not in post4["body"]
    assert post4["full_text"] == post4["title"] + "\n\n" + post4["body"]

    assert not any(p["post_id"] == "test_2" for p in result)
    assert not any(p["post_id"] == "test_3" for p in result)


# -------------------------
# Load task tests
# -------------------------
@pytest.fixture
def mock_postgres(dagbag):
    """
    Mock PostgresHook at the *actual module name* DagBag loaded,
    and also patch Airflow Connection.get as a safety net.
    """
    dag = dagbag.dags.get("reddit_post_ingestion")
    load_func = dag.get_task("load_reddit_posts").python_callable
    module_name = load_func.__module__

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mock_hook_instance = MagicMock()
    mock_hook_instance.get_conn.return_value = mock_conn

    with patch(f"{module_name}.PostgresHook") as mock_hook_class, patch(
        "airflow.sdk.definitions.connection.Connection.get", return_value=MagicMock()
    ):
        mock_hook_class.return_value = mock_hook_instance
        yield mock_hook_class, mock_hook_instance, mock_conn, mock_cursor


def test_load_reddit_posts(mock_postgres, dagbag):
    mock_hook_class, mock_hook, mock_conn, mock_cursor = mock_postgres

    dag = dagbag.dags.get("reddit_post_ingestion")
    load_func = dag.get_task("load_reddit_posts").python_callable

    input_data = [
        {
            "post_id": "test_post_1",
            "title": "Test Title 1",
            "full_text": "Test Title 1\n\nTest body 1",
            "body": "Test body 1",
            "subreddit": "MachineLearning",
            "score": 100,
            "created_utc": 1640995200.0,
            "num_comments": 25,
            "permalink": "/r/MachineLearning/comments/test_post_1/",
        },
        {
            "post_id": "test_post_2",
            "title": "Test Title 2",
            "full_text": "Test Title 2\n\nTest body 2",
            "body": "Test body 2",
            "subreddit": "DataScience",
            "score": 50,
            "created_utc": 1640995300.0,
            "num_comments": 10,
            "permalink": "/r/DataScience/comments/test_post_2/",
        },
    ]

    load_func(input_data)

    # Hook created with correct conn id
    mock_hook_class.assert_called_once_with(postgres_conn_id=POSTGRES_CONN_ID)

    # DB calls made
    mock_hook.get_conn.assert_called_once()
    mock_conn.cursor.assert_called_once()

    # SQL executed at least a few times
    assert mock_cursor.execute.call_count >= 2

    # Commits should happen (depends on your implementation; keep it flexible)
    assert mock_conn.commit.call_count >= 1

    # Close calls might or might not exist in your DAG; don't make them mandatory
    # If your DAG explicitly closes, you can tighten these asserts.



