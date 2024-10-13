from locust.locust_concurrent import HttpUser, task, between
import time
import json
import os
from src.utils.auth import username, password

class GraphQLUser(HttpUser):
    wait_time = between(1, 5)  # Khoảng thời gian nghỉ giữa các yêu cầu (giây)
    response_file = "response.json"

    def on_start(self):
        """
        Phương thức này được gọi khi người dùng bắt đầu. Nó sẽ đăng nhập và lấy token.
        """
        self.token = None
        self.token_expiry = 0
        self.get_token()

        # Đảm bảo file response.json được khởi tạo rỗng
        if os.path.exists(self.response_file):
            os.remove(self.response_file)

    def get_token(self):
        """
        Hàm này giả lập quá trình lấy token từ Authority và lưu lại thời gian hết hạn.
        """
        url = "http://localhost:33001/oauth/login3"
        response = self.client.get(url)
        keyJson = response.json()

        # Payload để lấy token
        payload = {
            "key": keyJson["key"],
            "username": username,  # Thay bằng thông tin thực
            "password": password  # Thay bằng thông tin thực
        }

        # Gửi yêu cầu để lấy token
        response = self.client.post(url, json=payload)
        tokenJson = response.json()

        # Lưu token và thời gian hết hạn (expiration)
        self.token = tokenJson.get("token", None)
        self.token_expiry = time.time() + tokenJson.get("expires_in", 3600)  # Giả sử token hết hạn sau 1 giờ

    def is_token_expired(self):
        """
        Kiểm tra xem token có hết hạn không.
        """
        return time.time() > self.token_expiry

    def ensure_valid_token(self):
        """
        Đảm bảo token luôn hợp lệ. Nếu token đã hết hạn, làm mới token.
        """
        if self.is_token_expired() or self.token is None:
            self.get_token()

    def write_response_to_file(self, response_data):
        """
        Ghi dữ liệu phản hồi vào tệp JSON.
        """
        with open(self.response_file, "a") as f:
            json.dump(response_data, f, indent=4)
            f.write("\n")

    @task
    def graphql_simple_query(self):
        """
        Hàm này thực hiện một truy vấn GraphQL đơn giản.
        """
        self.ensure_valid_token()  # Kiểm tra và làm mới token nếu cần

        gqlurl = "http://localhost:33001/api/gql"
        query_string = "{userPage{id name surname email}}"  # Truy vấn đơn giản

        payload = {
            "query": query_string
        }

        # Sử dụng cookies cho xác thực
        cookies = {'authorization': self.token}

        # Gửi yêu cầu POST tới GraphQL API
        with self.client.post(gqlurl, json=payload, cookies=cookies, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed! Status Code: {response.status_code}")
                self.write_response_to_file({"error": response.text, "status_code": response.status_code})
            else:
                response_data = response.json()
                response.success()

                # Ghi phản hồi vào file JSON
                self.write_response_to_file(response_data)
