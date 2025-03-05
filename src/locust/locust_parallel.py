from locust import HttpUser, task, between
from gevent.pool import Pool
import json

# Load user-provided queries from JSON file
def load_user_queries():
    with open('locust_queries.json', 'r') as f:
        return json.load(f)

user_queries = load_user_queries()

def create_query_task(query_name, variables=None, expected_result=None):
    query = user_queries.get(query_name, "")
    if not query:
        raise ValueError(f"Query '{query_name}' not found in user-provided queries.")
    variables = variables or {}
    expected_result = expected_result or {}

    def task_func(self):
        response = self.client.post(
            "/api/gql",
            json={
                "query": query,
                "variables": variables
            },
            name=query_name
        )
        if expected_result:
            assert expected_result == response.json(), f"Unexpected result for {query_name}\nExpected: {expected_result}\nGot: {response.json()}"
    
    task_func.__name__ = query_name
    return task_func

class ApiAdminUser(HttpUser):
    """
    Locust user class để thực hiện các bài kiểm tra tải song song.
    """
    host = "http://localhost:33001"  # Địa chỉ host của API
    wait_time = between(1, 5)  # Thời gian chờ giữa các task
    parallel_pool_size = 100  # Số lượng task chạy song song

    def on_start(self):
        response = self.client.get("/oauth/login3")
        key_response = response.json()
        files = {
            'username': (None, "john.newbie@world.com"),
            'password': (None, "john.newbie@world.com"),
            "key": (None, key_response.get("key", None))
        }
        self.client.post("/oauth/login2", files=files)

    @task
    def graphql_parallel_test(self):
        pool = Pool(self.parallel_pool_size)

        def execute_query_task(query_name):
            query_task = create_query_task(query_name)
            query_task(self)

        # Tạo và chạy các task song song
        for query_name in user_queries.keys():
            pool.spawn(execute_query_task, query_name)

        # Đợi tất cả các task hoàn thành
        pool.join()

    # Tạo các task động dựa trên các query từ file JSON
    for query_name in user_queries.keys():
        locals()[f"query_{query_name}"] = task(create_query_task(query_name))