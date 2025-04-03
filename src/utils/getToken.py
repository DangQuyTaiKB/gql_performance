import aiohttp

async def getToken(username, password, login_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(login_url) as resp:
            # print(resp.status)
            keyJson = await resp.json()
            print(keyJson)
        payload = {"key": keyJson["key"], "username": username, "password": password}
        print(payload)

        async with session.post(login_url, json=payload) as resp:
            # print(resp.status)
            tokenJson = await resp.json()
            # print(tokenJson)
    return tokenJson.get("token", None)

