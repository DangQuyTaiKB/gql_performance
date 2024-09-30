import aiohttp
import os
import asyncio
from aiohttp import ClientSession, TCPConnector

def query(q, token):
    async def post(variables):
        # gqlurl = "http://host.docker.internal:33001/api/gql"
        gqlurl = "http://localhost:33001/api/gql"
        payload = {"query": q, "variables": variables}
        # headers = {"Authorization": f"Bearer {token}"}
        cookies = {'authorization': token}

        async with aiohttp.ClientSession() as session:
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
