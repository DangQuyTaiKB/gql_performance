from locust import HttpUser, task, between
from utils.auth import username, password

class GraphQLUser(HttpUser):
    wait_time = between(1, 5)  # Thời gian nghỉ giữa các yêu cầu (1 đến 5 giây)

    def on_start(self):
        """
        Phương thức này được gọi khi người dùng bắt đầu. Nó sẽ đăng nhập và lấy token.
        """
        self.token = self.get_token()

    def get_token(self):
        """
        Hàm này giả lập quá trình lấy token giống như trong hàm getToken bạn đã chia sẻ.
        """
        url = "http://localhost:33001/oauth/login3"
        response = self.client.get(url)

        keyJson = response.json()
        payload = {
            "key": keyJson["key"],
            "username": username,  # Thay bằng thông tin thực
            "password": password   # Thay bằng thông tin thực
        }
        response = self.client.post(url, json=payload)
        tokenJson = response.json()

        return tokenJson.get("token", None)

    @task
    def graphql_simple_query(self):
        """
        Hàm này thực hiện một truy vấn GraphQL đơn giản.
        """
        gqlurl = "http://localhost:33001/api/gql"
        query_string = "{userPage{id name surname email}}"  # Truy vấn đơn giản

        payload = {
            "query": query_string,
            "variables": {}
            
        }

        # Sử dụng cookies cho xác thực
        cookies = {'authorization': self.token}

        # Gửi yêu cầu POST tới GraphQL API
        with self.client.post(gqlurl, json=payload, cookies=cookies, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed! Status Code: {response.status_code}")
            else:
                response.success()
