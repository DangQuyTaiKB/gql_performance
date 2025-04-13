from locust import HttpUser, task, between
import json
import os
from locust import events
from jtl_listener import JtlListener
from random import choice
# Cấu hình endpoints
gqlurl = os.getenv("GQL_PROXY", "http://localhost:33001/api/gql")
login_url = os.getenv("GQL_LOGIN", "http://localhost:33001/oauth/login3")
username = os.getenv("GQL_USERNAME", "john.newbie@world.com")
password = os.getenv("GQL_PASSWORD", "john.newbie@world.com")
api_token = os.getenv("JTL_API_TOKEN", "at-53875e0b-7dbf-4ce7-a6a9-b94ea00829f1")

def load_user_queries():
    """Load queries and variables from JSON file"""
    with open('locust_queries.json', 'r') as f:
        data = json.load(f)
        
        # Xử lý cả trường hợp queries là string hoặc dict
        if isinstance(data, str):
            return {"query1": {"query": data, "variables": {}}}
        return data

user_queries = load_user_queries()

def create_query_task(query_name):
    """Tạo task với query và variables tương ứng"""
    query_data = user_queries.get(query_name, {})
    query = query_data.get("query", "")
    variables = query_data.get("variables", {})
    
    if not query:
        raise ValueError(f"Query '{query_name}' not found or invalid")

    def task_func(self):
        response = self.client.post(
            "/api/gql",
            json={
                "query": query,
                "variables": variables
            },
            name=query_name
        )
        # Có thể thêm validation ở đây nếu cần
        # if "expected_result" in query_data:
        #     assert query_data["expected_result"] == response.json()
    
    task_func.__name__ = query_name
    return task_func

class ApiAdminUser(HttpUser):
    host = gqlurl.replace("/api/gql", "")
    wait_time = between(1, 5)

    def on_start(self):
        """Authentication logic (giữ nguyên)"""
        response = self.client.get("/oauth/login3")
        key_response = response.json()
        files = {
            'username': (None, username),
            'password': (None, password),
            "key": (None, key_response.get("key", None))
        }
        self.client.post("/oauth/login2", files=files, allow_redirects=True, catch_response=True)


    @task
    def random_query_task(self):
        """Task chọn query ngẫu nhiên"""
        query_name = choice(list(user_queries.keys()))
        query_task = create_query_task(query_name)
        query_task(self)

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    """JTL Listener (giữ nguyên)"""
    JtlListener(
        env=environment,
        project_name="tai_projects",
        scenario_name="tai_senario",
        environment="tai_environment_test",
        backend_url="http://localhost"
    )