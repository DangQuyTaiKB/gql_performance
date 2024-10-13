import requests

def getToken(username, password):
    # keyurl = "http://host.docker.internal:33001/oauth/login3"
    keyurl = "http://localhost:33001/oauth/login3"

    # Gửi yêu cầu GET để lấy key
    resp = requests.get(keyurl)
    keyJson = resp.json()
    print(keyJson)

    # Chuẩn bị payload với key nhận được
    payload = {"key": keyJson["key"], "username": username, "password": password}
    print(payload)

    # Gửi yêu cầu POST để lấy token
    resp = requests.post(keyurl, json=payload)
    tokenJson = resp.json()

    return tokenJson.get("token", None)



import requests

def query(q, token):
    def post(variables):
        # gqlurl = "http://host.docker.internal:33001/api/gql"
        gqlurl = "http://localhost:33001/api/gql"
        payload = {"query": q, "variables": variables}
        # headers = {"Authorization": f"Bearer {token}"}
        cookies = {'authorization': token}

        # Gửi yêu cầu POST tới gqlurl
        resp = requests.post(gqlurl, json=payload, cookies=cookies)

        # Kiểm tra status code của response
        if resp.status_code != 200:
            text = resp.text
            print(text)
            return text
        else:
            response = resp.json()
            return response

    return post

from utils.auth import username, password
token = getToken(username, password)
print(token)
qfunc = query("{userPage{id name surname email}}", token)
response = qfunc({})
print(response)