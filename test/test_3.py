import aiohttp

async def getToken(username, password):

    # keyurl = "http://host.docker.internal:33001/oauth/login3"
    keyurl = "http://localhost:33001/oauth/login3"

    async with aiohttp.ClientSession() as session:
        async with session.get(keyurl) as resp:
            # print(resp.status)
            keyJson = await resp.json()
            print(keyJson)
        payload = {"key": keyJson["key"], "username": username, "password": password}
        print(payload)

        async with session.post(keyurl, json=payload) as resp:
            # print(resp.status)
            tokenJson = await resp.json()
            # print(tokenJson)
            print("\n")
            expires_in = tokenJson.get("expires_in")
            print(expires_in)
            print("\n")
    return tokenJson.get("token", None)

           
def query(q, token):
    async def post(variables):
        # gqlurl = "http://host.docker.internal:33001/api/gql"
        gqlurl = "http://localhost:33001/api/gql"
        payload = {"query": q, "variables": variables}
        # headers = {"Authorization": f"Bearer {token}"}
        cookies = {'authorization': token}

        async with aiohttp.ClientSession() as session:
            # print(headers, cookies)
            async with session.post(gqlurl, json=payload, cookies=cookies) as resp:
                # print(resp.status)
                if resp.status != 200:
                    text = await resp.text()
                    print(text)
                    return text
                else:
                    response = await resp.json()
                    return response
    return post



# from utils.auth import username, password
username = "john.newbie@world.com"
password = "john.newbie@world.com"

async def main():
    token = await getToken(username, password)
    print(token)
    qfunc = query("{userPage{id name surname email}}", token)
    response = await qfunc({})
    print(response)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())