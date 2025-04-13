from locust import HttpUser, task, between
import os
import json

# Configuration
GQL_URL = os.getenv("GQL_PROXY", "http://localhost:33001/api/gql")
LOGIN_URL = os.getenv("GQL_LOGIN", "http://localhost:33001/oauth/login3")
USERNAME = os.getenv("GQL_USERNAME", "john.newbie@world.com")
PASSWORD = os.getenv("GQL_PASSWORD", "john.newbie@world.com")

class SingleQueryUser(HttpUser):
    host = GQL_URL.replace("/api/gql", "")
    wait_time = between(1, 5)
    
    # The single query we'll be testing
    TEST_QUERY = """
    {
      result: userPage(limit: 10) {
        id
      }
    }
    """

    def on_start(self):
        """Authentication flow - unchanged from your original"""
        # Step 1: Get login key
        key_response = self.client.get("/oauth/login3")
        key = key_response.json().get("key")
        print(key_response.json())
        # Step 2: Authenticate
        login_response = self.client.post(
            "/oauth/login2",
            files={
                'username': (None, USERNAME),
                'password': (None, PASSWORD),
                'key': (None, key)
            },
            allow_redirects=True,
            catch_response=True
        )
        
        # Store the token for later use
        self.token = login_response.cookies.get("authorization")
        

    @task
    def execute_single_query(self):
        """Execute our single test query"""
        if not hasattr(self, 'token'):
            print("Not authenticated - skipping query")
            return
            
        response = self.client.post(
            "/api/gql",
            json={
                "query": self.TEST_QUERY,
                "variables": {}
            },
            headers={
                # "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            name="userPage_query"
        )

        print (f"Response: {response.text}")
        
        # Basic response validation
        if response.status_code != 200:
            print(f"Query failed: {response.status_code} - {response.text}")
        elif "errors" in response.json():
            print(f"GraphQL error: {response.json()['errors']}")