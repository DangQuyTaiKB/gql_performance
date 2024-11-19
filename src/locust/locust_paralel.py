from locust import HttpUser, task, between
from gevent.pool import Group
import time
import json
import os
import sys
import os

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from query.userPage import queryStr_0
username = os.getenv("GQL_USERNAME", "john.newbie@world.com")
password = os.getenv("GQL_PASSWORD", "john.newbie@world.com")
gqlurl = os.getenv("GQL_PROXY", "http://localhost:33001/api/gql")
login_url = os.getenv("GQL_LOGIN", "http://localhost:33001/oauth/login3")
num_of_parallel_requests = 6

class GraphQLUser(HttpUser):
    wait_time = between(1, 5)  # Wait time between requests (seconds)
    response_file = "response.json"
    def on_start(self):
        self.token = None
        self.token_expiry = 0
        self.get_token()

        # Ensure response.json file is initialized empty
        if os.path.exists(self.response_file):
            os.remove(self.response_file)

    def get_token(self):

        response = self.client.get(login_url)
        keyJson = response.json()

        payload = {"key": keyJson["key"], "username": username, "password": password}
        response = self.client.post(login_url, json=payload)
        tokenJson = response.json()

        # Save token and expiration time
        self.token = tokenJson.get("token", None)
        self.token_expiry = time.time() + tokenJson.get("expires_in", 3600)  # Assume token expires after 1 hour

    def is_token_expired(self):
        return time.time() > self.token_expiry

    def ensure_valid_token(self):
        if self.is_token_expired() or self.token is None:
            self.get_token()

    def write_response_to_file(self, response_data):
        with open(self.response_file, "a", encoding="utf-8") as f:
            json.dump(response_data, f, indent=4, ensure_ascii=False)
            f.write("\n")



    @task
    def graphql_locust(self):
        """
        This function performs a simple GraphQL query in parallel.
        """
        self.ensure_valid_token()  # Check and refresh token if needed

        query_string = queryStr_0

        payload = {"query": query_string, "variables": {}}
        cookies = {'authorization': self.token}

        # Create a gevent group for parallel requests
        group = Group()

        def send_request():
            with self.client.post(gqlurl, json=payload, cookies=cookies, catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"Failed! Status Code: {response.status_code}")
                    self.write_response_to_file({"error": response.text, "status_code": response.status_code})
                else:
                    response_data = response.json()
                    response.success()
                    self.write_response_to_file(response_data)

        # Spawn multiple requests in parallel
        for _ in range(num_of_parallel_requests):
            group.spawn(send_request)

        # Wait for all requests to complete
        group.join()
