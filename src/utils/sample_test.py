﻿import aiohttp
import time
import logging

# Configure logger
logger = logging.getLogger("sample_test")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("sample_test.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(file_handler)

async def sample_test(query, token, gqlurl):
    """Process queries and return response details."""
    payload = {"query": query, "variables": {}}
    cookies = {'authorization': token}
    start_time = time.time()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                gqlurl,
                json=payload,
                cookies=cookies,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                response_time = time.time() - start_time
                response_json = await resp.json()
                logger.info(f"Query executed successfully: {query}")
                return {
                    "status": resp.status,
                    "response_time": response_time,
                    "response_body": response_json
                }
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        return {
            "status": None,
            "response_time": None,
            "error": str(e)
        }
