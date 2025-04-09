import aiohttp
import json

async def getToken(username, password):
    # keyurl = "http://host.docker.internal:33001/oauth/login3"
    keyurl = "http://localhost:33001/oauth/login3"

    async with aiohttp.ClientSession() as session:
        async with session.get(keyurl) as resp:
            keyJson = await resp.json()
            print(keyJson)
        payload = {"key": keyJson["key"], "username": username, "password": password}
        print(payload)

        async with session.post(keyurl, json=payload) as resp:
            tokenJson = await resp.json()
            print("\n")
            expires_in = tokenJson.get("expires_in")
            print(expires_in)
            print("\n")
    return tokenJson.get("token", None)


def query(q, token, variables):
    async def post():
        gqlurl = "http://localhost:33001/api/gql"
        payload = {"query": q, "variables": variables}
        cookies = {'authorization': token}

        async with aiohttp.ClientSession() as session:
            async with session.post(gqlurl, json=payload, cookies=cookies) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(text)
                    return text
                else:
                    response = await resp.json()
                    return response

    return post  # Return the async function itself


username = "john.newbie@world.com"
password = "john.newbie@world.com"


async def main():
    # Read the query from the read.gql file
    with open("update.gql", "r", encoding="utf-8") as file:
        gql_query = file.read()

    # Get the variables from the variables.json file
    with open("variables_updates.json", "r", encoding="utf-8") as file:
        variables = json.load(file)
    print("Variables:", variables)

    token = await getToken(username, password)
    print("Token:", token)

    qfunc = query(gql_query, token, variables)
    response = await qfunc()  # Await the returned async function
    print("Response:", response)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())