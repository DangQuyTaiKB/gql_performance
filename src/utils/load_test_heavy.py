import asyncio
import aiohttp
import time
import statistics
import random
import logging
import json
import psutil
from aiohttp import ClientSession, TCPConnector

# Configure logger
logger = logging.getLogger("load_test")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("load_test.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(file_handler)

async def make_request(session, url, query, token):
    """Make a single request with retry logic"""
    payload = {"query": query, "variables": {}}
    cookies = {'authorization': token}
    start_time = time.time()
    
    try:
        async with session.post(
            url,
            json=payload,
            cookies=cookies,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            response_time = time.time() - start_time
            if resp.status == 200:
                await resp.json()  # Ensure response is fully read
                logger.info(f"Request success: {resp.status}")
            else:
                logger.warning(f"Request non-200: {resp.status}")
            return resp.status, response_time
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        return None, 0

async def load_test_heavy(url, q, token, num_requests, concurrent_limit):
    """Run a sustained heavy load test"""
    # Initialize metrics
    start_time = time.time()
    all_results = []  # This will store all [status, response_time] pairs
    
    async def worker(session, queue):
        """Worker to process requests from queue"""
        while True:
            try:
                query = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
                
            status, response_time = await make_request(session, url, query, token)
            all_results.append([status, response_time])  # Store as list per your example
    
    queue = asyncio.Queue()
    for _ in range(num_requests):
        queue.put_nowait(random.choice(list(q.values())))
    
    # Run requests with connection pooling
    connector = TCPConnector(limit=concurrent_limit)
    async with ClientSession(connector=connector) as session:
        workers = [worker(session, queue) for _ in range(concurrent_limit)]
        await asyncio.gather(*workers)
    
    # Calculate metrics
    success_count = sum(1 for status, _ in all_results if status == 200)
    failure_count = num_requests - success_count
    response_times = [t for _, t in all_results if t > 0]
    
     # Tạo file kết quả
    with open("response_heavy.json", "w") as f:
        json.dump(all_results, f)
    # Prepare request queue
    # Prepare results dictionary
    dict_all = {
        "results": all_results,  # Contains all [status, response_time] pairs
        "response_times": response_times,
        "num_requests": num_requests,
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": f"{(success_count/num_requests)*100:.2f}%",
        "response_time_stats": {
            "avg": statistics.mean(response_times) if response_times else 0,
            "min": min(response_times) if response_times else 0,
            "max": max(response_times) if response_times else 0,
            "median": statistics.median(response_times) if response_times else 0,
            "p95": statistics.quantiles(response_times, n=20)[-1] if response_times else 0,
        },
        "system_metrics": {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent
        },
        "duration_seconds": time.time() - start_time,
        "requests_per_second": num_requests / (time.time() - start_time)
    }

    return dict_all