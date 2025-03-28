﻿import asyncio
import aiohttp
from aiohttp import ClientSession, TCPConnector
import time
import statistics
import concurrent.futures
import os
import psutil
import random
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


# Tạo logger riêng cho load_test
logger = logging.getLogger("load_test")
logger.setLevel(logging.INFO)

# Handler cho file log
file_handler = logging.FileHandler("load_test.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(file_handler)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
)
async def make_retryable_request(session, url, query, token):
    """Xử lý request với retry và timeout"""
    payload = {"query": query, "variables": {}}
    cookies = {'authorization': token}
    
    try:
        async with session.post(
            url,
            json=payload,
            cookies=cookies,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            return await resp.json(), resp.status, time.time()
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        raise

def dict_all_results(results, response_times, success_count, failure_count):
    avg_response_time = statistics.mean(response_times)
    min_response_time = min(response_times)
    max_response_time = max(response_times)
    median_response_time = statistics.median(response_times)
    return {
        "results": results,
        "avg_response_time": avg_response_time,
        "min_response_time": min_response_time,
        "max_response_time": max_response_time,
        "median_response_time": median_response_time,
        "num_requests": len(results),
        "success_count": success_count,
        "failure_count": failure_count,
        "response_times": response_times
    }

def print_dict(dict_all):
    print(f"Total Requests: {dict_all['num_requests']}")
    print(f"Successful Requests: {dict_all['success_count']}")
    print(f"Failed Requests: {dict_all['failure_count']}")
    print(f"Success Rate: {dict_all['success_count']/dict_all['num_requests']*100:.2f}%")
    print(f"Average Response Time: {dict_all['avg_response_time']:.3f} seconds")
    print(f"Minimum Response Time: {dict_all['min_response_time']:.3f} seconds")
    print(f"Maximum Response Time: {dict_all['max_response_time']:.3f} seconds")
    print(f"Median Response Time: {dict_all['median_response_time']:.3f} seconds")

async def load_test_concurrent_1(q, token, num_requests, concurrent_limit, url):
    async def single_request(session):
        query = random.choice(list(q.values()))
        start_time = time.time()
        try:
            response, status, end_time = await make_retryable_request(session, url, query, token)
            return response, (end_time - start_time)
        except Exception as e:
            logger.error(f"Final failure: {str(e)}")
            return None, 0

    async def run_requests():
        connector = TCPConnector(limit=concurrent_limit)
        async with ClientSession(connector=connector) as session:
            tasks = [single_request(session) for _ in range(num_requests)]
            return await asyncio.gather(*tasks)

    results = await run_requests()
    
    # Log system metrics
    logger.info(f"CPU Usage: {psutil.cpu_percent()}%")
    logger.info(f"Memory Usage: {psutil.virtual_memory().percent}%")

    success_count = sum(1 for r, _ in results if isinstance(r, dict) and 'data' in r)
    failure_count = num_requests - success_count
    
    response_times = [t for _, t in results]
    dict_all = dict_all_results(results, response_times, success_count, failure_count)
    dict_all.update({
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent
    })
    print_dict(dict_all)
    return dict_all

async def load_test_parallel(url, q, token, num_requests, num_workers):
    async def send_request(session, url, q, token):
        try:
            query = random.choice(list(q.values()))
            start_time = time.time()
            response, status, end_time = await make_retryable_request(session, url, query, token)
            return status, (end_time - start_time)
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return None, 0

    async def run_requests(url, q, token, num_requests):
        async with aiohttp.ClientSession() as session:
            tasks = [send_request(session, url, q, token) for _ in range(num_requests)]
            return await asyncio.gather(*tasks)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(
                executor, 
                lambda: asyncio.run(run_requests(url, q, token, num_requests // num_workers))
            )
            for _ in range(num_workers)
        ]
        results = await asyncio.gather(*futures)

    flatten_results = [item for sublist in results for item in sublist]
    
    # Log system metrics
    logger.info(f"CPU Usage: {psutil.cpu_percent()}%")
    logger.info(f"Memory Usage: {psutil.virtual_memory().percent}%")

    success_count = sum(1 for status, _ in flatten_results if status == 200)
    failure_count = num_requests - success_count
    response_times = [t for _, t in flatten_results]
    dict_all = dict_all_results(flatten_results, response_times, success_count, failure_count)
    dict_all.update({
        "num_requests": num_requests,
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent
    })
    print_dict(dict_all)
    return dict_all