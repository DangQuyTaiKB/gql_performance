from locust import HttpUser, task, between
from gevent.pool import Group
import json
import os
from locust import events
from jtl_listener import JtlListener
from random import choice

# ---------- Environment Configuration ----------
gqlurl = os.getenv("GQL_PROXY", "http://frontend:8000/api/gql")
login_url = os.getenv("GQL_LOGIN", "http://frontend:8000/oauth/login3")
username = os.getenv("GQL_USERNAME", "john.newbie@world.com")
password = os.getenv("GQL_PASSWORD", "john.newbie@world.com")

print(f"GQL Endpoint: {gqlurl}")
print(f"Login Endpoint: {login_url}")
print(f"Username: {username}")
print(f"Password: {password}")

# ---------- Query Loading ----------
def load_user_queries():
    """Load queries and variables from JSON file"""
    with open('locust_queries.json', 'r') as f:
        data = json.load(f)
        
        # Handle both old format (query string) and new format (query + variables)
        if isinstance(data, str):
            return {"query1": {"query": data, "variables": {}}}
        return data

user_queries = load_user_queries()

# ---------- Query Task Factory ----------
def create_query_task(query_name):
    """Create task with query and corresponding variables"""
    query_data = user_queries.get(query_name, {})
    query = query_data.get("query", "")
    variables = query_data.get("variables", {})
    
    if not query:
        raise ValueError(f"Query '{query_name}' not found or invalid")

    def task_func(self):
        with self.client.post(
            "/api/gql",
            json={
                "query": query,
                "variables": variables
            },
            name=query_name,
            catch_response=True
        ) as response:
            # Optional: Add validation for expected results
            if "expected_result" in query_data:
                try:
                    assert response.json() == query_data["expected_result"], \
                        f"Result mismatch in {query_name}"
                except AssertionError as e:
                    response.failure(str(e))
    
    task_func.__name__ = query_name
    return task_func

# ---------- Load Test Class ----------
class ApiAdminUser(HttpUser):
    host = gqlurl.replace("/api/gql", "")
    wait_time = between(1, 5)
    
    # Read number of parallel requests from file
    with open("locust_parallel_requests.txt", "r") as f:
        num_parallel_requests = int(f.read().strip())

    def on_start(self):
        """Authentication flow (unchanged)"""
        with self.client.get("/oauth/login3", json={}) as response:
            key = response.json()
        
        self.client.post(
            "/oauth/login2",
            files={
                'username': (None, username),
                'password': (None, password),
                "key": (None, key.get("key", None))
            },
            allow_redirects=True,
            catch_response=True
        )

    @task
    def parallel_graphql_requests(self):
        """Execute parallel requests with random queries and variables"""
        group = Group()
        
        def execute_random_query():
            # Random query selection with variables
            query_name = choice(list(user_queries.keys()))
            task_func = create_query_task(query_name)
            task_func(self)
        
        # Spawn parallel requests
        for _ in range(self.num_parallel_requests):
            group.spawn(execute_random_query)
        
        group.join()  # Wait for all requests

# ---------- JTL Reporting Integration ----------
@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    JtlListener(
        env=environment,
        project_name="tai_projects",
        scenario_name="tai_senario",
        environment="tai_environment_test",
        backend_url="http://localhost"
    )