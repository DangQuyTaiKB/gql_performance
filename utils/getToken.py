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
    return tokenJson.get("token", None)

