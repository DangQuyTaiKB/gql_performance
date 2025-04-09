import asyncio
import aiohttp
from aiohttp import ClientSession, TCPConnector
import time
import statistics
import concurrent.futures
import os
import psutil
import random
import logging
import json


# Tạo logger riêng cho load_test
logger = logging.getLogger("load_test")
logger.setLevel(logging.INFO)

# Handler cho file log
file_handler = logging.FileHandler("load_test.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(file_handler)

async def load_test(q, token, num_requests, concurrent_limit, url):
    async def single_request(session):
# Chọn ngẫu nhiên một query
        query_name = random.choice(list(q.keys()))
        query_data = q[query_name]
        query_text = query_data['query']
        
        # Xử lý variables (chuyển từ string sang dict nếu cần)
        variables = query_data.get('variables', {})
        if isinstance(variables, str):
            try:
                variables = json.loads(variables) if variables.strip() else {}
            except json.JSONDecodeError:
                variables = {}

        payload = {
            "query": query_text,
            "variables": variables
        }
        
        cookies = {'authorization': token}
        start_time = time.time()
  
        async with session.post(
            url,
            json=payload,
            cookies=cookies,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            response_json = await resp.json()
            end_time = time.time()

            # Ghi log kết quả thành công
            logger.info(f"Request status: {resp.status}, Query: {query_text}")
            # # Ghi kết quả vào file
            # with open("response_retryable.json", "w") as f:
            #     json.dump(response_json, f)

            return resp.status, (end_time - start_time)

    async def run_requests():
        connector = TCPConnector(limit=concurrent_limit)
        async with ClientSession(connector=connector) as session:
            tasks = [single_request(session) for _ in range(num_requests)]
            return await asyncio.gather(*tasks)

    results = await run_requests()

    # Tạo file kết quả
    with open("response_concurrent.json", "w") as f:
        json.dump(results, f)

    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    logger.info(f"CPU Usage: {cpu_usage}%")
    logger.info(f"Memory Usage: {memory_usage}%")

    success_count = sum(1 for status, _ in results if status == 200)
    failure_count = num_requests - success_count
    response_times = [t for _, t in results if t > 0]

    # print(response_times)
    avg_response_time = statistics.mean(response_times)
    min_response_time = min(response_times)
    max_response_time = max(response_times)
    median_response_time = statistics.median(response_times)


    dict_all = {
        "results": results,
        "avg_response_time": avg_response_time,
        "min_response_time": min_response_time,
        "max_response_time": max_response_time,
        "median_response_time": median_response_time,
        "num_requests": len(results),
        "success_count": success_count,
        "failure_count": failure_count,
        "response_times": response_times,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage
    }
    

    print(f"Total Requests: {dict_all['num_requests']}")
    print(f"Successful Requests: {dict_all['success_count']}")
    print(f"Failed Requests: {dict_all['failure_count']}")
    print(f"Success Rate: {dict_all['success_count']/dict_all['num_requests']*100:.2f}%")
    print(f"Average Response Time: {dict_all['avg_response_time']:.3f} seconds")
    print(f"Minimum Response Time: {dict_all['min_response_time']:.3f} seconds")
    print(f"Maximum Response Time: {dict_all['max_response_time']:.3f} seconds")
    print(f"Median Response Time: {dict_all['median_response_time']:.3f} seconds")
    return dict_all
